// Übt api/fortschritt.js gegen einen nachgebauten Redis-Speicher durch, damit
// die Funktion ohne echte Datenbank prüfbar bleibt:  node tools/api_check.js
const path = require("path");
const speicher = new Map();
global.fetch = async (url, opts) => {
  const [befehl, key, wert] = JSON.parse(opts.body);
  let result = null;
  if (befehl === "GET") result = speicher.has(key) ? speicher.get(key) : null;
  if (befehl === "SET") { speicher.set(key, wert); result = "OK"; }
  return { ok: true, json: async () => ({ result }) };
};
process.env.KV_REST_API_URL = "https://beispiel.example/";
process.env.KV_REST_API_TOKEN = "geheim";
const handler = require(path.resolve("api/fortschritt.js"));

function res() {
  const r = { code: 200, body: null, setHeader(){} };
  r.status = (c) => { r.code = c; return r; };
  r.json = (b) => { r.body = b; return r; };
  return r;
}
async function ruf(method, query, body) {
  const r = res();
  await handler({ method, query, body }, r);
  return [r.code, r.body];
}

(async () => {
  const code = "abcde23456fghij78901";
  console.log("leer:      ", ...await ruf("GET", { app: "lernkonsole", code }));
  console.log("schreiben: ", ...await ruf("POST", { app: "lernkonsole", code }, { cards: { a: 1 }, log: [], meta: {} }));
  const [c, b] = await ruf("GET", { app: "lernkonsole", code });
  console.log("lesen:     ", c, JSON.stringify(b.daten), b.vorhanden);
  console.log("andere App:", ...await ruf("GET", { app: "lernkonsole2", code }));
  console.log("kurz:      ", ...await ruf("GET", { app: "lernkonsole", code: "kurz" }));
  console.log("app falsch:", ...await ruf("GET", { app: "bö!", code }));
  console.log("kein Stand:", ...await ruf("POST", { app: "lernkonsole", code }, { irgendwas: true }));
  console.log("String-Body:", ...await ruf("POST", { app: "lernkonsole", code }, JSON.stringify({ cards: {}, log: [], meta: {} })));
  console.log("Methode:   ", ...await ruf("DELETE", { app: "lernkonsole", code }));
  delete process.env.KV_REST_API_URL;
  const [c2, b2] = await ruf("GET", { app: "lernkonsole", code });
  console.log("ohne DB:   ", c2, b2.fehler);
})();
