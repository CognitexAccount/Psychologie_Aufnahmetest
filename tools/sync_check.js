// Fährt die Client-Seite gegen die echte Serverless-Funktion, damit nicht nur
// beide Hälften für sich funktionieren, sondern auch ihr Drahtformat zusammen-
// passt:  node tools/sync_check.js [lernkonsole/index.html]
const fs = require("fs");
const path = require("path");

const datei = process.argv[2] || "lernkonsole/index.html";
const html = fs.readFileSync(datei, "utf8");
const src = html.match(/<script>([\s\S]*?)<\/script>/g).pop().replace(/^<script>|<\/script>$/g, "");
const poolJson = html.match(/<script type="application\/json" id="pool-data">([\s\S]*?)<\/script>/)[1];

/* ── nachgebautes Supabase hinter der Funktion ──────────────────────────── */
const tabelle = new Map();
let serverAus = false;
const echtesFetch = async (url, opts = {}) => {
  const antwort = (status, body) => ({ ok: status < 400, status, json: async () => body });
  if ((opts.method || "GET") === "GET") {
    const q = new URL(url).searchParams;
    const zeile = tabelle.get(q.get("app").slice(3) + "::" + q.get("code").slice(3));
    return antwort(200, zeile ? [zeile] : []);
  }
  const [zeile] = JSON.parse(opts.body);
  tabelle.set(zeile.app + "::" + zeile.code, zeile);
  return antwort(201, null);
};
global.fetch = echtesFetch;
process.env.SUPABASE_URL = "https://beispiel.supabase.co";
process.env.SUPABASE_SERVICE_ROLE_KEY = "geheim";
const handler = require(path.resolve("api/fortschritt.js"));

/* ── der Client ruft nicht ins Netz, sondern direkt in die Funktion ─────── */
global.fetch = async (pfad, opts = {}) => {
  /* Was die Funktion selbst an Supabase schickt, geht an den Nachbau. */
  if (String(pfad).includes("/rest/v1/")) return echtesFetch(pfad, opts);
  if (serverAus) throw new Error("network");
  const u = new URL(pfad, "https://beispiel.test");
  const req = {
    method: opts.method || "GET",
    query: { app: u.searchParams.get("app"), code: u.searchParams.get("code") },
    body: opts.body ? JSON.parse(opts.body) : undefined,
  };
  let status = 200, body = null;
  await handler(req, {
    setHeader() {},
    status(c) { status = c; return this; },
    json(b) { body = b; return this; },
  });
  return { ok: status < 400, status, json: async () => body };
};

/* ── Umgebung für das App-Skript ────────────────────────────────────────── */
const ablage = new Map();
global.localStorage = {
  getItem: (k) => (ablage.has(k) ? ablage.get(k) : null),
  setItem: (k, v) => ablage.set(k, v),
  removeItem: (k) => ablage.delete(k),
};
global.window = { claude: undefined };
global.document = { getElementById: (id) => (id === "pool-data" ? { textContent: poolJson } : {}) };
global.React = {
  useState: (i) => [typeof i === "function" ? i() : i, () => {}],
  useEffect() {}, useMemo: (f) => f(), useCallback: (f) => f,
  useRef: (i) => ({ current: i }), Fragment: "Fragment",
  createElement: (type, props, ...kinder) => ({ type, props: { ...props, children: kinder } }),
};
global.ReactDOM = { createRoot: () => ({ render() {} }) };

const pruef = (was, ist, soll) => {
  const a = JSON.stringify(ist), b = JSON.stringify(soll);
  if (a !== b) { console.error("FEHLER — " + was + ": " + a + " statt " + b); process.exitCode = 1; }
  else console.log("ok  " + was);
};

const ablauf = `
;(async function(){
  const id = POOL[0].id, id2 = POOL[1].id;

  // 1. Jungfräulicher Server
  const leer = await wolkeLaden();
  pruef("frischer Server ist leer", leer.vorhanden, false);

  // 2. Gerät A lernt und sichert
  const geraetA = { cards: { [id]: { S: 3, D: 5, due: 1, last: 0, reps: 1, lapses: 0 } }, log: [], meta: { sessions: 1, days: [], geaendert: 1000 } };
  lokalSchreiben(alsNutzlast(geraetA));
  const gesichert = await wolkeSpeichern(alsNutzlast(geraetA));
  pruef("Sichern quittiert", typeof gesichert.aktualisiert, "number");

  // 3. Gerät B öffnet die Seite zum ersten Mal: nichts lokal, Stand vom Server
  const beiB = await wolkeLaden();
  pruef("Gerät B findet den Stand", beiB.vorhanden, true);
  pruef("Gerät B bekommt dieselben Karten", Object.keys(beiB.daten.cards), [id]);
  pruef("Gerät B übernimmt den Server", neuerer(null, normalisieren(beiB.daten)).meta.geaendert, 1000);

  // 4. Gerät B lernt weiter und sichert
  const geraetB = { ...normalisieren(beiB.daten), meta: { ...beiB.daten.meta, geaendert: 2000 } };
  geraetB.cards[id2] = { S: 2, D: 6, due: 1, last: 0, reps: 1, lapses: 0 };
  await wolkeSpeichern(alsNutzlast(geraetB));

  // 5. Gerät A kommt zurück: sein alter Stand darf den neueren nicht plätten
  const zurueckA = await wolkeLaden();
  const gewinner = neuerer(lokalLesen(), normalisieren(zurueckA.daten));
  pruef("der neuere Stand gewinnt", gewinner.meta.geaendert, 2000);
  pruef("beide Karten sind da", Object.keys(gewinner.cards).length, 2);

  // 6. Offline: der Client muss den Fehler als solchen sehen
  serverAus = true;
  let gefangen = null;
  try { await wolkeLaden(); } catch (e) { gefangen = e.code || "geworfen"; }
  pruef("Ausfall wird gemeldet", Boolean(gefangen), true);
  serverAus = false;

  // 7. Danach lässt sich wieder abgleichen, und lokal ist nichts verloren
  const nachher = await wolkeLaden();
  pruef("nach dem Ausfall wieder lesbar", nachher.vorhanden, true);
  pruef("lokaler Stand unversehrt", Object.keys(lokalLesen().cards), [id]);

  console.log(process.exitCode ? "\\nDURCHSTICH FEHLGESCHLAGEN" : "\\nDURCHSTICH OK");
})();
`;

eval(src + ablauf);
