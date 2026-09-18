/* Speichert den Lernfortschritt je Synchronisationscode in der Datenbank, die
   am Vercel-Projekt hängt. Ohne Abhängigkeiten: die Redis-kompatiblen Speicher
   (Vercel KV, Upstash) sprechen über eine REST-Schnittstelle, die sich mit dem
   eingebauten fetch bedienen lässt.

   GET  /api/fortschritt?app=<id>&code=<code>  → gespeicherter Stand
   POST /api/fortschritt?app=<id>&code=<code>  → Stand ablegen (JSON im Body)

   Der Code ist das Geheimnis: Wer ihn hat, sieht und schreibt diesen Stand.
   Deshalb wird er lang und zufällig erzeugt, nicht vom Menschen ausgedacht. */

const MAX_BYTES = 2 * 1024 * 1024;
const CODE_FORMAT = /^[a-z0-9]{12,64}$/;
const APP_FORMAT = /^[a-z0-9_-]{1,32}$/;

/* Je nachdem, welche Datenbank im Vercel-Dashboard verbunden wurde, heißen die
   Environment-Variablen anders — hier werden die gängigen Namen abgeklopft. */
function zugang() {
  const url =
    process.env.KV_REST_API_URL ||
    process.env.UPSTASH_REDIS_REST_URL ||
    process.env.REDIS_REST_URL ||
    "";
  const token =
    process.env.KV_REST_API_TOKEN ||
    process.env.UPSTASH_REDIS_REST_TOKEN ||
    process.env.REDIS_REST_TOKEN ||
    "";
  if (!url || !token) return null;
  return { url: url.replace(/\/+$/, ""), token };
}

async function redis(befehl) {
  const z = zugang();
  const antwort = await fetch(z.url, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + z.token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(befehl),
  });
  const ergebnis = await antwort.json().catch(() => null);
  if (!antwort.ok) {
    throw new Error("Speicher antwortete mit " + antwort.status);
  }
  if (ergebnis && ergebnis.error) throw new Error(ergebnis.error);
  return ergebnis ? ergebnis.result : null;
}

function istFortschritt(daten) {
  return (
    daten &&
    typeof daten === "object" &&
    daten.cards &&
    typeof daten.cards === "object" &&
    !Array.isArray(daten.cards)
  );
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");

  if (!zugang()) {
    return res.status(503).json({
      ok: false,
      fehler: "keine-datenbank",
      meldung:
        "Am Vercel-Projekt hängt noch keine Datenbank. Unter Storage eine anlegen und mit dem Projekt verbinden.",
    });
  }

  const app = String((req.query && req.query.app) || "");
  const code = String((req.query && req.query.code) || "");
  if (!APP_FORMAT.test(app)) {
    return res.status(400).json({ ok: false, fehler: "app-ungueltig" });
  }
  if (!CODE_FORMAT.test(code)) {
    return res.status(400).json({ ok: false, fehler: "code-ungueltig" });
  }
  const schluessel = "lernkonsole:" + app + ":" + code;

  try {
    if (req.method === "GET") {
      const roh = await redis(["GET", schluessel]);
      if (!roh) {
        return res.status(200).json({ ok: true, vorhanden: false, daten: null });
      }
      const eintrag = typeof roh === "string" ? JSON.parse(roh) : roh;
      return res.status(200).json({
        ok: true,
        vorhanden: true,
        daten: eintrag.daten,
        aktualisiert: eintrag.aktualisiert || null,
      });
    }

    if (req.method === "POST" || req.method === "PUT") {
      let daten = req.body;
      if (typeof daten === "string") {
        try {
          daten = JSON.parse(daten);
        } catch (e) {
          return res.status(400).json({ ok: false, fehler: "kein-json" });
        }
      }
      if (!istFortschritt(daten)) {
        return res.status(400).json({ ok: false, fehler: "kein-fortschritt" });
      }
      const aktualisiert = Date.now();
      const eintrag = JSON.stringify({ daten, aktualisiert });
      if (eintrag.length > MAX_BYTES) {
        return res.status(413).json({ ok: false, fehler: "zu-gross" });
      }
      await redis(["SET", schluessel, eintrag]);
      return res.status(200).json({ ok: true, aktualisiert });
    }

    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ ok: false, fehler: "methode" });
  } catch (e) {
    return res.status(502).json({
      ok: false,
      fehler: "speicher",
      meldung: String((e && e.message) || e),
    });
  }
};
