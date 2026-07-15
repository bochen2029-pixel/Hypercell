#!/usr/bin/env python3
# ruff: noqa: E501, B905  -- self-contained tool; embedded HTML/CSS/JS lines are long by nature
"""hypercell Medium viewer — a live, read-only web dashboard for the swarm's Medium.

The Medium (`<home>/_medium/medium.db`) is hypercell's shared coordination log — the
stigmergic blackboard cells fan out over. This is its viewer, the hypercell analog of
Intercom's broadcast.db dashboard: watch cultures (runs) spawn, cells submit candidates,
the oracle score, and a champion emerge, live.

Point-and-run, stdlib only (no pip):
    python tools/medium_viewer.py                      # auto-finds .hypercellstate/_medium/medium.db
    python tools/medium_viewer.py --port 8799
    python tools/medium_viewer.py --home C:\\hypercell\\.hypercellstate
    python tools/medium_viewer.py --db path/to/medium.db --no-open

Safety: every request opens a fresh read-only connection (PRAGMA query_only=ON) with a
short busy_timeout — it can never modify the Medium and never blocks the live writers
(WAL readers don't block writers).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DB_PATH: Path | None = None


# --------------------------------------------------------------------------- db (read-only)
def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH), timeout=5.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=4000")
    return con


def rows(sql: str, params: tuple = ()) -> list[dict]:
    con = connect()
    try:
        cur = con.execute(sql, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        con.close()


def _preview(body: str | None, n: int = 240) -> str:
    if not body:
        return ""
    try:
        v = json.loads(body)
    except Exception:
        v = body
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + " …"


# --------------------------------------------------------------------------- api
def api_overview() -> dict:
    total = rows("SELECT count(*) c FROM messages")[0]["c"]
    cultures = rows(
        """SELECT culture,
                  count(*) msgs,
                  count(DISTINCT sender) cells,
                  max(round) rounds,
                  max(ts) last_ts,
                  min(ts) first_ts
           FROM messages GROUP BY culture ORDER BY last_ts DESC"""
    )
    types = rows("SELECT type, count(*) c FROM messages GROUP BY type ORDER BY c DESC")
    return {
        "db": str(DB_PATH),
        "db_bytes": DB_PATH.stat().st_size if DB_PATH and DB_PATH.exists() else 0,
        "total": total,
        "cultures": cultures,
        "types": {t["type"]: t["c"] for t in types},
    }


def api_culture(culture: str, after: int = 0) -> dict:
    msgs = rows(
        """SELECT seq, ts, sender, recipient, type, round, body, artifact
           FROM messages WHERE culture=? AND seq>? ORDER BY seq""",
        (culture, after),
    )
    for m in msgs:
        m["preview"] = _preview(m.pop("body", None))
        art = m.pop("artifact", None)
        m["artifact"] = _preview(art, 160) if art else None
    cells = sorted({m["sender"] for m in msgs} | set(
        r["sender"] for r in rows("SELECT DISTINCT sender FROM messages WHERE culture=?", (culture,))
    ))
    return {"culture": culture, "cells": cells, "messages": msgs}


# --------------------------------------------------------------------------- html (embedded)
HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>hypercell · Medium</title>
<style>
 :root{--bg:#0b0f0d;--panel:#121815;--line:#223028;--fg:#d7e2da;--dim:#7f8f86;--acc:#57d38c;--hot:#f0b45a;--blue:#6ab7ff}
 *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.5 ui-monospace,Consolas,monospace}
 header{display:flex;gap:16px;align-items:baseline;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--panel)}
 header h1{font-size:15px;margin:0;color:var(--acc);letter-spacing:.5px}
 header .meta{color:var(--dim)} header .live{margin-left:auto;color:var(--acc)}
 .wrap{display:flex;height:calc(100vh - 44px)}
 .side{width:320px;min-width:320px;border-right:1px solid var(--line);overflow:auto;background:var(--panel)}
 .main{flex:1;overflow:auto;padding:0 0 40px}
 .cult{padding:10px 14px;border-bottom:1px solid var(--line);cursor:pointer}
 .cult:hover{background:#182320} .cult.sel{background:#1c2a24;border-left:3px solid var(--acc)}
 .cult .id{color:var(--fg);font-weight:600} .cult .sub{color:var(--dim);font-size:12px;margin-top:2px}
 .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#3a463f;margin-right:6px}
 .dot.on{background:var(--acc);box-shadow:0 0 6px var(--acc)}
 .rnd{position:sticky;top:0;background:#0e1512;color:var(--hot);padding:6px 16px;border-bottom:1px solid var(--line);font-weight:600}
 .msg{display:grid;grid-template-columns:52px 90px 90px 1fr;gap:10px;padding:6px 16px;border-bottom:1px solid #16201b;align-items:start}
 .msg:hover{background:#10160f} .seq{color:var(--dim)} .snd{color:var(--blue);font-weight:600}
 .ty{color:var(--dim)} .ty.submission{color:var(--acc)} .ty.champion,.ty.score{color:var(--hot)}
 .bd{white-space:pre-wrap;word-break:break-word;color:#cdd8d0} .art{color:var(--dim);font-size:12px;margin-top:2px}
 .empty{padding:40px;color:var(--dim);text-align:center}
 .pill{display:inline-block;padding:1px 7px;border:1px solid var(--line);border-radius:10px;color:var(--dim);margin-left:6px}
</style></head><body>
<header>
 <h1>hypercell · Medium</h1>
 <span class="meta" id="db"></span>
 <span class="meta" id="tot"></span>
 <span class="live" id="live">● live</span>
</header>
<div class="wrap">
 <div class="side" id="side"></div>
 <div class="main" id="main"><div class="empty">pick a culture (run) on the left to watch the swarm</div></div>
</div>
<script>
let SEL=null, seen=0;
const $=id=>document.getElementById(id);
function ago(ts){ if(!ts)return''; const d=(Date.now()-Date.parse(ts))/1000;
  if(d<60)return Math.round(d)+'s'; if(d<3600)return Math.round(d/60)+'m'; return Math.round(d/3600)+'h'; }
async function overview(){
  const o=await (await fetch('/api/overview')).json();
  $('db').textContent=o.db+'  ('+(o.db_bytes/1024).toFixed(0)+' KB)';
  $('tot').textContent=o.total+' messages · '+o.cultures.length+' cultures';
  $('side').innerHTML=o.cultures.map(c=>{
    const live=(Date.now()-Date.parse(c.last_ts))<8000;
    return `<div class="cult ${c.culture===SEL?'sel':''}" onclick="pick('${c.culture}')">
      <div class="id"><span class="dot ${live?'on':''}"></span>${c.culture}</div>
      <div class="sub">${c.cells} cells · ${c.msgs} msgs · ${c.rounds||0} rounds · ${ago(c.last_ts)} ago</div></div>`;
  }).join('')|| '<div class="empty">no runs yet — try<br><br>hc run tournament --n 6 ...</div>';
}
async function stream(reset){
  if(!SEL)return; if(reset){seen=0; $('main').innerHTML='';}
  const d=await (await fetch('/api/culture?c='+encodeURIComponent(SEL)+'&after='+seen)).json();
  if(!d.messages.length && reset){ $('main').innerHTML='<div class="empty">(no messages yet)</div>'; return; }
  let html='', lastR=null;
  for(const m of d.messages){
    if(m.round!==lastR){ html+=`<div class="rnd">round ${m.round==null?'—':m.round}</div>`; lastR=m.round; }
    const to=m.recipient?` → ${m.recipient}`:'';
    html+=`<div class="msg"><div class="seq">#${m.seq}</div>
      <div class="snd">${m.sender}${to}</div>
      <div class="ty ${m.type}">${m.type}</div>
      <div><div class="bd">${(m.preview||'').replace(/</g,'&lt;')}</div>
      ${m.artifact?`<div class="art">▸ ${m.artifact.replace(/</g,'&lt;')}</div>`:''}</div></div>`;
    seen=Math.max(seen,m.seq);
  }
  if(reset)$('main').innerHTML=html; else $('main').insertAdjacentHTML('beforeend',html);
}
function pick(c){ SEL=c; overview(); stream(true); }
setInterval(()=>{overview(); stream(false);},1500);
overview();
</script></body></html>"""


# --------------------------------------------------------------------------- http
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def _send(self, code, body, ctype):
        b = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, default=str), "application/json; charset=utf-8")

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, HTML, "text/html; charset=utf-8")
            if u.path == "/api/overview":
                return self._json(api_overview())
            if u.path == "/api/culture":
                return self._json(api_culture(qs.get("c", [""])[0], int(qs.get("after", ["0"])[0])))
            return self._json({"error": "not found"}, 404)
        except Exception as e:
            return self._json({"error": str(e)}, 400)


def _default_db(home_arg: str | None) -> Path:
    home = home_arg or os.environ.get("HYPERCELL_HOME") or ".hypercellstate"
    return Path(home) / "_medium" / "medium.db"


def main() -> None:
    global DB_PATH
    ap = argparse.ArgumentParser(description="Live read-only viewer for the hypercell Medium (medium.db).")
    ap.add_argument("--db", help="path to medium.db (default: <home>/_medium/medium.db)")
    ap.add_argument("--home", help="HYPERCELL_HOME (default: env or .hypercellstate)")
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    DB_PATH = (Path(a.db) if a.db else _default_db(a.home)).resolve()
    if not DB_PATH.exists():
        print(f"[viewer] Medium DB not found: {DB_PATH}", file=sys.stderr)
        print("[viewer] run a tournament first, e.g.:  hc run tournament --n 6 --provider deepseek ...", file=sys.stderr)
        sys.exit(1)

    url = f"http://{a.host}:{a.port}/"
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.daemon_threads = True
    print(f"[viewer] hypercell Medium  ->  {url}")
    print(f"[viewer] db: {DB_PATH}  ({DB_PATH.stat().st_size:,} bytes, read-only)")
    print("[viewer] Ctrl+C to stop")
    if not a.no_open:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[viewer] bye")
        srv.shutdown()


if __name__ == "__main__":
    main()
