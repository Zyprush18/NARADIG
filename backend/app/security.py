"""Auth: hash password bersalt, token HMAC, pencabutan token, rate limit login."""
import base64, hashlib, hmac, json, os, secrets, time
from typing import Optional

from fastapi import Depends, Header, HTTPException

from . import config, db

PBKDF2_ROUNDS = 120_000
TOKEN_TTL = 8 * 3600
RATE_MAX, RATE_WINDOW = 5, 900  # 5 percobaan / 15 menit


def pw_hash(p: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", p.encode(), salt, PBKDF2_ROUNDS)
    return salt.hex() + ":" + h.hex()


def pw_verify(p: str, stored: str) -> bool:
    if not stored:
        return False
    if ":" not in stored:  # hash lama (salt statis) -> verifikasi kompatibel
        legacy = hashlib.pbkdf2_hmac("sha256", p.encode(), b"naradig", 60000).hex()
        return hmac.compare_digest(legacy, stored)
    salt_hex, h_hex = stored.split(":", 1)
    try:
        h = hashlib.pbkdf2_hmac("sha256", p.encode(), bytes.fromhex(salt_hex), PBKDF2_ROUNDS)
    except ValueError:
        return False
    return hmac.compare_digest(h.hex(), h_hex)


def sign(p: str) -> str:
    return hmac.new(config.SECRET.encode(), p.encode(), hashlib.sha256).hexdigest()


def make_token(u) -> str:
    payload = {"uid": u["id"], "name": u["name"], "role": u["role"],
               "exp": time.time() + TOKEN_TTL, "jti": secrets.token_hex(12)}
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return p + "." + sign(p)


def _decode(token: str) -> dict:
    raw = token[7:] if token.lower().startswith("bearer ") else token
    p, s = raw.split(".")
    if not hmac.compare_digest(s, sign(p)):
        raise ValueError
    d = json.loads(base64.urlsafe_b64decode(p + "=="))
    if d.get("exp", 0) < time.time():
        raise ValueError
    if d.get("jti") and db.q("SELECT 1 FROM revoked_tokens WHERE jti=?", (d["jti"],), one=True):
        raise ValueError
    return d


def auth(authorization: Optional[str] = Header(None)):
    try:
        return _decode(authorization or "")
    except Exception:
        raise HTTPException(401, "Sesi tidak valid atau sudah berakhir, silakan login ulang")


def need(perm):
    def dep(u=Depends(auth)):
        if perm not in config.ROLES[u["role"]]:
            raise HTTPException(403, f'Peran {u["role"]} tidak memiliki izin "{perm}"')
        return u
    return dep


def revoke(token_payload: dict):
    db.q("INSERT INTO revoked_tokens(jti,at) VALUES(?,?)", (token_payload.get("jti"), int(time.time())), write=True)
    db.q("DELETE FROM revoked_tokens WHERE at<?", (int(time.time()) - 30 * 86400,), write=True)


def rate_ok(key: str) -> bool:
    now = time.time()
    db.q("DELETE FROM login_attempts WHERE at<?", (now - RATE_WINDOW,), write=True)
    n = db.q("SELECT COUNT(*) AS n FROM login_attempts WHERE akey=?", (key,), one=True)["n"]
    return n < RATE_MAX


def rate_hit(key: str):
    db.q("INSERT INTO login_attempts(akey,at) VALUES(?,?)", (key, time.time()), write=True)


def rate_clear(key: str):
    db.q("DELETE FROM login_attempts WHERE akey=?", (key,), write=True)