"""Uji parser scraper tanpa jaringan (fixture HTML)."""
from app import scrape

INDEX = (
    '<a href="https://www.antaranews.com/berita/123/judul">satu</a>'
    '<a href="/tag/lain">dua</a>'
    '<a href="https://www.antaranews.com/berita/456/lain">tiga</a>'
)

ART = """<html><head>
<meta property="og:title" content="Judul Uji">
<meta property="article:published_time" content="2026-11-14T10:00:00Z">
</head><body>
<nav><p>Menu navigasi situs yang panjang sekali agar ikut terambil bila salah pilih.</p></nav>
<div class="post-content">
<p>Paragraf pertama artikel yang cukup panjang untuk lolos ambang minimum teks.</p>
<p>Paragraf kedua juga panjang dan memuat rincian angka klaim yang perlu dilacak.</p>
</div>
</body></html>"""


def _links(html, pattern):
    p = scrape._Links(pattern)
    p.feed(html)
    return p.urls


def test_links_only_match():
    urls = _links(INDEX, scrape.SITES["antara"]["link"])
    assert urls == [
        "https://www.antaranews.com/berita/123/judul",
        "https://www.antaranews.com/berita/456/lain",
    ]


def test_article_body_prefers_container():
    art = scrape._Article()
    art.feed(ART)
    assert art.title == "Judul Uji"
    assert art.published == "2026-11-14T10:00:00Z"
    assert scrape._ms(art.published) == 1794650400000
    body = scrape._body(art, "post-content")
    assert body.startswith("Paragraf pertama")
    assert "Paragraf kedua" in body
    assert "Menu navigasi" not in body


def test_body_falls_back_to_all_paragraphs():
    art = scrape._Article()
    art.feed(ART)
    body = scrape._body(art, "kelas-tidak-ada")
    assert "Menu navigasi" in body
