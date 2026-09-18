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
python3 tools/build_app.py lernkonsole/app.config.json
python3 tools/build_app.py lernkonsole2/app.config.json

node tools/render_check.js lernkonsole/index.html   # rendert jede Ansicht einmal durch
node tools/api_check.js                             # übt die Serverless-Funktion durch
```

## Fortschritt speichern

Die App sucht sich ihren Speicher selbst, in dieser Reihenfolge:

1. **Artifact-Speicher** — nur in der Artifact-Fassung vorhanden, arbeitet ohne
   Zutun.
2. **Synchronisationscode** — auf dieser Domain. In der Auswertung erzeugt
   „Synchronisation einrichten“ einen zwanzigstelligen Code; ab dann geht jede
   Bewertung zusätzlich an `/api/fortschritt`. Derselbe Code auf einem anderen
   Gerät holt den Stand dort wieder hervor. Es gibt keine Anmeldung: Der Code
   **ist** der Schlüssel, deshalb wird er zufällig erzeugt und nicht ausgedacht.
3. **Browser** — ohne beides bleibt der Stand in `localStorage`, und die
   Sicherungsdatei in der Auswertung ist der einzige Weg nach draußen.

### Datenbank am Vercel-Projekt

`api/fortschritt.js` braucht einen Redis-kompatiblen Speicher. Im Vercel-Dashboard
unter **Storage** eine Datenbank anlegen (Upstash Redis bzw. Vercel KV) und mit
dem Projekt verbinden — Vercel legt die Zugangsdaten dann selbst als
Environment-Variablen ab. Die Funktion nimmt `KV_REST_API_URL`,
`UPSTASH_REDIS_REST_URL` oder `REDIS_REST_URL` samt passendem Token. Fehlt die
Datenbank, antwortet sie mit `503 keine-datenbank`, und die App sagt in der
Auswertung, dass der Fortschritt vorerst lokal bleibt — kaputt geht dabei nichts.

Abhängigkeiten hat die Funktion keine: Sie spricht die REST-Schnittstelle des
Speichers mit dem eingebauten `fetch` an.
