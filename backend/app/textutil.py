"""Utilitas teks: tokenisasi, hash, deteksi bahasa."""
import hashlib, re

from . import config


def tok(s):
    return [w for w in re.sub(r"[^a-z0-9\s]", "", str(s).lower()).split()
            if len(w) > 2 and w not in config.STOP]


def hsh(s):
    return hashlib.sha1(" ".join(tok(s)).encode()).hexdigest()[:16]


def lang(s):
    w = re.split(r"\W+", str(s).lower())
    en = sum(x in ("the", "and", "for", "with", "was", "are") for x in w)
    idn = sum(x in ("yang", "dan", "di", "untuk", "dengan", "pada", "dari") for x in w)
    return "en" if en > idn else "id"


def nums(s):
    return [x.rstrip(".") for x in re.findall(r"\d[\d.]*", s)]