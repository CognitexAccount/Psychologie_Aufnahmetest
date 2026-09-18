/* Sagt, welcher Speicher am Projekt hängt und ob die Tabelle steht — ohne
   Zugangsdaten preiszugeben. Zum Nachsehen nach dem Einrichten:
   https://<deine-domain>/api/status  */

const { zugang } = require("./fortschritt.js");

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  const z = zugang();
  if (!z) {
    return res.status(200).json({
      speicher: "keiner",
      bereit: false,
      meldung:
        "Am Vercel-Projekt hängt keine Datenbank, oder die Environment-Variablen sind im aktuellen Deployment noch nicht da. Nach dem Verbinden einmal neu deployen.",
    });
  }

  if (z.art === "redis") {
    return res.status(200).json({ speicher: "redis", bereit: true });
  }

  const dienstschluessel = Boolean(
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY
  );
  try {
    const antwort = await fetch(z.url + "/rest/v1/fortschritt?select=app&limit=1", {
      headers: { apikey: z.key, Authorization: "Bearer " + z.key },
    });
    if (antwort.ok) {
      return res.status(200).json({
        speicher: "supabase",
        bereit: true,
        dienstschluessel,
        meldung: dienstschluessel
          ? undefined
          : "Es wird nur der öffentliche anon-Key gefunden. Der reicht, solange Row Level Security aus ist — besser ist SUPABASE_SERVICE_ROLE_KEY.",
      });
    }
    const inhalt = await antwort.json().catch(() => null);
    return res.status(200).json({
      speicher: "supabase",
      bereit: false,
      dienstschluessel,
      meldung:
        antwort.status === 404
          ? "Die Tabelle „fortschritt“ fehlt noch. Das SQL dafür steht in tools/supabase.sql."
          : "Supabase antwortete mit " + antwort.status + ": " + ((inhalt && inhalt.message) || "ohne Begründung"),
    });
  } catch (e) {
    return res.status(200).json({
      speicher: "supabase",
      bereit: false,
      dienstschluessel,
      meldung: "Supabase war nicht erreichbar: " + String((e && e.message) || e),
    });
  }
};
