"""Setzt aus den Kapiteldateien in quellen/ den Fragenpool eines Durchgangs zusammen.

    python3 tools/build_pool.py quellen lernkonsole2/pool.json

Die Kennung einer Frage leitet sich aus ihrem Fragestamm ab (sha1, zehn Zeichen).
Das hält den Lernfortschritt über Neubauten hinweg stabil, solange der Stamm
gleich bleibt, und macht eine versehentlich doppelt eingetragene Frage sofort
sichtbar: Sie bekäme dieselbe Kennung.
"""
import glob
import hashlib
import json
import os
import sys

FELDER = ("id", "kap", "sec", "stem", "opts", "concept")


def kennung(frage):
    return "k%d-%s" % (frage["kap"], hashlib.sha1(frage["stem"].encode("utf-8")).hexdigest()[:10])


def einlesen(ordner):
    fragen = []
    for pfad in sorted(glob.glob(os.path.join(ordner, "kapitel-*.json"))):
        with open(pfad, encoding="utf-8") as f:
            kapitel = json.load(f)
        for frage in kapitel:
            for pflicht in ("kap", "sec", "stem", "opts"):
                if pflicht not in frage:
                    raise SystemExit("%s: Frage ohne „%s“: %.60s" % (pfad, pflicht, frage.get("stem", "?")))
            if len(frage["opts"]) != 4:
                raise SystemExit("%s: %d statt 4 Optionen: %.60s" % (pfad, len(frage["opts"]), frage["stem"]))
            if not any(o["c"] for o in frage["opts"]):
                raise SystemExit("%s: keine richtige Option: %.60s" % (pfad, frage["stem"]))
        fragen += kapitel
        print("   %-28s %3d Fragen" % (os.path.basename(pfad), len(kapitel)))
    return fragen


def main(ordner, ziel):
    fragen = einlesen(ordner)
    ausgabe = []
    gesehen = {}
    for frage in fragen:
        frage["id"] = kennung(frage)
        if frage["id"] in gesehen:
            raise SystemExit("Zwei Fragen mit gleichem Stamm: %.70s" % frage["stem"])
        gesehen[frage["id"]] = frage
        ausgabe.append({k: frage[k] for k in FELDER if k in frage})
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(ausgabe, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s — %d Fragen" % (ziel, len(ausgabe)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quellen",
         sys.argv[2] if len(sys.argv) > 2 else "lernkonsole2/pool.json")
