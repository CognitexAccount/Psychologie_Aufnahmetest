# Lernkonsole

Spaced-Repetition-Trainer (FSRS-4.5) für den österreichischen Aufnahmetest
Psychologie, 185 Fragen aus acht Kapiteln.

- `lernkonsolemaster.jsx` — ursprüngliche React-Quelldatei (unverändert).
- `index.html` — eigenständige, hostbare Fassung derselben App: React/JSX
  wurde von Hand zu `React.createElement`-Aufrufen konvertiert (kein
  Build-Schritt nötig), React und ReactDOM werden per CDN geladen, und die
  Fragen liegen als eingebettetes JSON vor.

## Online-Hosting und Speichern

`index.html` ist so angepasst, dass sie als Claude-Artifact veröffentlicht
werden kann und dort automatisch zwei Laufzeit-Fähigkeiten nutzt:

- **`db`** — der Lernfortschritt (Karten, Verlauf, Kalibrierung) wird bei
  jeder Antwort in einem Cloud-Dokument dieser Seite gespeichert und beim
  erneuten Öffnen im selben Konto automatisch wiederhergestellt. Ist die
  Fähigkeit nicht verfügbar, fällt die App auf `localStorage` im Browser
  zurück, damit trotzdem nichts verloren geht.
- **`downloads`** — der Button „Als Datei sichern" in der Auswertung nutzt
  die Downloads-Fähigkeit der Artifact-Laufzeit, um eine Sicherungsdatei
  anzubieten (ein einfacher Datei-Download würde in der Artifact-Sandbox
  sonst stillschweigend ins Leere laufen).

Wird `index.html` außerhalb der Artifact-Umgebung geöffnet — z. B. über die
Vercel-Deployment dieses Repos —, stehen diese Fähigkeiten nicht zur
Verfügung: Die App läuft normal weiter, speichert den Fortschritt aber nur
lokal in diesem Browser (`localStorage`), und „Als Datei sichern" nutzt dort
einen normalen Datei-Download statt der Downloads-Fähigkeit.

## Vercel-Deployment

`../vercel.json` leitet `/` und `/lernkonsole` auf `lernkonsole/index.html`
um, damit die Root-Domain der Vercel-Preview die App zeigt statt eines
404 — ohne diese Datei findet Vercel dort keine `index.html`, weil die App
in diesem Unterordner liegt.
