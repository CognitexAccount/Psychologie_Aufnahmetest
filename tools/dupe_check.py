"""Sucht doppelte Fragen — innerhalb eines Pools und zwischen mehreren.

    python3 tools/dupe_check.py lernkonsole/pool.json lernkonsole2/pool.json

Gemeldet wird beides: wortgleiche Fragen und solche, die nur umformuliert sind.
Rückgabewert 1, sobald etwas gefunden wurde, damit der Aufruf im Zweifel auffällt.
"""
import json
import re
import sys
import unicodedata
from itertools import combinations


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return " ".join(re.sub(r"[^a-zäöüß0-9 ]", " ", text).split())


def signatur(frage):
    """Stamm plus Optionen — unabhängig davon, wie die Optionen sortiert sind."""
    return (
        norm(frage["stem"]),
        tuple(sorted(norm(o["t"]) for o in frage["opts"])),
    )


def begriffe(frage):
    volltext = norm(frage["stem"] + " " + " ".join(o["t"] for o in frage["opts"]))
    return {w for w in volltext.split() if len(w) > 4}


def aehnlichkeit(x, y):
    a, b = begriffe(x), begriffe(y)
    return len(a & b) / max(1, len(a | b))


SCHWELLE = 0.45   # darüber lohnt das Nachsehen von Hand


def paare(pool_a, pool_b, selbe_liste):
    if selbe_liste:
        return combinations(range(len(pool_a)), 2)
    return ((i, j) for i in range(len(pool_a)) for j in range(len(pool_b)))


def pruefe(name_a, pool_a, name_b, pool_b):
    selbe_liste = pool_a is pool_b
    gleich, aehnlich = [], []
    for i, j in paare(pool_a, pool_b, selbe_liste):
        x, y = pool_a[i], pool_b[j]
        if x["kap"] != y["kap"]:
            continue
        if signatur(x) == signatur(y):
            gleich.append((x, y))
        elif aehnlichkeit(x, y) >= SCHWELLE:
            aehnlich.append((round(aehnlichkeit(x, y), 2), x, y))

    titel = name_a if selbe_liste else name_a + "  ↔  " + name_b
    print("── " + titel)
    print("   wortgleich: %d      umformuliert (Verdacht): %d" % (len(gleich), len(aehnlich)))
    for x, y in gleich:
        print("   = Kap %d  %s / %s  %s" % (x["kap"], x["id"], y["id"], x["stem"][:80]))
    for wert, x, y in sorted(aehnlich, key=lambda p: -p[0]):
        print("   ~ %.2f Kap %d  %s / %s" % (wert, x["kap"], x["id"], y["id"]))
        print("       %s" % x["stem"][:100])
        print("       %s" % y["stem"][:100])
    return len(gleich) + len(aehnlich)


def main(pfade):
    pools = [(p, json.load(open(p, encoding="utf-8"))) for p in pfade]
    treffer = 0
    for name, pool in pools:
        treffer += pruefe(name, pool, name, pool)
    for (na, pa), (nb, pb) in combinations(pools, 2):
        treffer += pruefe(na, pa, nb, pb)
    print("\n%s" % ("Keine Doppelungen." if not treffer else "Gefunden: %d Stellen." % treffer))
    return 1 if treffer else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["lernkonsole/pool.json", "lernkonsole2/pool.json"]))
