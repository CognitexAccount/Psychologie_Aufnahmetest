// Übt api/fortschritt.js gegen nachgebaute Speicher durch, damit die Funktion
// ohne echte Datenbank prüfbar bleibt:  node tools/api_check.js
const path = require("path");

/* ── nachgebaute Speicher hinter fetch ──────────────────────────────────── */
const tabelle = new Map();        // Supabase: "app::code" → Zeile
const redisSpeicher = new Map();  // Redis: Schlüssel → String
let tabelleFehlt = false;

global.fetch = async (url, opts = {}) => {
  const antwort = (status, body) => ({ ok: status < 400, status, json: async () => body });

  if (String(url).includes("/rest/v1/")) {           // Supabase
    if (tabelleFehlt) return antwort(404, { message: 'relation "public.fortschritt" does not exist' });
    if ((opts.method || "GET") === "GET") {
      const q = new URL(url).searchParams;
      const schluessel = q.get("app").slice(3) + "::" + q.get("code").slice(3);
      const zeile = tabelle.get(schluessel);
      return antwort(200, zeile ? [zeile] : []);
    }
    const [zeile] = JSON.parse(opts.body);
    tabelle.set(zeile.app + "::" + zeile.code, zeile);
    return antwort(201, null);
  }

  const [befehl, key, wert] = JSON.parse(opts.body);  // Redis
  let result = null;
  if (befehl === "GET") result = redisSpeicher.has(key) ? redisSpeicher.get(key) : null;
  if (befehl === "SET") { redisSpeicher.set(key, wert); result = "OK"; }
  return antwort(200, { result });
};

const handler = require(path.resolve("api/fortschritt.js"));

function res() {
  const r = { code: 200, body: null, setHeader() {} };
  r.status = (c) => { r.code = c; return r; };
  r.json = (b) => { r.body = b; return r; };
  return r;
}
async function ruf(method, query, body) {
  const r = res();
  await handler({ method, query, body }, r);
  return [r.code, r.body];
}

const code = "abcde23456fghij78901";
const stand = { cards: { a: 1 }, log: [], meta: {} };

async function durchgang(name) {
  console.log("\n— " + name + " —");
  console.log("leer:       ", ...await ruf("GET", { app: "lernkonsole", code }));
  console.log("schreiben:  ", ...await ruf("POST", { app: "lernkonsole", code }, stand));
  const [c, b] = await ruf("GET", { app: "lernkonsole", code });
  console.log("lesen:      ", c, JSON.stringify(b.daten), b.vorhanden, typeof b.aktualisiert);
  console.log("überschreib:", ...await ruf("POST", { app: "lernkonsole", code }, { cards: { a: 1, b: 2 }, log: [], meta: {} }));
  console.log("erneut:     ", JSON.stringify((await ruf("GET", { app: "lernkonsole", code }))[1].daten));
  console.log("andere App: ", ...await ruf("GET", { app: "lernkonsole2", code }));
  console.log("kurz:       ", ...await ruf("GET", { app: "lernkonsole", code: "abc" }));
  console.log("app falsch: ", ...await ruf("GET", { app: "boe!", code }));
  console.log("kein Stand: ", ...await ruf("POST", { app: "lernkonsole", code }, { irgendwas: true }));
  console.log("String-Body:", ...await ruf("POST", { app: "lernkonsole", code }, JSON.stringify(stand)));
  console.log("Methode:    ", ...await ruf("DELETE", { app: "lernkonsole", code }));
}

(async () => {
  process.env.SUPABASE_URL = "https://beispiel.supabase.co";
  process.env.SUPABASE_SERVICE_ROLE_KEY = "geheim";
  await durchgang("Supabase");

  tabelleFehlt = true;
  console.log("ohne Tabelle:", ...await ruf("GET", { app: "lernkonsole", code }));
  tabelleFehlt = false;

  delete process.env.SUPABASE_URL;
  delete process.env.SUPABASE_SERVICE_ROLE_KEY;
  process.env.KV_REST_API_URL = "https://beispiel.example/";
  process.env.KV_REST_API_TOKEN = "geheim";
  await durchgang("Redis");

  delete process.env.KV_REST_API_URL;
  delete process.env.KV_REST_API_TOKEN;
  const [c, b] = await ruf("GET", { app: "lernkonsole", code });
  console.log("\nohne Speicher:", c, b.fehler);
})();
