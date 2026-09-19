# Lernkonsolen — Aufnahmetest Psychologie

Zwei eigenständige Trainer mit demselben Verfahren (FSRS-4.5), aber getrennten
Fragenpools und getrenntem Fortschritt:

| Pfad | Inhalt | Fälligkeiten |
| --- | --- | --- |
| `/lernkonsole` | 185 Fragen, Kapitel 1–8 | nach Uhrzeit |
| `/lernkonsole2` | 175 Fragen, Kapitel 2–8 | nach ganzen Kalendertagen |

## Bauen

Beide Seiten werden aus einem Fragenpool und einer Konfiguration erzeugt; die
gebaute `index.html` ist eine einzelne Datei ohne Build-Schritt beim Ausliefern.

```sh
python3 tools/build_pool.py quellen lernkonsole2/pool.json   # Kapiteldateien → Pool
python3 tools/build_app.py lernkonsole/app.config.json
python3 tools/build_app.py lernkonsole2/app.config.json

node tools/render_check.js lernkonsole/index.html   # rendert jede Ansicht einmal durch
node tools/sync_check.js lernkonsole/index.html     # Client gegen die echte Funktion
node tools/api_check.js                             # übt die Serverless-Funktion durch
python3 tools/dupe_check.py                         # doppelte Fragen in und zwischen den Pools
```

Der Pool des zweiten Durchgangs entsteht aus den Kapiteldateien in `quellen/`;
die Kennung einer Frage ist der sha1 ihres Fragestamms, damit der Lernfortschritt
Neubauten übersteht. Ein Durchgang soll keine Fragen aus einem anderen wiederholen. Deshalb nennt
`lernkonsole2/app.config.json` unter `keineDoppelungenMit` den Pool des ersten
Durchgangs: Findet der Bau dort eine wortgleiche Frage, bricht er ab und nennt
sie beim Namen. `tools/dupe_check.py` prüft dasselbe von Hand und meldet
zusätzlich bloß umformulierte Fragen.

Karten zu Fragen, die aus einem Pool verschwunden sind, räumt die App beim
Laden aus dem Stand — sonst zählten sie in der Auswertung ewig mit.

## Fortschritt speichern

Die App sucht sich ihren Speicher selbst, in dieser Reihenfolge:

1. **Artifact-Speicher** — nur in der Artifact-Fassung vorhanden, arbeitet ohne
   Zutun.
2. **Server dieser Seite** — auf der eigenen Domain. Jede Konsole hat unter
   `/api/fortschritt` genau einen Stand; jedes Gerät, das die Adresse öffnet,
   führt ihn fort. Anzumelden ist nichts, einzugeben auch nichts. Weichen zwei
   Geräte voneinander ab, gewinnt beim Öffnen der zuletzt geänderte Stand
   (`meta.geaendert`).
3. **Browser** — ist der Server nicht erreichbar, bleibt der Stand in
   `localStorage`, und die Auswertung sagt das auch. Geschrieben wird erst
   wieder auf den Server, wenn einmal erfolgreich von ihm gelesen wurde — sonst
   könnte ein lange nicht geöffnetes Gerät einen neueren Stand überschreiben.

Der Stand hängt damit an der Adresse, nicht an einem Konto: Wer die URL kennt,
sieht ihn. Der `serverCode` in der jeweiligen `app.config.json` ist nur ein
fester, zufälliger Schlüssel, damit die Ablage nicht unter einem ratbaren Namen
liegt — ein Passwort ist er nicht.

### Datenbank am Vercel-Projekt

Unterstützt werden Supabase (Postgres über PostgREST) und Redis-Speicher
(Vercel KV, Upstash); die Funktion nimmt, was da ist, und hat keine
Abhängigkeiten.

**Supabase**

1. Im Vercel-Dashboard unter **Storage** die Supabase-Datenbank mit dem Projekt
   verbinden — Vercel legt `SUPABASE_URL` und `SUPABASE_SERVICE_ROLE_KEY` selbst
   als Environment-Variablen ab.
2. Im Supabase-Dashboard unter **SQL Editor** den Inhalt von
   [`tools/supabase.sql`](tools/supabase.sql) einmal ausführen. Das legt die
   Tabelle `fortschritt` an.
3. Einmal neu deployen, damit das Deployment die Variablen kennt.
4. `https://<deine-domain>/api/status` aufrufen: Dort steht, welcher Speicher
   erkannt wurde und ob die Tabelle steht.

**Redis (Vercel KV / Upstash)**

Datenbank unter **Storage** anlegen und verbinden — mehr ist nicht nötig, die
Funktion nimmt `KV_REST_API_URL`, `UPSTASH_REDIS_REST_URL` oder
`REDIS_REST_URL` samt passendem Token.

Fehlt beides, antwortet die Funktion mit `503` und die App sagt in der
Auswertung, dass der Fortschritt vorerst lokal bleibt — kaputt geht dabei nichts.
