"""Baut aus einem Fragenpool eine eigenständige, hostbare HTML-App.

    python3 tools/build_app.py lernkonsole/app.config.json

Die Konfiguration bestimmt Fragenpool, Zielpfad, Titel, Speicherschlüssel und
die Kapitelnamen; der Rest der App ist für alle Durchgänge identisch.
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "lernkonsole/app.config.json")
with open(config_path, encoding="utf-8") as f:
    CONFIG = json.load(f)

with open(os.path.join(REPO, CONFIG["pool"]), encoding="utf-8") as f:
    pool_raw = f.read()

# sanity: no closing-script sequence in the payload
assert "</" not in pool_raw or "</script" not in pool_raw.lower()

POOL_COUNT = len(json.loads(pool_raw))

css = r"""
body{background:#F2F4F7;margin:0}
.lk{
  --paper:#F2F4F7; --surface:#FFFFFF; --ink:#141A21; --muted:#66717F; --line:#DCE1E8;
  --axis:#12355B; --axis-soft:#E7EDF5; --ok:#0B6E4F; --ok-bg:#E5F2EC;
  --no:#A5231C; --no-bg:#FAE9E7; --mark:#B08200; --mark-bg:#FCF9EF;
  --display:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --body:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  background:var(--paper); color:var(--ink); font-family:var(--body);
  font-size:16px; line-height:1.55; min-height:100vh;
}
.lk *{box-sizing:border-box}
.lk .wrap{max-width:760px;margin:0 auto;padding:0 16px 56px}
.lk header{background:var(--axis);color:#fff;padding:22px 0 18px;margin-bottom:20px}
.lk header .wrap{padding-bottom:0}
.lk .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#9FB6D2;margin:0 0 6px}
.lk h1{font-family:var(--display);font-weight:600;font-size:23px;line-height:1.25;margin:0}
.lk h1 .sub{display:block;font-size:15px;font-weight:400;color:#B9CBE1;margin-top:5px;font-family:var(--body)}
.lk .loadnote{font-family:var(--mono);font-size:13px;color:var(--muted);padding-top:40px}

.lk .gauge{margin:16px 0 0}
.lk .gauge-row{display:flex;align-items:flex-end;gap:2px;height:26px}
.lk .tick{flex:1 1 0;background:#2E4F78;border-radius:1px;height:9px;transition:height .18s ease,background .18s ease}
.lk .tick.scored{background:#4FD09B;height:22px}
.lk .tick.missed{background:#E0736B;height:14px}
.lk .tick.current{background:#F2C63C;height:26px}
.lk .gauge-legend{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;color:#9FB6D2;margin-top:6px;letter-spacing:.04em}

.lk .card{background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:20px;margin-bottom:16px}
.lk .ch{font-family:var(--display);font-size:17px;font-weight:600;margin:0 0 12px}
.lk .lead{font-size:14.5px;color:#33404F;margin:0 0 14px}
.lk .footnote{font-size:13px;color:var(--muted);margin:0}

.lk .statgrid{display:flex;gap:24px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:16px}
.lk .stat{display:flex;flex-direction:column}
.lk .stat .num{font-family:var(--display);font-size:30px;line-height:1;color:var(--axis)}
.lk .stat .num .of{font-size:16px;color:var(--muted)}
.lk .stat .lab{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:6px}

.lk .meta{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:baseline;font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:16px}
.lk .meta .sect{color:var(--axis)}
.lk .meta .tag{color:var(--mark);border:1px solid #EADFBE;background:var(--mark-bg);border-radius:2px;padding:1px 6px;font-size:10px}
.lk .meta .hint{margin-left:auto;text-transform:none;letter-spacing:0;font-family:var(--body);font-size:12.5px}
.lk .stem{font-family:var(--display);font-size:19px;line-height:1.42;margin:0 0 16px}

.lk .opts{display:flex;flex-direction:column;gap:9px}
.lk .opt{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--line);border-radius:3px;background:#fff;padding:12px 13px;cursor:pointer;text-align:left;width:100%;font:inherit;color:inherit;transition:border-color .12s,background .12s}
.lk .opt:hover:not(:disabled){border-color:#A9B6C7}
.lk .opt:focus-visible{outline:2px solid var(--mark);outline-offset:2px}
.lk .opt .key{font-family:var(--mono);font-size:12px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:2px;width:24px;min-width:24px;height:24px;display:flex;align-items:center;justify-content:center;margin-top:1px}
.lk .opt.picked{background:var(--axis-soft);border-color:var(--axis)}
.lk .opt.picked .key{background:var(--axis);color:#fff;border-color:var(--axis)}
.lk .opt .txt{flex:1}
.lk .opt:disabled{cursor:default}
.lk .opt.frozen{opacity:.9}
.lk .opt.res-hit{border-color:var(--ok);background:var(--ok-bg)}
.lk .opt.res-hit .key{background:var(--ok);color:#fff;border-color:var(--ok)}
.lk .opt.res-missed{border-color:var(--ok);background:#fff;border-style:dashed}
.lk .opt.res-missed .key{color:var(--ok);border-color:var(--ok)}
.lk .opt.res-false{border-color:var(--no);background:var(--no-bg)}
.lk .opt.res-false .key{background:var(--no);color:#fff;border-color:var(--no)}
.lk .opt.res-clean{opacity:.72}
.lk .verdict{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px}
.lk .v-ok{color:var(--ok)}
.lk .v-no{color:var(--no)}
.lk .v-neutral{color:var(--muted)}
.lk .fb{display:block;font-size:14px;line-height:1.5;color:#33404F;margin-top:7px}

.lk .banner{border-left:3px solid var(--line);padding:10px 0 10px 14px;margin-top:16px;font-size:14.5px}
.lk .banner.point{border-color:var(--ok);color:var(--ok);font-weight:600}
.lk .banner.nopoint{border-color:var(--no);color:var(--no);font-weight:600}
.lk .banner small{display:block;font-weight:400;color:var(--muted);margin-top:3px;font-size:13px}

.lk .concept{border:1px solid #EADFBE;border-left:3px solid var(--mark);background:var(--mark-bg);border-radius:3px;padding:15px 17px;margin-top:16px}
.lk .concept .clabel{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--mark);margin-bottom:6px}
.lk .concept h3{font-family:var(--display);font-size:16.5px;font-weight:600;margin:0 0 9px}
.lk .concept ul{margin:0;padding-left:19px;font-size:14px;line-height:1.55;color:#33404F}
.lk .concept li{margin-bottom:6px}
.lk .concept li:last-child{margin-bottom:0}

.lk .confbox{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}
.lk .conftitle{font-family:var(--display);font-size:16.5px;margin:0 0 4px}
.lk .confhint{font-size:13px;color:var(--muted);margin:0 0 12px}
.lk .confrow{display:flex;gap:9px;flex-wrap:wrap}
.lk .confbtn{flex:1 1 180px;display:flex;flex-direction:column;gap:3px;text-align:left;border:1px solid var(--line);border-radius:3px;background:#fff;padding:11px 13px;cursor:pointer;font:inherit;color:inherit;transition:border-color .12s,background .12s}
.lk .confbtn:hover{border-color:var(--axis);background:var(--axis-soft)}
.lk .confbtn:focus-visible{outline:2px solid var(--mark);outline-offset:2px}
.lk .confbtn .cl{font-weight:600;font-size:14.5px}
.lk .confbtn .cn{font-size:12.5px;color:var(--muted)}

.lk .actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:18px}
.lk .wrapactions{margin-top:4px}
.lk button.primary{background:var(--axis);color:#fff;border:1px solid var(--axis);border-radius:3px;padding:12px 20px;font:600 15px/1 var(--body);cursor:pointer}
.lk button.primary:hover{background:#0D2A47}
.lk button.ghost{background:#fff;color:var(--axis);border:1px solid var(--line);border-radius:3px;padding:12px 18px;font:600 14.5px/1 var(--body);cursor:pointer}
.lk button.ghost:hover{border-color:var(--axis)}
.lk button.danger{background:#fff;color:var(--no);border:1px solid #E8C9C6;border-radius:3px;padding:12px 18px;font:600 14.5px/1 var(--body);cursor:pointer}
.lk button.danger:hover{border-color:var(--no)}
.lk button:focus-visible{outline:2px solid var(--mark);outline-offset:2px}
.lk button:disabled{opacity:.5;cursor:default}
.lk .scoreline{font-family:var(--mono);font-size:12.5px;color:var(--muted);margin-left:auto;letter-spacing:.04em}
.lk .aslabel{display:inline-flex;align-items:center;background:#fff;color:var(--axis);border:1px solid var(--line);border-radius:3px;padding:12px 18px;font:600 14.5px/1 var(--body);cursor:pointer}
.lk .aslabel:hover{border-color:var(--axis)}
.lk .impmsg{font-size:13.5px;margin:12px 0 0}
.lk .impmsg.good{color:var(--ok)}
.lk .impmsg.bad{color:var(--no)}
.lk .diag{margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.lk .diaglabel{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:7px}
.lk .diag code{display:inline-block;font-family:var(--mono);font-size:11.5px;background:var(--paper);border:1px solid var(--line);border-radius:2px;padding:3px 7px;margin:0 6px 6px 0;color:#33404F}

.lk .reviewlist{list-style:none;margin:0;padding:0}
.lk .reviewlist li{border-top:1px solid var(--line);padding:12px 0;display:flex;flex-direction:column;gap:3px}
.lk .reviewlist li:first-child{border-top:0;padding-top:0}
.lk .rk{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--axis)}
.lk .rs{font-family:var(--display);font-size:15.5px;line-height:1.4}
.lk .rc{font-size:13px;color:var(--muted)}

.lk .kalib{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}
.lk .krow{display:flex;align-items:center;gap:12px}
.lk .klabel{flex:0 0 118px;font-size:13.5px}
.lk .kbar{flex:1;height:10px;background:var(--axis-soft);border-radius:2px;overflow:hidden}
.lk .kfill{height:100%;background:var(--axis)}
.lk .kval{flex:0 0 84px;text-align:right;font-family:var(--mono);font-size:12.5px}
.lk .kn{display:block;font-size:10.5px;color:var(--muted)}

.lk .fcast{display:flex;gap:4px;align-items:flex-end}
.lk .fcol{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;min-width:0}
.lk .fbarwrap{width:100%;height:70px;display:flex;align-items:flex-end}
.lk .fbar{width:100%;background:var(--axis);border-radius:1px;min-height:2px}
.lk .fnum{font-family:var(--mono);font-size:11px;color:var(--axis);height:14px}
.lk .fday{font-family:var(--mono);font-size:9.5px;color:var(--muted);white-space:nowrap;transform:rotate(-45deg);transform-origin:center;height:22px}

.lk .kaplist{list-style:none;margin:0;padding:0}
.lk .kaplist li{display:flex;align-items:center;gap:12px;padding:9px 0;border-top:1px solid var(--line)}
.lk .kaplist li:first-child{border-top:0}
.lk .kapname{flex:1 1 auto;font-size:13.5px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lk .kapname b{font-family:var(--mono);color:var(--muted);font-weight:600;margin-right:5px}
.lk .kapbar{flex:0 0 70px;height:8px;background:var(--axis-soft);border-radius:2px;overflow:hidden}
.lk .kapfill{display:block;height:100%;background:var(--axis)}
.lk .kapnum{flex:0 0 84px;text-align:right;font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.lk .kapnum em{display:block;font-style:normal;color:var(--axis)}

@media (max-width:560px){
  .lk h1{font-size:20px}
  .lk .stem{font-size:17.5px}
  .lk .card{padding:16px}
  .lk .statgrid{gap:18px}
  .lk .stat .num{font-size:26px}
  .lk .klabel{flex:0 0 92px;font-size:12.5px}
  .lk .kapname{font-size:12.5px}
  .lk .fday{font-size:8.5px}
}
@media (prefers-reduced-motion:reduce){
  .lk *{transition:none !important}
}
"""

app_js = r"""
const { useState, useEffect, useMemo, useCallback, useRef, Fragment } = React;
const h = React.createElement;

const POOL = JSON.parse(document.getElementById("pool-data").textContent);

const KAPITEL = __KAPITEL_JSON__;

const STORE_KEY = __STORE_KEY_JSON__;
const DB_PATH = "progress/state";
const SESSION_SIZE = 20;
const NEW_QUOTA = 8;   // reservierte Plätze für neuen Stoff — sonst verdrängen
                       // Wiederholungen ihn, und der Pool ist nie komplett durch
const DAY = 86400000;

/* ══════════════ FSRS ══════════════
   FSRS-4.5 mit Standardgewichten. Retrievability wird aus der tatsächlich
   verstrichenen Zeit berechnet — vorgezogene Wiederholungen wachsen dadurch
   automatisch nur anteilig im Intervall. */
const W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031,
           1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755];
const DECAY = -0.5;
const FACTOR = 19 / 81;
const TARGET_R = 0.93;   // höher als der FSRS-Standard 0.90: Prüfungsvorbereitung
const MAX_INTERVAL = 60; // Tage — nichts verschwindet für Monate aus dem Umlauf

const clampD = (d) => Math.min(Math.max(d, 1), 10);
const clampS = (s) => Math.max(s, 0.01);

function retrievability(elapsedDays, stability) {
  if (stability <= 0) return 0;
  return Math.pow(1 + FACTOR * (elapsedDays / stability), DECAY);
}
function intervalFrom(stability) {
  const raw = (stability / FACTOR) * (Math.pow(TARGET_R, 1 / DECAY) - 1);
  return Math.min(MAX_INTERVAL, Math.max(1, Math.round(raw)));
}
function initCard(grade) {
  const S = clampS(W[grade - 1]);
  const D = clampD(W[4] - Math.exp(W[5] * (grade - 1)) + 1);
  return { S, D };
}
function nextDifficulty(D, grade) {
  const dDelta = D - W[6] * (grade - 3);
  const dInit4 = W[4] - Math.exp(W[5] * 3) + 1;
  return clampD(W[7] * dInit4 + (1 - W[7]) * dDelta);
}
function nextStability(D, S, R, grade) {
  if (grade === 1) {
    const sFail = W[11] * Math.pow(D, -W[12]) * (Math.pow(S + 1, W[13]) - 1) * Math.exp(W[14] * (1 - R));
    return clampS(Math.min(sFail, S));
  }
  const hard = grade === 2 ? W[15] : 1;
  const easy = grade === 4 ? W[16] : 1;
  const growth = 1 + Math.exp(W[8]) * (11 - D) * Math.pow(S, -W[9]) *
    (Math.exp(W[10] * (1 - R)) - 1) * hard * easy;
  return clampS(S * growth);
}
function schedule(card, grade, nowMs) {
  let S, D;
  if (!card) {
    const init = initCard(grade);
    S = init.S; D = init.D;
  } else {
    const elapsed = Math.max(0, (nowMs - card.last) / DAY);
    const R = retrievability(elapsed, card.S);
    D = nextDifficulty(card.D, grade);
    S = nextStability(D, card.S, R, grade);
  }
  const days = intervalFrom(S);
  return {
    S, D,
    last: nowMs,
    due: nowMs + days * DAY,
    reps: (card?.reps || 0) + 1,
    lapses: (card?.lapses || 0) + (grade === 1 ? 1 : 0),
    interval: days,
  };
}

/* ══════════════ Hilfsfunktionen ══════════════ */
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
const startOfDay = (ms) => { const d = new Date(ms); d.setHours(0, 0, 0, 0); return d.getTime(); };
const deDate = (ms) => new Date(ms).toLocaleDateString("de-AT", { day: "2-digit", month: "2-digit" });

/* Zusammenstellung einer Session: erst Platz für neuen Stoff reservieren,
   dann fällige Wiederholungen, dann auffüllen, zuletzt vorziehen. */
function planSession(buckets) {
  const picked = [];
  const seen = new Set();
  const add = (list, cap) => {
    for (const q of list) {
      if (picked.length >= cap) break;
      if (seen.has(q.id)) continue;
      seen.add(q.id);
      picked.push(q);
    }
  };
  const neuQuote = Math.min(NEW_QUOTA, buckets.neu.length);
  add(buckets.due, SESSION_SIZE - neuQuote);
  add(buckets.neu, SESSION_SIZE);
  add(buckets.due, SESSION_SIZE);
  const vorNeu = picked.length;
  add(buckets.early, SESSION_SIZE);
  const vorgezogen = new Set(picked.slice(vorNeu).map((q) => q.id));
  const counts = {
    due: picked.filter((q) => buckets.due.includes(q)).length,
    neu: picked.filter((q) => buckets.neu.includes(q)).length,
    early: vorgezogen.size,
  };
  return { picked, vorgezogen, counts };
}

const CONFIDENCE = [
  { key: 1, grade: 2, label: "Unsicher", note: "geraten oder stark geschwankt" },
  { key: 2, grade: 3, label: "Ziemlich sicher", note: "kurz überlegt, dann klar" },
  { key: 3, grade: 4, label: "Sofort klar", note: "ohne Zögern gewusst" },
];

/* ══════════════ App ══════════════ */
function Lernkonsole() {
  const [state, setState] = useState(null);       // {cards, log, meta}
  const [loading, setLoading] = useState(true);
  const [storageMode, setStorageMode] = useState("checking"); // cloud | local
  const [view, setView] = useState("home");        // home | session | ende | dashboard
  const [session, setSession] = useState(null);
  const dbRef = useRef(null);

  /* — Pool einmalig beim Start durchmischen — */
  const shuffledPool = useMemo(() => shuffle(POOL), []);
  const byId = useMemo(() => {
    const m = {};
    POOL.forEach((q) => (m[q.id] = q));
    return m;
  }, []);

  /* — Laden: zuerst der Cloud-Speicher dieser Seite, sonst dieser Browser — */
  useEffect(() => {
    let alive = true;
    const leer = { cards: {}, log: [], meta: { sessions: 0, days: [] } };
    const normalisieren = (raw) => ({
      cards: raw.cards || {},
      log: raw.log || [],
      meta: { sessions: 0, days: [], ...(raw.meta || {}) },
    });

    (async () => {
      let loaded = null;
      let mode = "local";

      try {
        if (typeof window.claude !== "undefined") {
          const db = await window.claude.use("db");
          if (db) {
            dbRef.current = db;
            mode = "cloud";
            const snap = await db.doc(DB_PATH).get();
            if (snap.exists) {
              const data = snap.data();
              if (data && typeof data.cards === "object") loaded = normalisieren(data);
            }
          }
        }
      } catch (e) { /* Cloud-Speicher nicht erreichbar */ }

      if (!loaded) {
        try {
          const raw = localStorage.getItem(STORE_KEY);
          if (raw) loaded = normalisieren(JSON.parse(raw));
        } catch (e) { /* lokaler Speicher nicht lesbar */ }
      }

      if (alive) {
        setState(loaded || leer);
        setStorageMode(mode);
        setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const persist = useCallback(async (next) => {
    setState(next);
    const payload = { cards: next.cards, log: next.log.slice(-3000), meta: next.meta };
    try {
      if (dbRef.current) {
        await dbRef.current.doc(DB_PATH).set(payload);
      } else {
        localStorage.setItem(STORE_KEY, JSON.stringify(payload));
      }
    } catch (e) {
      console.error("Speichern fehlgeschlagen", e);
      try { localStorage.setItem(STORE_KEY, JSON.stringify(payload)); } catch (e2) { /* auch das ging nicht */ }
    }
  }, []);

  /* — Auswahl der Session: fällig → neu → vorgezogen — */
  const buckets = useMemo(() => {
    if (!state) return { due: [], neu: [], early: [] };
    const now = Date.now();
    const due = [], neu = [], early = [];
    shuffledPool.forEach((q) => {
      const c = state.cards[q.id];
      if (!c) neu.push(q);
      else if (c.due <= now) due.push(q);
      else early.push(q);
    });
    due.sort((a, b) => state.cards[a.id].due - state.cards[b.id].due);
    early.sort((a, b) => state.cards[a.id].due - state.cards[b.id].due);
    return { due, neu, early };
  }, [state, shuffledPool]);

  const plan = useMemo(() => planSession(buckets), [buckets]);

  function startSession() {
    const items = shuffle(plan.picked).map((q) => ({
      q,
      order: shuffle([0, 1, 2, 3]),
      vorgezogen: plan.vorgezogen.has(q.id),
    }));
    setSession({ items, idx: 0, phase: "answer", picks: [], results: [] });
    setView("session");
  }

  if (loading) {
    return h("div", { className: "lk" },
      h(Styles, null),
      h("div", { className: "wrap" }, h("p", { className: "loadnote" }, "Fortschritt wird geladen …"))
    );
  }

  return h("div", { className: "lk" },
    h(Styles, null),
    view === "home" ? h(Home, { buckets, plan, state, onStart: startSession, onDash: () => setView("dashboard") }) : null,
    (view === "session" && session) ? h(Session, { session, setSession, state, persist, onDone: () => setView("ende") }) : null,
    (view === "ende" && session) ? h(Ende, { session, byId, onHome: () => { setSession(null); setView("home"); }, onDash: () => setView("dashboard") }) : null,
    view === "dashboard" ? h(Dashboard, { state, persist, storageMode, onHome: () => setView("home") }) : null
  );
}

/* ══════════════ Startbildschirm ══════════════ */
function Home({ buckets, plan, state, onStart, onDash }) {
  const total = POOL.length;
  const gesehen = Object.keys(state.cards).length;
  const faellig = buckets.due.length;
  const neu = buckets.neu.length;
  const c = plan.counts;
  const teile = [];
  if (c.due) teile.push(`${c.due} fällige`);
  if (c.neu) teile.push(`${c.neu} neue`);
  if (c.early) teile.push(`${c.early} vorgezogene`);
  const zusammensetzung = teile.length > 1
    ? teile.slice(0, -1).join(", ") + " und " + teile[teile.length - 1]
    : teile[0] || "";

  return h(Fragment, null,
    h("header", null,
      h("div", { className: "wrap" },
        h("p", { className: "eyebrow" }, "Aufnahmetest Psychologie"),
        h("h1", null, __APP_TITLE_JSON__, h("span", { className: "sub" }, __APP_SUBTITLE_JSON__))
      )
    ),
    h("div", { className: "wrap" },
      h("div", { className: "card" },
        h("div", { className: "statgrid" },
          h("div", { className: "stat" }, h("span", { className: "num" }, faellig), h("span", { className: "lab" }, "fällig")),
          h("div", { className: "stat" }, h("span", { className: "num" }, neu), h("span", { className: "lab" }, "noch nie gesehen")),
          h("div", { className: "stat" }, h("span", { className: "num" }, gesehen, h("span", { className: "of" }, "/", total)), h("span", { className: "lab" }, "im Umlauf"))
        ),
        h("p", { className: "lead" },
          plan.picked.length === 0
            ? "Der Pool ist leer."
            : `Die nächste Session bringt ${zusammensetzung} ${plan.picked.length === 1 ? "Frage" : "Fragen"}, quer durch alle Kapitel gemischt.`,
          c.early > 0 ? " Vorgezogene Wiederholungen wachsen im Intervall nur anteilig." : null
        ),
        h("div", { className: "actions" },
          h("button", { className: "primary", onClick: onStart }, "Session starten"),
          h("button", { className: "ghost", onClick: onDash }, "Auswertung")
        )
      ),
      h("p", { className: "footnote" }, "Die Antwortoptionen werden bei jeder Frage neu gemischt. Ein Punkt zählt nur, wenn alle vier Optionen richtig bewertet sind.")
    )
  );
}

/* ══════════════ Session ══════════════ */
function Session({ session, setSession, state, persist, onDone }) {
  const { items, idx, phase, picks, results } = session;
  const item = items[idx];
  const q = item.q;
  const opts = item.order.map((i) => q.opts[i]);

  const toggle = (i) => {
    if (phase !== "answer") return;
    const next = picks.includes(i) ? picks.filter((x) => x !== i) : [...picks, i];
    setSession({ ...session, picks: next });
  };

  const askConfidence = () => setSession({ ...session, phase: "confidence" });

  const submit = async (conf) => {
    const korrekt = opts.every((o, i) => o.c === picks.includes(i));
    const grade = korrekt ? conf.grade : 1;
    const now = Date.now();
    const card = state.cards[q.id];
    const updated = schedule(card, grade, now);

    const nextState = {
      cards: { ...state.cards, [q.id]: updated },
      log: [...state.log, { id: q.id, ts: now, grade, korrekt, conf: conf.key, kap: q.kap }],
      meta: {
        ...state.meta,
        days: Array.from(new Set([...(state.meta.days || []), startOfDay(now)])).sort(),
      },
    };
    await persist(nextState);

    setSession({
      ...session,
      phase: "review",
      results: [...results, { id: q.id, korrekt, conf: conf.key, interval: updated.interval, picks: picks.slice(), order: item.order }],
    });
  };

  const weiter = () => {
    if (idx + 1 >= items.length) { onDone(); return; }
    setSession({ ...session, idx: idx + 1, phase: "answer", picks: [] });
  };

  const punkte = results.filter((r) => r.korrekt).length;
  const letzte = phase === "review" ? results[results.length - 1] : null;

  return h(Fragment, null,
    h("header", null,
      h("div", { className: "wrap" },
        h("p", { className: "eyebrow" }, "Frage ", idx + 1, " von ", items.length),
        h("h1", null, "Gemischter Durchgang", h("span", { className: "sub" }, KAPITEL[q.kap])),
        h("div", { className: "gauge" },
          h("div", { className: "gauge-row" },
            items.map((_, i) => {
              const r = results[i];
              let cls = "tick";
              if (r) cls += r.korrekt ? " scored" : " missed";
              else if (i === idx) cls += " current";
              return h("span", { key: i, className: cls });
            })
          ),
          h("div", { className: "gauge-legend" },
            h("span", null, punkte, " Punkte"),
            h("span", null, results.length, " bewertet")
          )
        )
      )
    ),
    h("div", { className: "wrap" },
      h("div", { className: "card" },
        h("div", { className: "meta" },
          h("span", { className: "sect" }, q.sec),
          item.vorgezogen ? h("span", { className: "tag" }, "vorgezogen") : null,
          h("span", { className: "hint" }, "Mehrfachauswahl · 1–4 richtig")
        ),
        h("p", { className: "stem" }, q.stem),
        h("div", { className: "opts" },
          opts.map((o, i) => {
            const picked = picks.includes(i);
            let cls = "opt";
            let zustand = null;
            if (phase === "answer" || phase === "confidence") {
              if (picked) cls += " picked";
              if (phase === "confidence") cls += " frozen";
            } else if (o.c && picked) {
              cls += " res-hit"; zustand = { t: "Richtig – korrekt markiert", k: "v-ok" };
            } else if (o.c && !picked) {
              cls += " res-missed"; zustand = { t: "Richtig – nicht markiert", k: "v-no" };
            } else if (!o.c && picked) {
              cls += " res-false"; zustand = { t: "Falsch – fälschlich markiert", k: "v-no" };
            } else {
              cls += " res-clean"; zustand = { t: "Falsch – korrekt ausgelassen", k: "v-neutral" };
            }
            return h("button", {
              key: i, className: cls, onClick: () => toggle(i), disabled: phase !== "answer", "aria-pressed": picked
            },
              h("span", { className: "key" }, "abcd"[i]),
              h("span", { className: "txt" },
                zustand ? h("span", { className: "verdict " + zustand.k }, zustand.t) : null,
                o.t,
                phase === "review" ? h("span", { className: "fb" }, o.fb) : null
              )
            );
          })
        ),
        phase === "answer" ? h("div", { className: "actions" },
          h("button", { className: "primary", onClick: askConfidence }, "Antwort prüfen"),
          h("span", { className: "scoreline" }, picks.length, " ausgewählt")
        ) : null,
        phase === "confidence" ? h("div", { className: "confbox" },
          h("p", { className: "conftitle" }, "Wie sicher warst du?"),
          h("p", { className: "confhint" }, "Noch vor dem Ergebnis — nur so lässt sich später ablesen, wie gut dein Sicherheitsgefühl trägt."),
          h("div", { className: "confrow" },
            CONFIDENCE.map((c) => h("button", { key: c.key, className: "confbtn", onClick: () => submit(c) },
              h("span", { className: "cl" }, c.label),
              h("span", { className: "cn" }, c.note)
            ))
          )
        ) : null,
        (phase === "review" && letzte) ? h(Fragment, null,
          h("div", { className: "banner " + (letzte.korrekt ? "point" : "nopoint") },
            letzte.korrekt ? "Punkt" : "Kein Punkt",
            h("small", null, letzte.korrekt
              ? `Alle vier Optionen richtig bewertet. Wiedervorlage in ${letzte.interval} ${letzte.interval === 1 ? "Tag" : "Tagen"}.`
              : `Mindestens eine Option falsch bewertet. Wiedervorlage in ${letzte.interval} ${letzte.interval === 1 ? "Tag" : "Tagen"}.`)
          ),
          h("div", { className: "concept" },
            h("span", { className: "clabel" }, "Konzept"),
            h("h3", null, q.concept.title),
            h("ul", null, q.concept.points.map((p, i) => h("li", { key: i, dangerouslySetInnerHTML: { __html: p } })))
          ),
          h("div", { className: "actions" },
            h("button", { className: "primary", onClick: weiter }, idx + 1 >= items.length ? "Session abschließen" : "Weiter"),
            h("span", { className: "scoreline" }, punkte, " / ", results.length)
          )
        ) : null
      )
    )
  );
}

/* ══════════════ Sessionende ══════════════ */
function Ende({ session, byId, onHome, onDash }) {
  const { results } = session;
  const punkte = results.filter((r) => r.korrekt).length;
  const quote = results.length ? Math.round((punkte / results.length) * 100) : 0;
  const fehler = results.filter((r) => !r.korrekt);
  const unsicherRichtig = results.filter((r) => r.korrekt && r.conf === 1);

  return h(Fragment, null,
    h("header", null,
      h("div", { className: "wrap" },
        h("p", { className: "eyebrow" }, "Session abgeschlossen"),
        h("h1", null, punkte, " von ", results.length, " Punkten", h("span", { className: "sub" }, quote, " % vollständig richtig bewertet"))
      )
    ),
    h("div", { className: "wrap" },
      fehler.length > 0 ? h("div", { className: "card" },
        h("h2", { className: "ch" }, "Ohne Punkt (", fehler.length, ")"),
        h("ul", { className: "reviewlist" },
          fehler.map((r, i) => {
            const q = byId[r.id];
            return h("li", { key: i },
              h("span", { className: "rk" }, q.sec),
              h("span", { className: "rs" }, q.stem),
              h("span", { className: "rc" }, q.concept.title)
            );
          })
        )
      ) : null,
      unsicherRichtig.length > 0 ? h("div", { className: "card" },
        h("h2", { className: "ch" }, "Richtig, aber unsicher (", unsicherRichtig.length, ")"),
        h("p", { className: "lead" }, "Diese Fragen kommen bewusst früher zurück als die sicher gewussten — das Wissen sitzt noch nicht fest."),
        h("ul", { className: "reviewlist" },
          unsicherRichtig.map((r, i) => {
            const q = byId[r.id];
            return h("li", { key: i },
              h("span", { className: "rk" }, q.sec),
              h("span", { className: "rs" }, q.stem)
            );
          })
        )
      ) : null,
      (fehler.length === 0 && unsicherRichtig.length === 0) ? h("div", { className: "card" },
        h("p", { className: "lead" }, "Alle ", results.length, " Fragen sicher und vollständig richtig bewertet.")
      ) : null,
      h("div", { className: "actions wrapactions" },
        h("button", { className: "primary", onClick: onHome }, "Zurück zum Start"),
        h("button", { className: "ghost", onClick: onDash }, "Auswertung")
      )
    )
  );
}

/* ══════════════ Auswertung ══════════════ */
function Dashboard({ state, persist, storageMode, onHome }) {
  const [confirmReset, setConfirmReset] = useState(false);
  const [importMeldung, setImportMeldung] = useState(null);
  const log = state.log;

  const importieren = (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const raw = JSON.parse(String(reader.result));
        if (!raw || typeof raw.cards !== "object" || raw.cards === null) {
          setImportMeldung({ ok: false, text: "Die Datei enthält keinen Kartenstand." });
          return;
        }
        const eigene = new Set(POOL.map((q) => q.id));
        const cards = {};
        let fremd = 0;
        Object.entries(raw.cards).forEach(([id, c]) => {
          if (eigene.has(id)) cards[id] = c; else fremd++;
        });
        await persist({
          cards,
          log: Array.isArray(raw.log) ? raw.log : [],
          meta: { sessions: 0, days: [], ...(raw.meta || {}) },
        });
        setImportMeldung({
          ok: true,
          text: Object.keys(cards).length + " Fragen wiederhergestellt" +
                (fremd ? ", " + fremd + " nicht zuordenbare übersprungen." : "."),
        });
      } catch (e) {
        setImportMeldung({ ok: false, text: "Die Datei ließ sich nicht lesen." });
      }
    };
    reader.readAsText(file);
    ev.target.value = "";
  };

  /* Kalibrierung */
  const kalib = CONFIDENCE.map((c) => {
    const rows = log.filter((l) => l.conf === c.key);
    const richtig = rows.filter((l) => l.korrekt).length;
    return { ...c, n: rows.length, quote: rows.length ? Math.round((richtig / rows.length) * 100) : null };
  });

  /* Fälligkeitsvorschau 14 Tage */
  const heute = startOfDay(Date.now());
  const forecast = [];
  for (let d = 0; d < 14; d++) {
    const tag = heute + d * DAY;
    const n = Object.values(state.cards).filter((c) => startOfDay(c.due) === tag).length;
    forecast.push({ tag, n });
  }
  const rueckstand = Object.values(state.cards).filter((c) => c.due < heute).length;
  const maxF = Math.max(1, ...forecast.map((f) => f.n));

  /* Abdeckung pro Kapitel */
  const abdeckung = Object.keys(KAPITEL).map((k) => {
    const kap = Number(k);
    const alle = POOL.filter((q) => q.kap === kap);
    const gesehen = alle.filter((q) => state.cards[q.id]).length;
    const rows = log.filter((l) => l.kap === kap);
    const quote = rows.length ? Math.round((rows.filter((l) => l.korrekt).length / rows.length) * 100) : null;
    return { kap, name: KAPITEL[kap], n: alle.length, gesehen, quote };
  });

  const exportieren = async () => {
    const payload = JSON.stringify({ cards: state.cards, log: state.log, meta: state.meta }, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    try {
      const downloads = (typeof window.claude !== "undefined") ? await window.claude.use("downloads") : null;
      if (downloads) {
        await downloads.save({ filename: "lernkonsole-fortschritt.json", data: blob });
        setImportMeldung({ ok: true, text: "Sicherungsdatei gespeichert." });
        return;
      }
    } catch (e) {
      if (e && e.code === "declined") return;
      setImportMeldung({ ok: false, text: "Sicherung fehlgeschlagen." });
      return;
    }
    // Außerhalb der Artifact-Ansicht (z. B. eigenständig gehostet): normaler Download.
    try {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "lernkonsole-fortschritt.json";
      a.click();
      URL.revokeObjectURL(url);
      setImportMeldung({ ok: true, text: "Sicherungsdatei heruntergeladen." });
    } catch (e) {
      setImportMeldung({ ok: false, text: "Sicherung fehlgeschlagen." });
    }
  };

  const zuruecksetzen = async () => {
    await persist({ cards: {}, log: [], meta: { sessions: 0, days: [] } });
    setConfirmReset(false);
  };

  const gesamt = log.length;
  const gesamtQuote = gesamt ? Math.round((log.filter((l) => l.korrekt).length / gesamt) * 100) : null;

  return h(Fragment, null,
    h("header", null,
      h("div", { className: "wrap" },
        h("p", { className: "eyebrow" }, "Auswertung"),
        h("h1", null, "Was der Verlauf zeigt", h("span", { className: "sub" }, gesamt, " Bewertungen", gesamtQuote !== null ? ` · ${gesamtQuote} % mit Punkt` : ""))
      )
    ),
    h("div", { className: "wrap" },

      h("div", { className: "card" },
        h("h2", { className: "ch" }, "Sicherheitsgefühl gegen Trefferquote"),
        gesamt === 0
          ? h("p", { className: "lead" }, "Noch keine Daten. Nach der ersten Session steht hier, wie verlässlich dein Sicherheitsgefühl ist.")
          : h(Fragment, null,
              h("div", { className: "kalib" },
                kalib.map((k) => h("div", { className: "krow", key: k.key },
                  h("span", { className: "klabel" }, k.label),
                  h("div", { className: "kbar" }, h("div", { className: "kfill", style: { width: (k.quote ?? 0) + "%" } })),
                  h("span", { className: "kval" }, k.quote === null ? "–" : k.quote + " %", h("span", { className: "kn" }, "n=", k.n))
                ))
              ),
              h("p", { className: "footnote" }, "Gut kalibriert heißt: Die Quote steigt von oben nach unten deutlich an. Liegt „Sofort klar“ merklich unter 90 %, überschätzt du dich — liegt „Unsicher“ hoch, traust du dir zu wenig zu.")
            )
      ),

      h("div", { className: "card" },
        h("h2", { className: "ch" }, "Die nächsten 14 Tage"),
        rueckstand > 0 ? h("p", { className: "lead" }, rueckstand, rueckstand === 1 ? " Frage ist" : " Fragen sind", " überfällig.") : null,
        h("div", { className: "fcast" },
          forecast.map((f, i) => h("div", { className: "fcol", key: i },
            h("div", { className: "fbarwrap" }, h("div", { className: "fbar", style: { height: Math.round((f.n / maxF) * 100) + "%" }, title: f.n + " fällig" })),
            h("span", { className: "fnum" }, f.n || ""),
            h("span", { className: "fday" }, i === 0 ? "heute" : deDate(f.tag))
          ))
        )
      ),

      h("div", { className: "card" },
        h("h2", { className: "ch" }, "Abdeckung nach Kapitel"),
        h("ul", { className: "kaplist" },
          abdeckung.map((a) => h("li", { key: a.kap },
            h("span", { className: "kapname" }, h("b", null, a.kap), " ", a.name),
            h("span", { className: "kapbar" }, h("span", { className: "kapfill", style: { width: Math.round((a.gesehen / a.n) * 100) + "%" } })),
            h("span", { className: "kapnum" }, a.gesehen, "/", a.n, a.quote !== null ? h("em", null, a.quote, " %") : null)
          ))
        )
      ),

      h("div", { className: "card" },
        h("h2", { className: "ch" }, "Fortschritt sichern und wiederherstellen"),
        h("p", { className: "lead" },
          storageMode === "cloud"
            ? "Der Fortschritt wird laufend online gespeichert und ist bei jedem Öffnen dieser Seite im gleichen Konto wieder da. Die Sicherungsdatei bleibt trotzdem sinnvoll, etwa um auf einem anderen Konto weiterzumachen."
            : "Cloud-Speicher ist in dieser Ansicht nicht verfügbar — der Fortschritt liegt nur lokal in diesem Browser. Sichere ihn regelmäßig als Datei, um ihn nicht zu verlieren."
        ),
        h("div", { className: "actions" },
          h("button", { className: "ghost", onClick: exportieren }, "Als Datei sichern"),
          h("label", { className: "ghost aslabel" }, "Aus Datei laden",
            h("input", { type: "file", accept: "application/json,.json", onChange: importieren, hidden: true })
          ),
          !confirmReset
            ? h("button", { className: "danger", onClick: () => setConfirmReset(true) }, "Alles zurücksetzen")
            : h(Fragment, null,
                h("button", { className: "danger", onClick: zuruecksetzen }, "Wirklich löschen"),
                h("button", { className: "ghost", onClick: () => setConfirmReset(false) }, "Abbrechen")
              )
        ),
        importMeldung ? h("p", { className: "impmsg " + (importMeldung.ok ? "good" : "bad") }, importMeldung.text) : null,
        h("div", { className: "diag" },
          h("span", { className: "diaglabel" }, "Speicherstatus"),
          h("code", null, storageMode === "cloud" ? "Cloud-Speicher verbunden" : storageMode === "local" ? "nur lokal in diesem Browser" : "wird geprüft …")
        )
      ),

      h("div", { className: "actions wrapactions" },
        h("button", { className: "primary", onClick: onHome }, "Zurück zum Start")
      )
    )
  );
}

/* ══════════════ Styles ══════════════ */
const STYLES_CSS = __CSS_JSON__;
function Styles() {
  return h("style", null, STYLES_CSS);
}

ReactDOM.createRoot(document.getElementById("root")).render(h(Lernkonsole));
"""

app_js = (
    app_js.replace("__CSS_JSON__", json.dumps(css))
    .replace("__KAPITEL_JSON__", json.dumps({str(k): v for k, v in CONFIG["kapitel"].items()}, ensure_ascii=False))
    .replace("__STORE_KEY_JSON__", json.dumps(CONFIG["storeKey"]))
    .replace("__APP_TITLE_JSON__", json.dumps(CONFIG["title"], ensure_ascii=False))
    .replace("__APP_SUBTITLE_JSON__", json.dumps(CONFIG["subtitle"].replace("{n}", str(POOL_COUNT)), ensure_ascii=False))
)

html = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>__PAGE_TITLE__</title>
</head>
<body>
<div id="root"></div>
<script type="application/json" id="pool-data">__POOL_JSON__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js"></script>
<script>
__APP_JS__
</script>
</body>
</html>
"""
html = (
    html.replace("__PAGE_TITLE__", CONFIG["title"])
    .replace("__POOL_JSON__", pool_raw)
    .replace("__APP_JS__", app_js)
)

out_path = os.path.join(REPO, CONFIG["out"])
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print("wrote", out_path, "—", POOL_COUNT, "Fragen,", len(html.encode("utf-8")), "bytes")
