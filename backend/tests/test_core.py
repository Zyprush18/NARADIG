"""Self-check inti: keamanan auth, rate limit, pencabutan token, review cleanup, query batch."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import db, security, analysis

PWD = "naradig123"


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        yield client


def login(c, email="admin@naradig.local", pwd=PWD):
    r = c.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def hdr(t):
    return {"Authorization": "Bearer " + t}


def test_password_salt_unique():
    a, b = security.pw_hash("sama"), security.pw_hash("sama")
    assert a != b and ":" in a
    assert security.pw_verify("sama", a) and not security.pw_verify("beda", a)


def test_legacy_hash_still_verifies():
    import hashlib
    legacy = hashlib.pbkdf2_hmac("sha256", b"naradig123", b"naradig", 60000).hex()
    assert security.pw_verify("naradig123", legacy)


def test_login_rate_limit(c):
    email = "viewer@naradig.local"
    for _ in range(5):
        assert c.post("/api/v1/auth/login", json={"email": email, "password": "salah"}).status_code == 401
    r = c.post("/api/v1/auth/login", json={"email": email, "password": PWD})
    assert r.status_code == 429


def test_logout_revokes_token(c):
    t = login(c)
    assert c.get("/api/v1/workspaces", headers=hdr(t)).status_code == 200
    assert c.post("/api/v1/auth/logout", headers=hdr(t)).status_code == 200
    assert c.get("/api/v1/workspaces", headers=hdr(t)).status_code == 401


def test_rate_limit_blocks_bruteforce():
    assert security.rate_ok("ip:test") is True
    for _ in range(5):
        security.rate_hit("ip:test")
    assert security.rate_ok("ip:test") is False


def test_review_cleanup_and_batch_queries(c):
    tok_admin = login(c)
    ws = c.post("/api/v1/workspaces", json={"name": "Tes"}, headers=hdr(tok_admin)).json()["id"]

    csv = ("title,text,date\n"
           "Bantuan banjir 500 paket,Pemerintah menyalurkan 500 paket bantuan untuk korban banjir Konawe,2026-11-01\n"
           "Bantuan banjir 5000 paket,Dikabarkan 5000 paket bantuan banjir Konawe disalurkan seluruh korban,2026-11-02\n")
    imp = c.post("/api/v1/imports", headers=hdr(tok_admin), json={
        "workspace_id": ws, "filename": "t.csv", "content": csv, "license": "uji",
        "mapping": {"text": "text", "title": "title", "pub": "date"}})
    assert imp.status_code == 200 and imp.json()["added"] == 2, imp.text

    assert c.post(f"/api/v1/workspaces/{ws}/analysis-jobs", headers=hdr(tok_admin)).json()["clusters"] == 1
    cid = c.get(f"/api/v1/clusters?workspace_id={ws}", headers=hdr(tok_admin)).json()[0]["id"]

    tok_rev = login(c, "reviewer@naradig.local")
    assert c.post(f"/api/v1/clusters/{cid}/reviews?workspace_id={ws}", headers=hdr(tok_rev),
                  json={"status": "Bukti membantah klaim"}).status_code == 200
    assert c.get(f"/api/v1/clusters/{cid}?workspace_id={ws}", headers=hdr(tok_admin)).json()["review"]["status"] == "Bukti membantah klaim"

    # Re-analisis: review lama harus ikut terhapus (bukan menempel ke klaster baru).
    c.post(f"/api/v1/workspaces/{ws}/analysis-jobs", headers=hdr(tok_admin))
    got = c.get(f"/api/v1/clusters?workspace_id={ws}", headers=hdr(tok_admin)).json()
    assert got and got[0]["review"] == "Belum ditinjau"

    # Batas query per daftar klaster (anti N+1): <= 6 query untuk 1 klaster.
    calls = {"n": 0}
    orig = db.q

    def counting(*a, **kw):
        calls["n"] += 1
        return orig(*a, **kw)

    db.q = counting
    try:
        analysis.list_clusters(ws)
    finally:
        db.q = orig
    assert calls["n"] <= 6, calls


def test_cluster_endpoints_scoped_to_workspace(c):
    """F11: ID klaster workspace A tidak boleh dibaca/direview dari workspace B."""
    tok = login(c)
    ws_a = c.post("/api/v1/workspaces", json={"name": "IDOR A"}, headers=hdr(tok)).json()["id"]
    ws_b = c.post("/api/v1/workspaces", json={"name": "IDOR B"}, headers=hdr(tok)).json()["id"]

    csv = ("title,text\n"
           "Klaim A,Bantuan 500 paket disalurkan ke korban banjir Konawe\n"
           "Klaim A versi 2,Bantuan 5000 paket disalurkan ke korban banjir Konawe\n")
    c.post("/api/v1/imports", headers=hdr(tok), json={
        "workspace_id": ws_a, "filename": "idor.csv", "content": csv, "license": "uji",
        "mapping": {"text": "text", "title": "title"}})
    c.post(f"/api/v1/workspaces/{ws_a}/analysis-jobs", headers=hdr(tok))
    rows = c.get(f"/api/v1/clusters?workspace_id={ws_a}", headers=hdr(tok)).json()
    assert rows, "klaster uji tidak terbentuk"
    cid = rows[0]["id"]

    assert c.get(f"/api/v1/clusters/{cid}?workspace_id={ws_a}", headers=hdr(tok)).status_code == 200
    assert c.get(f"/api/v1/clusters/{cid}?workspace_id={ws_b}", headers=hdr(tok)).status_code == 404
    assert c.get(f"/api/v1/narratives/{cid}/timeline?workspace_id={ws_b}",
                 headers=hdr(tok)).status_code == 404
    assert c.get(f"/api/v1/narratives/{cid}/graph?workspace_id={ws_b}",
                 headers=hdr(tok)).status_code == 404
    assert c.post(f"/api/v1/clusters/{cid}/reviews?workspace_id={ws_b}", headers=hdr(tok),
                  json={"status": "Bukti cukup sebagai konteks"}).status_code == 404

    # workspace_id wajib: tanpa itu endpoint menolak, bukan membaca lintas workspace.
    assert c.get(f"/api/v1/clusters/{cid}", headers=hdr(tok)).status_code == 422


def test_unauthenticated_rejected(c):
    assert c.get("/api/v1/clusters?workspace_id=1").status_code == 401