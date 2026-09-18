// Rendert jede Ansicht der gebauten App mit Platzhalter-React einmal durch,
// damit Konvertierungsfehler auffallen, bevor die Seite veröffentlicht wird.
//     node tools/render_check.js lernkonsole/index.html
const fs = require("fs");
const html = fs.readFileSync(process.argv[2] || "lernkonsole/index.html", "utf8");
const src = html.match(/<script>([\s\S]*?)<\/script>/g).pop().replace(/^<script>|<\/script>$/g, "");
const poolJson = html.match(/<script type="application\/json" id="pool-data">([\s\S]*?)<\/script>/)[1];

function createElement(type, props, ...children) {
  props = props || {};
  return { type, props: { ...props, children: children.length === 1 ? children[0] : children } };
}
function renderTree(node) {
  if (node === null || node === undefined || typeof node !== "object") return;
  if (Array.isArray(node)) { node.forEach(renderTree); return; }
  const { type, props } = node;
  if (typeof type === "function") { renderTree(type(props)); return; }
  if (props && props.children !== undefined) renderTree(props.children);
}

global.React = {
  useState: (init) => [typeof init === "function" ? init() : init, () => {}],
  useEffect: (fn) => { try { fn(); } catch (e) { console.error("useEffect threw:", e); } },
  useMemo: (fn) => fn(),
  useCallback: (fn) => fn,
  useRef: (init) => ({ current: init }),
  Fragment: "Fragment",
  createElement,
};
global.ReactDOM = { createRoot: () => ({ render: () => {} }) };
global.window = { claude: undefined };
global.localStorage = { getItem: () => null, setItem: () => {} };
global.document = {
  getElementById: (id) => (id === "pool-data" ? { textContent: poolJson } : {}),
};
global.console = console;

const testCode = `
;(function(){
  const byId = {};
  POOL.forEach((q) => (byId[q.id] = q));

  // ---- Home: normal + empty-pool branch ----
  const stateFixture = { cards: {}, log: [], meta: { sessions: 0, days: [] } };
  POOL.slice(0, 4).forEach((q, i) => {
    stateFixture.cards[q.id] = schedule(undefined, (i % 4) + 1, Date.now() - i * DAY);
  });
  const buckets = { due: POOL.slice(0, 2), neu: POOL.slice(4, 9), early: POOL.slice(2, 4) };
  const plan = planSession(buckets);
  renderTree(createElement(Home, { buckets, plan, state: stateFixture, onStart(){}, onDash(){} }));
  renderTree(createElement(Home, { buckets: { due: [], neu: [], early: [] }, plan: { picked: [], vorgezogen: new Set(), counts: {} }, state: stateFixture, onStart(){}, onDash(){} }));
  console.log("Home OK");

  // ---- Session: answer / confidence / review(point) / review(nopoint) ----
  const items = POOL.slice(0, 3).map((q) => ({ q, order: [0,1,2,3], vorgezogen: false }));
  const baseSession = { items, idx: 0, phase: "answer", picks: [], results: [] };
  renderTree(createElement(Session, { session: baseSession, setSession(){}, state: stateFixture, persist: async()=>{}, onDone(){} }));

  const confSession = { ...baseSession, phase: "confidence", picks: [0,1] };
  renderTree(createElement(Session, { session: confSession, setSession(){}, state: stateFixture, persist: async()=>{}, onDone(){} }));

  const q0 = items[0].q;
  const correctPicks = q0.opts.map((o,i)=>o.c?i:null).filter(i=>i!==null);
  const reviewPointSession = {
    items, idx: 0, phase: "review", picks: correctPicks,
    results: [{ id: q0.id, korrekt: true, conf: 1, interval: 3, picks: correctPicks, order: [0,1,2,3] }],
  };
  renderTree(createElement(Session, { session: reviewPointSession, setSession(){}, state: stateFixture, persist: async()=>{}, onDone(){} }));

  const reviewNoPointSession = {
    items, idx: items.length - 1, phase: "review", picks: [],
    results: [{ id: q0.id, korrekt: false, conf: 2, interval: 1, picks: [], order: [0,1,2,3] }],
  };
  renderTree(createElement(Session, { session: reviewNoPointSession, setSession(){}, state: stateFixture, persist: async()=>{}, onDone(){} }));
  console.log("Session OK");

  // ---- Ende: fehler>0, unsicherRichtig>0, all-clean ----
  const endeSession1 = { results: [
    { id: POOL[0].id, korrekt: false, conf: 1 },
    { id: POOL[1].id, korrekt: true, conf: 1 },
    { id: POOL[2].id, korrekt: true, conf: 3 },
  ]};
  renderTree(createElement(Ende, { session: endeSession1, byId, onHome(){}, onDash(){} }));
  const endeSession2 = { results: [ { id: POOL[3].id, korrekt: true, conf: 3 } ] };
  renderTree(createElement(Ende, { session: endeSession2, byId, onHome(){}, onDash(){} }));
  console.log("Ende OK");

  // ---- Dashboard: cloud + local, with and without log data, confirmReset toggled via direct render ----
  const logFixture = POOL.slice(0, 20).map((q, i) => ({ id: q.id, ts: Date.now() - i * 1000, grade: (i%4)+1, korrekt: i % 3 !== 0, conf: (i % 3) + 1, kap: q.kap }));
  const stateFixture2 = { cards: stateFixture.cards, log: logFixture, meta: { sessions: 1, days: [Date.now()] } };
  renderTree(createElement(Dashboard, { state: stateFixture2, persist: async()=>{}, storageMode: "cloud", onHome(){} }));
  renderTree(createElement(Dashboard, { state: stateFixture2, persist: async()=>{}, storageMode: "local", onHome(){} }));
  renderTree(createElement(Dashboard, { state: { cards: {}, log: [], meta: { sessions: 0, days: [] } }, persist: async()=>{}, storageMode: "checking", onHome(){} }));
  console.log("Dashboard OK");

  console.log("ALL COMPONENT RENDERS OK");
})();
`;

try {
  eval(src + testCode);
} catch (e) {
  console.error("ERROR:", e);
  process.exit(1);
}
