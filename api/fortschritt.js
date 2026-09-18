/* Speichert den Lernfortschritt in der Datenbank, die am Vercel-Projekt hängt.
   Ohne Abhängigkeiten: Supabase bringt mit PostgREST eine HTTP-Schnittstelle
   mit, die sich mit dem eingebauten fetch bedienen lässt; Redis-Speicher
   (Vercel KV, Upstash) werden weiterhin unterstützt.

   GET  /api/fortschritt?app=<id>&code=<code>  → gespeicherter Stand
   POST /api/fortschritt?app=<id>&code=<code>  → Stand ablegen (JSON im Body)  */

const MAX_BYTES = 2 * 1024 * 1024;
const CODE_FORMAT = /^[a-z0-9]{6,64}$/;
const APP_FORMAT = /^[a-z0-9_-]{1,32}$/;
const TABELLE = "fortschritt";

/* Je nachdem, welche Datenbank im Vercel-Dashboard verbunden wurde, heißen die
   Environment-Variablen anders — hier werden die gängigen Namen abgeklopft. */
function zugang() {
  const supabaseUrl =
    process.env.SUPABASE_URL ||
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    "";
  const supabaseKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    "";
  if (supabaseUrl && supabaseKey) {
    return { art: "supabase", url: supabaseUrl.replace(/\/+$/, ""), key: supabaseKey };
  }

  const redisUrl =
    process.env.KV_REST_API_URL ||
    process.env.UPSTASH_REDIS_REST_URL ||
    process.env.REDIS_REST_URL ||
    "";
  const redisToken =
    process.env.KV_REST_API_TOKEN ||
    process.env.UPSTASH_REDIS_REST_TOKEN ||
    process.env.REDIS_REST_TOKEN ||
    "";
  if (redisUrl && redisToken) {
    return { art: "redis", url: redisUrl.replace(/\/+$/, ""), token: redisToken };
  }
  return null;
}

/* ── Supabase (PostgREST) ────────────────────────────────────────────────── */
async function supabase(z, pfad, optionen) {
  const antwort = await fetch(z.url + "/rest/v1/" + pfad, {
    ...optionen,
    headers: {
      apikey: z.key,
      Authorization: "Bearer " + z.key,
      "Content-Type": "application/json",
      ...(optionen && optionen.headers),
    },
  });
  const inhalt = await antwort.json().catch(() => null);
  if (!antwort.ok) {
    const fehler = new Error((inhalt && (inhalt.message || inhalt.hint)) || "HTTP " + antwort.status);
    /* Die Tabelle fehlt noch — das ist kein Ausfall, sondern ein fehlender
       Einrichtungsschritt, und wird der App auch so gemeldet. */
    if (antwort.status === 404 || (inhalt && /relation .* does not exist/i.test(inhalt.message || ""))) {
      fehler.fehlt = true;
    }
    throw fehler;
  }
  return inhalt;
}

const filter = (app, code) =>
  "?app=eq." + encodeURIComponent(app) + "&code=eq." + encodeURIComponent(code);

async function supabaseLesen(z, app, code) {
  const zeilen = await supabase(z, TABELLE + filter(app, code) + "&select=daten,aktualisiert&limit=1", {
    method: "GET",
  });
  if (!Array.isArray(zeilen) || zeilen.length === 0) return null;
  return {
    daten: zeilen[0].daten,
    aktualisiert: Date.parse(zeilen[0].aktualisiert) || null,
  };
}

async function supabaseSchreiben(z, app, code, daten, aktualisiert) {
  await supabase(z, TABELLE, {
    method: "POST",
    headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
    body: JSON.stringify([
      { app, code, daten, aktualisiert: new Date(aktualisiert).toISOString() },
    ]),
  });
}

/* ── Redis (Vercel KV, Upstash) ──────────────────────────────────────────── */
async function redis(z, befehl) {
  const antwort = await fetch(z.url, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + z.token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(befehl),
  });
  const ergebnis = await antwort.json().catch(() => null);
  if (!antwort.ok) throw new Error("Speicher antwortete mit " + antwort.status);
  if (ergebnis && ergebnis.error) throw new Error(ergebnis.error);
  return ergebnis ? ergebnis.result : null;
}

const redisSchluessel = (app, code) => "lernkonsole:" + app + ":" + code;

async function redisLesen(z, app, code) {
  const roh = await redis(z, ["GET", redisSchluessel(app, code)]);
  if (!roh) return null;
  const eintrag = typeof roh === "string" ? JSON.parse(roh) : roh;
  return { daten: eintrag.daten, aktualisiert: eintrag.aktualisiert || null };
}

async function redisSchreiben(z, app, code, daten, aktualisiert) {
  await redis(z, ["SET", redisSchluessel(app, code), JSON.stringify({ daten, aktualisiert })]);
}

/* ── Handler ─────────────────────────────────────────────────────────────── */
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

  const z = zugang();
  if (!z) {
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

  try {
    if (req.method === "GET") {
      const eintrag = z.art === "supabase"
        ? await supabaseLesen(z, app, code)
        : await redisLesen(z, app, code);
      if (!eintrag) {
        return res.status(200).json({ ok: true, vorhanden: false, daten: null });
      }
      return res.status(200).json({
        ok: true,
        vorhanden: true,
        daten: eintrag.daten,
        aktualisiert: eintrag.aktualisiert,
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
      if (JSON.stringify(daten).length > MAX_BYTES) {
        return res.status(413).json({ ok: false, fehler: "zu-gross" });
      }
      const aktualisiert = Date.now();
      if (z.art === "supabase") await supabaseSchreiben(z, app, code, daten, aktualisiert);
      else await redisSchreiben(z, app, code, daten, aktualisiert);
      return res.status(200).json({ ok: true, aktualisiert });
    }

    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ ok: false, fehler: "methode" });
  } catch (e) {
    if (e && e.fehlt) {
      return res.status(503).json({
        ok: false,
        fehler: "keine-tabelle",
        meldung:
          "Die Datenbank ist verbunden, die Tabelle „" + TABELLE + "“ fehlt aber noch. Das SQL dafür steht in tools/supabase.sql.",
      });
    }
    return res.status(502).json({
      ok: false,
      fehler: "speicher",
      meldung: String((e && e.message) || e),
    });
  }
};

module.exports.zugang = zugang;
