"""
SR PHYSICS — Full Suite (Production Build v4 — Final)
=====================================================

Pages
-----
    /                        Portfolio (Hero, About, RESULTS, REVIEWS, Gallery, Class, News, Paper Feedback, Community, Magic teaser)
    /magic                   Magic hub — separate interface
    /magic/sessions          Sessions from Sir (YouTube)
    /magic/from-sir          From Sir (TikTok vertical feed)
    /magic/simulations       PhET simulations
    /magic/visualizations    3D visualizations
    /admin                   P6 Crew console

Install
-------
    pip install flask
    python app.py

Password: Set in ADMIN_PASSWORD environment variable
"""
import os
import re
import json
import database as db
from collections import Counter
from flask import Flask, Response, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
if len(app.secret_key) < 32:
    raise RuntimeError("SECRET_KEY must contain at least 32 characters")
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")) or os.environ.get("APP_ENV") == "production",
)

ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
DB_PATH = "Aiven PostgreSQL"

# ============================================================
# 🔴 REPLACE WITH YOUR HOSTED LOGO URL
# ============================================================
LOGO_URL = "https://i.ibb.co/35ZLQmZd/Gemini-Generated-Image-wsrv3ywsrv3ywsrv-removebg-preview.png"

TYPE_TABLE = {
    "requests":       "join_requests",
    "comments":       "comments",
    "complaints":     "complaints",
    "doubts":         "doubts",
    "news":           "news",
    "sessions":       "sessions",
    "motivations":    "motivations",
    "papers":         "papers",
    "paper_feedback": "paper_feedback",
}


# ============================================================
# DATABASE
# ============================================================
def init_db():
    db.ensure_schema()
    with db.connect() as c:
        db.schema_lock(c)
        c.execute("""CREATE TABLE IF NOT EXISTS join_requests (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT,
            batch TEXT, location TEXT, message TEXT,
            status TEXT DEFAULT 'new', created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, batch TEXT, rating INTEGER DEFAULT 5,
            message TEXT NOT NULL, status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
            name TEXT, contact TEXT, category TEXT,
            message TEXT NOT NULL, status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS doubts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, batch TEXT, topic TEXT,
            question TEXT NOT NULL, status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL, description TEXT, image_url TEXT,
            status TEXT DEFAULT 'published', created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL, description TEXT, youtube_url TEXT NOT NULL,
            status TEXT DEFAULT 'published', created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS motivations (
            id SERIAL PRIMARY KEY,
            title TEXT, tiktok_url TEXT NOT NULL,
            status TEXT DEFAULT 'published', created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, description TEXT,
            status TEXT DEFAULT 'published', created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
        c.execute("""CREATE TABLE IF NOT EXISTS paper_feedback (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER, name TEXT, batch TEXT,
            mcq TEXT, structured TEXT, essays TEXT,
            comment TEXT, status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT to_char(CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))""")
    print("[db] ready ·", DB_PATH)


# Initialized lazily on first API request; builds and page delivery need no DB.


def extract_youtube_id(url):
    if not url: return ""
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else ""


def extract_tiktok_id(url):
    if not url: return ""
    m = re.search(r"/video/(\d+)", url)
    if m: return m.group(1)
    m = re.search(r"(\d{15,25})", url)
    return m.group(1) if m else ""


# ============================================================
# SHARED CSS
# ============================================================
BASE_CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070708;--surface:#101012;--surface-2:#151518;
  --line:rgba(245,196,81,.13);--line-soft:rgba(255,255,255,.06);
  --gold:#F5C451;--gold-bright:#FFE39B;--gold-deep:#B98A24;
  --text:#EDEAE4;--muted:#84848E;--muted-2:#5A5A63;
  --font-d:'Space Grotesk',system-ui,sans-serif;
  --font-s:'Instrument Serif',Georgia,serif;
  --font-m:'JetBrains Mono',ui-monospace,monospace;
  --sinhala:'Noto Sans Sinhala',sans-serif;
  --ease:cubic-bezier(.22,1,.36,1);
  --gut:clamp(18px,4vw,56px);
}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--font-d),var(--sinhala);font-size:16px;line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
body.lock{overflow:hidden;height:100vh}
img{max-width:100%;display:block}a{color:inherit;text-decoration:none}
button{font:inherit;color:inherit;background:none;border:none;cursor:pointer}
::selection{background:var(--gold);color:#0a0a0a}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-track{background:#0a0a0b}
::-webkit-scrollbar-thumb{background:#2a2a2e;border-radius:9px}
::-webkit-scrollbar-thumb:hover{background:var(--gold-deep)}
.grain{position:fixed;inset:0;z-index:9998;pointer-events:none;opacity:.045;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  animation:grainShift 6s steps(6) infinite}
@keyframes grainShift{0%{transform:translate(0,0)}20%{transform:translate(-4%,3%)}40%{transform:translate(3%,-4%)}60%{transform:translate(-3%,-3%)}80%{transform:translate(4%,2%)}100%{transform:translate(0,0)}}
.vignette{position:fixed;inset:0;z-index:9997;pointer-events:none;background:radial-gradient(ellipse at 50% 40%,transparent 45%,rgba(0,0,0,.55) 100%)}
.cursor,.cursor-dot{position:fixed;top:0;left:0;pointer-events:none;z-index:10000;border-radius:50%;opacity:0}
.cursor{width:34px;height:34px;border:1px solid rgba(245,196,81,.55);margin:-17px 0 0 -17px;transition:width .35s var(--ease),height .35s var(--ease),margin .35s var(--ease),background .35s var(--ease),border-color .35s var(--ease),opacity .3s}
.cursor-dot{width:5px;height:5px;background:var(--gold);margin:-2.5px 0 0 -2.5px;transition:transform .18s var(--ease),opacity .3s}
.cursor.hover{width:62px;height:62px;margin:-31px 0 0 -31px;background:rgba(245,196,81,.09);border-color:rgba(245,196,81,.85)}
.cursor-dot.hover{transform:scale(.3)}
body.pointer-on .cursor,body.pointer-on .cursor-dot{opacity:1}
@media (pointer:coarse){.cursor,.cursor-dot{display:none!important}}
/* LOADER — image only, no text, no progress bar */
#loader{position:fixed;inset:0;z-index:9999;background:#050506;display:flex;align-items:center;justify-content:center;transition:opacity .8s var(--ease),visibility .8s}
#loader.done{opacity:0;visibility:hidden}
.loader-inner{display:flex;flex-direction:column;align-items:center;gap:44px;position:relative}
.loader-logo-wrap{position:relative;width:150px;height:150px;display:grid;place-items:center}
.loader-logo-wrap::before{content:'';position:absolute;inset:-18px;border-radius:50%;border:1px solid rgba(245,196,81,.15);animation:loaderRing 3.5s linear infinite}
.loader-logo-wrap::after{content:'';position:absolute;inset:-36px;border-radius:50%;border:1px solid transparent;border-top-color:rgba(245,196,81,.5);animation:loaderRing 5s linear infinite reverse}
@keyframes loaderRing{to{transform:rotate(360deg)}}
.loader-logo{width:120px;height:120px;object-fit:contain;border-radius:26px;position:relative;z-index:2;filter:drop-shadow(0 0 26px rgba(245,196,81,.4));animation:logoPulse 2.4s ease-in-out infinite}
@keyframes logoPulse{0%,100%{transform:scale(1);filter:drop-shadow(0 0 26px rgba(245,196,81,.4))}50%{transform:scale(1.05);filter:drop-shadow(0 0 38px rgba(245,196,81,.62))}}
.progress{position:fixed;top:0;left:0;height:2px;width:0;z-index:9000;background:linear-gradient(90deg,var(--gold-deep),var(--gold),var(--gold-bright));box-shadow:0 0 12px rgba(245,196,81,.7)}
/* NAV */
.nav{position:fixed;top:0;left:0;right:0;z-index:8000;display:flex;align-items:center;justify-content:space-between;padding:0 var(--gut);height:76px;transition:background .5s var(--ease),backdrop-filter .5s,border-color .5s,height .4s var(--ease);border-bottom:1px solid transparent}
.nav.stuck{background:rgba(7,7,8,.78);backdrop-filter:blur(18px) saturate(140%);-webkit-backdrop-filter:blur(18px) saturate(140%);border-bottom-color:var(--line-soft);height:66px}
.nav-brand{display:flex;align-items:center;gap:13px;flex-shrink:0}
.brand-logo{width:42px;height:42px;border-radius:12px;object-fit:contain;background:rgba(245,196,81,.04);padding:5px;border:1px solid var(--line);transition:border-color .4s,transform .6s var(--ease)}
.nav-brand:hover .brand-logo{border-color:var(--gold);transform:rotate(-6deg) scale(1.03)}
.brand-txt{display:flex;flex-direction:column;line-height:1.15}
.brand-txt strong{font-size:13px;font-weight:600;letter-spacing:-.01em}
.brand-txt small{font-family:var(--font-m);font-size:9px;letter-spacing:.22em;color:var(--muted-2);text-transform:uppercase}
.nav-links{display:flex;gap:2px;align-items:center}
.nav-links a{position:relative;font-size:12.5px;font-weight:400;color:var(--muted);padding:8px 11px;border-radius:100px;letter-spacing:.01em;transition:color .3s,background .3s}
.nav-links a::before{content:'';position:absolute;left:11px;right:11px;bottom:4px;height:1px;background:var(--gold);transform:scaleX(0);transform-origin:right;transition:transform .45s var(--ease)}
.nav-links a:hover{color:var(--text)}
.nav-links a:hover::before{transform:scaleX(1);transform-origin:left}
.nav-links a.active{color:var(--gold)}
.nav-links a.active::before{transform:scaleX(1);transform-origin:left}
.nav-cta{font-family:var(--font-m);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;padding:11px 20px;border:1px solid var(--line);border-radius:100px;color:var(--gold);position:relative;overflow:hidden;transition:color .4s;flex-shrink:0}
.nav-cta span{position:relative;z-index:2}
.nav-cta::after{content:'';position:absolute;inset:0;background:var(--gold);transform:translateY(101%);transition:transform .5s var(--ease)}
.nav-cta:hover{color:#0a0a0a}.nav-cta:hover::after{transform:translateY(0)}
.nav-magic{font-family:var(--font-m);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;padding:11px 20px;border:1px solid rgba(245,196,81,.4);border-radius:100px;color:#0a0a0a;background:linear-gradient(100deg,var(--gold) 0%,var(--gold-bright) 50%,var(--gold) 100%);background-size:220% 100%;animation:shine 6s linear infinite;position:relative;overflow:hidden;flex-shrink:0;transition:transform .4s var(--ease),box-shadow .5s}
.nav-magic:hover{box-shadow:0 0 40px -4px rgba(245,196,81,.55);transform:translateY(-2px)}
@keyframes shine{to{background-position:-220% 0}}
.burger{display:none;width:44px;height:44px;position:relative;z-index:8100}
.burger i{position:absolute;left:11px;right:11px;height:1.5px;background:var(--text);transition:transform .4s var(--ease),opacity .3s;border-radius:2px}
.burger i:nth-child(1){top:17px}.burger i:nth-child(2){bottom:17px}
.burger.open i:nth-child(1){transform:translateY(4px) rotate(45deg)}
.burger.open i:nth-child(2){transform:translateY(-4px) rotate(-45deg)}
.mobile-menu{position:fixed;inset:0;z-index:8050;background:#060607;display:flex;flex-direction:column;justify-content:center;padding:100px var(--gut) 40px;clip-path:inset(0 0 100% 0);transition:clip-path .8s var(--ease);overflow-y:auto}
.mobile-menu.open{clip-path:inset(0 0 0 0)}
.mobile-menu a{font-size:clamp(1.5rem,6.5vw,3rem);font-weight:600;letter-spacing:-.035em;padding:clamp(7px,1.2vw,12px) 0;border-bottom:1px solid var(--line-soft);opacity:0;transform:translateY(24px);transition:opacity .6s var(--ease),transform .6s var(--ease),color .3s;display:flex;align-items:baseline;gap:12px}
.mobile-menu.open a{opacity:1;transform:translateY(0)}
.mobile-menu a:hover,.mobile-menu a:active{color:var(--gold)}
.mobile-menu a span{font-family:var(--font-m);font-size:10px;color:var(--gold);letter-spacing:.1em;flex-shrink:0}
/* SECTIONS */
.wrap{max-width:1400px;margin:0 auto;padding:0 var(--gut)}
.sec{padding:clamp(80px,12vh,150px) 0}
.sec-head{display:flex;align-items:center;gap:20px;margin-bottom:clamp(36px,5.5vh,68px)}
.sec-num{font-family:var(--font-m);font-size:10.5px;letter-spacing:.2em;color:var(--gold);border:1px solid var(--line);border-radius:100px;padding:6px 13px;flex-shrink:0;transition:background .4s,color .4s,border-color .4s}
.sec-head:hover .sec-num{background:var(--gold);color:#0a0a0a;border-color:var(--gold)}
.sec-label{font-family:var(--font-m);font-size:10.5px;letter-spacing:.32em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.sec-rule{flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent);position:relative;overflow:hidden}
.sec-rule::after{content:'';position:absolute;top:0;left:-30%;width:30%;height:100%;background:linear-gradient(90deg,transparent,var(--gold),transparent);animation:ruleRun 4.5s cubic-bezier(.65,0,.35,1) infinite}
@keyframes ruleRun{0%{left:-30%}55%{left:100%}100%{left:100%}}
.sec-title{font-size:clamp(2rem,4.4vw,3.8rem);font-weight:600;line-height:1.02;letter-spacing:-.04em;margin-bottom:22px;background:linear-gradient(110deg,var(--text) 0%,var(--text) 40%,var(--gold-bright) 50%,var(--text) 60%,var(--text) 100%);background-size:250% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:titleShine 8s linear infinite}
@keyframes titleShine{to{background-position:-250% 0}}
.sec-title em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.sec-lead{font-size:clamp(.95rem,1.25vw,1.06rem);color:var(--muted);max-width:56ch;font-weight:300}
[data-reveal]{opacity:0;transform:translateY(34px);transition:opacity .95s var(--ease),transform .95s var(--ease)}
[data-reveal].in{opacity:1;transform:none}
/* BUTTONS */
.btn{position:relative;display:inline-flex;align-items:center;gap:11px;padding:16px 30px;border-radius:100px;font-size:13.5px;font-weight:500;letter-spacing:.01em;overflow:hidden;transition:color .4s var(--ease),border-color .4s;will-change:transform}
.btn svg{width:15px;height:15px;transition:transform .5s var(--ease)}
.btn:hover svg{transform:translateX(5px)}
.btn-gold{background:linear-gradient(100deg,var(--gold) 0%,var(--gold-bright) 50%,var(--gold) 100%);background-size:220% 100%;color:#0a0a0a;animation:shine 6s linear infinite;box-shadow:0 0 0 0 rgba(245,196,81,.4);transition:box-shadow .5s,transform .4s var(--ease)}
.btn-gold:hover{box-shadow:0 10px 40px -8px rgba(245,196,81,.55)}
.btn-ghost{border:1px solid var(--line);color:var(--text)}
.btn-ghost::after{content:'';position:absolute;inset:0;background:rgba(245,196,81,.1);transform:scaleX(0);transform-origin:right;transition:transform .55s var(--ease);z-index:0}
.btn-ghost:hover{border-color:rgba(245,196,81,.5)}.btn-ghost:hover::after{transform:scaleX(1);transform-origin:left}
.btn span,.btn svg{position:relative;z-index:2}
/* PAGE HERO */
.page-hero{position:relative;padding:160px 0 60px;overflow:hidden;border-bottom:1px solid var(--line-soft)}
.page-hero::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 20% 20%,rgba(245,196,81,.09),transparent 55%),radial-gradient(ellipse at 80% 80%,rgba(245,196,81,.05),transparent 55%);pointer-events:none}
.page-hero-inner{position:relative;z-index:2;max-width:1400px;margin:0 auto;padding:0 var(--gut)}
.page-hero .eyebrow{display:inline-flex;align-items:center;gap:11px;font-family:var(--font-m);font-size:10px;letter-spacing:.3em;text-transform:uppercase;color:var(--muted);margin-bottom:24px;border:1px solid var(--line-soft);border-radius:100px;padding:8px 16px 8px 12px;background:rgba(255,255,255,.015)}
.page-hero .eyebrow .pulse{width:6px;height:6px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 0 rgba(245,196,81,.7);animation:pulse 2.2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(245,196,81,.6)}70%{box-shadow:0 0 0 11px rgba(245,196,81,0)}100%{box-shadow:0 0 0 0 rgba(245,196,81,0)}}
.page-hero h1{font-size:clamp(2.4rem,6vw,5.4rem);font-weight:600;line-height:.95;letter-spacing:-.045em;margin-bottom:22px}
.page-hero h1 em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.page-hero p{font-size:clamp(1rem,1.4vw,1.14rem);color:var(--muted);max-width:60ch;font-weight:300}
.page-hero .crumb{font-family:var(--font-m);font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2);margin-top:28px}
.page-hero .crumb a{color:var(--gold)}
.page-hero .crumb a:hover{text-decoration:underline}
/* TOAST */
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(120%);z-index:9990;background:rgba(10,10,12,.95);border:1px solid var(--line);border-radius:100px;padding:14px 24px;font-family:var(--font-m);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--text);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);transition:transform .6s var(--ease);display:flex;align-items:center;gap:12px;max-width:calc(100vw - 40px)}
.toast.on{transform:translateX(-50%) translateY(0)}
.toast .dot{width:6px;height:6px;border-radius:50%;background:var(--gold);flex-shrink:0}
.toast.err{border-color:rgba(255,90,90,.4)}.toast.err .dot{background:#ff5a5a}
/* FOOTER */
.footer{border-top:1px solid var(--line);margin-top:clamp(60px,9vh,110px);padding:clamp(50px,7vh,80px) 0 34px;position:relative;overflow:hidden}
.footer::before{content:'';position:absolute;top:-1px;left:50%;transform:translateX(-50%);width:min(600px,80%);height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
.f-top{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:44px;margin-bottom:56px}
.f-brand h4{font-size:clamp(1.5rem,2.8vw,2.2rem);font-weight:600;letter-spacing:-.04em;line-height:1.05;margin-bottom:14px}
.f-brand h4 em{font-family:var(--font-s);font-style:italic;font-weight:400;color:var(--gold)}
.f-brand p{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);max-width:34ch;line-height:2}
.f-col h5{font-family:var(--font-m);font-size:9.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2);margin-bottom:20px}
.f-col a{display:block;font-size:13.5px;color:var(--muted);padding:6px 0;transition:color .3s,transform .4s var(--ease)}
.f-col a:hover{color:var(--gold);transform:translateX(6px)}
.f-bot{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;padding-top:26px;border-top:1px solid var(--line-soft);font-family:var(--font-m);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted-2)}
.f-bot b{color:var(--gold);font-weight:400}
.f-top-btn{width:44px;height:44px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;transition:background .4s,border-color .4s,transform .4s var(--ease)}
.f-top-btn svg{width:14px;height:14px;stroke:var(--gold);transition:stroke .4s}
.f-top-btn:hover{background:var(--gold);border-color:var(--gold);transform:translateY(-4px)}
.f-top-btn:hover svg{stroke:#0a0a0a}
/* FORM */
.form{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.field{position:relative}
.field.full{grid-column:1/-1}
.field label{display:block;font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:9px;transition:color .3s}
.field:focus-within label{color:var(--gold)}
.field input,.field select,.field textarea{width:100%;background:rgba(255,255,255,.015);border:1px solid var(--line-soft);border-radius:6px;padding:15px 18px;color:var(--text);font-family:var(--font-d),var(--sinhala);font-size:14px;font-weight:300;letter-spacing:.01em;transition:border-color .4s,background .4s,box-shadow .4s;outline:none;appearance:none;-webkit-appearance:none}
.field select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23F5C451' fill='none' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 18px center;padding-right:42px;cursor:pointer}
.field select option{background:#0e0e10;color:var(--text)}
.field textarea{min-height:120px;resize:vertical;line-height:1.6}
.field input:focus,.field select:focus,.field textarea:focus{border-color:rgba(245,196,81,.55);background:rgba(245,196,81,.02);box-shadow:0 0 0 3px rgba(245,196,81,.08)}
.field input::placeholder,.field textarea::placeholder{color:var(--muted-2)}
.submit-row{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;gap:20px;margin-top:8px;flex-wrap:wrap}
.submit-note{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);line-height:1.9}
.submit-note b{color:var(--gold);font-weight:400}
.submit-btn{position:relative;display:inline-flex;align-items:center;gap:11px;padding:16px 34px;border-radius:100px;font-size:13.5px;font-weight:500;letter-spacing:.02em;background:linear-gradient(100deg,var(--gold) 0%,var(--gold-bright) 50%,var(--gold) 100%);background-size:220% 100%;color:#0a0a0a;animation:shine 6s linear infinite;box-shadow:0 0 0 0 rgba(245,196,81,.4);transition:box-shadow .5s,transform .4s var(--ease);overflow:hidden}
.submit-btn:hover{box-shadow:0 12px 44px -10px rgba(245,196,81,.55)}
.submit-btn svg{width:15px;height:15px;transition:transform .5s var(--ease)}
.submit-btn:hover svg{transform:translateX(5px)}
.submit-btn:disabled{opacity:.6;cursor:wait}
/* MODAL */
.modal{position:fixed;inset:0;z-index:9500;background:rgba(5,5,6,.92);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:center;padding:clamp(12px,3vw,40px);opacity:0;visibility:hidden;transition:opacity .5s var(--ease),visibility .5s}
.modal.open{opacity:1;visibility:visible}
.modal-inner{width:100%;max-width:1200px;height:min(88vh,860px);background:#0A0A0C;border:1px solid var(--line);border-radius:8px;overflow:hidden;display:flex;flex-direction:column;transform:scale(.96) translateY(16px);transition:transform .6s var(--ease);box-shadow:0 40px 120px -30px rgba(0,0,0,.9)}
.modal.open .modal-inner{transform:scale(1) translateY(0)}
.modal-bar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 18px;border-bottom:1px solid var(--line-soft);flex-shrink:0;background:rgba(0,0,0,.35)}
.modal-title{font-family:var(--font-m);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);display:flex;align-items:center;gap:10px;min-width:0}
.modal-title span{color:var(--muted-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.modal-actions{display:flex;gap:8px;flex-shrink:0}
.modal-btn{width:40px;height:40px;border:1px solid var(--line-soft);border-radius:50%;display:grid;place-items:center;color:var(--muted);transition:background .35s,color .35s,border-color .35s,transform .4s var(--ease)}
.modal-btn svg{width:14px;height:14px}
.modal-btn:hover{background:var(--gold);color:#0a0a0a;border-color:var(--gold);transform:scale(1.06)}
.modal-frame{flex:1;position:relative;background:#000}
.modal-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#000}
.modal-loading{position:absolute;inset:0;display:grid;place-items:center;background:#0A0A0C;font-family:var(--font-m);font-size:10px;letter-spacing:.3em;text-transform:uppercase;color:var(--muted-2);gap:16px;z-index:2}
.modal-loading.hide{display:none}
.modal-spin{width:34px;height:34px;border:1px solid rgba(245,196,81,.2);border-top-color:var(--gold);border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:80px 20px;border:1px dashed var(--line-soft);border-radius:8px;max-width:640px;margin:0 auto}
.empty svg{width:52px;height:52px;stroke:var(--muted-2);margin:0 auto 20px;display:block;opacity:.5}
.empty h3{font-size:1.1rem;font-weight:600;letter-spacing:-.02em;margin-bottom:8px}
.empty p{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);line-height:1.9}
@media(max-width:1080px){
  .nav-links{display:none}.nav-cta{display:none}.nav-magic{display:none}.burger{display:block}
  .f-top{grid-template-columns:1fr 1fr}.f-brand{grid-column:1/-1}
  .form{grid-template-columns:1fr}
}
@media(max-width:640px){
  :root{--gut:18px}
  .sec{padding:clamp(60px,10vh,100px) 0}
  .sec-title{font-size:clamp(1.7rem,8vw,2.4rem)}
  .page-hero{padding:120px 0 40px}
  .page-hero h1{font-size:clamp(2rem,10vw,3rem)}
  .f-top{grid-template-columns:1fr;gap:34px}
  .f-bot{flex-direction:column;align-items:flex-start;gap:18px}
  .submit-row{flex-direction:column;align-items:stretch}
  .submit-btn{width:100%;justify-content:center;padding:16px 24px}
  .submit-note{text-align:center}
  .field input,.field select,.field textarea{padding:14px 16px;font-size:14px}
  .modal{padding:0}.modal-inner{height:100%;max-height:100%;border-radius:0;border:0}
  .brand-logo{width:38px;height:38px}
  .loader-logo{width:100px;height:100px}
  .loader-logo-wrap{width:130px;height:130px}
}
@media(prefers-reduced-motion:reduce){
  *{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
  html{scroll-behavior:auto}
}
"""


# ============================================================
# SHARED JS (with robust reveal scanner)
# ============================================================
BASE_JS = r"""
(function(){
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* LOADER — image only, no progress bar */
  var loader = document.getElementById('loader');
  if(loader){
    var DUR = reduced ? 500 : 1900;
    setTimeout(function(){
      loader.classList.add('done');
      document.body.classList.add('loaded');
      setTimeout(function(){ loader.style.display = 'none'; }, 800);
    }, DUR);
  }

  /* NAV */
  var nav = document.getElementById('nav');
  var progress = document.getElementById('progress');
  function onScroll(){
    var y = window.scrollY;
    if(nav) nav.classList.toggle('stuck', y > 40);
    if(progress){
      var h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* MOBILE MENU */
  var burger = document.getElementById('burger');
  var menu = document.getElementById('mobileMenu');
  if(burger && menu){
    burger.addEventListener('click', function(){
      var open = menu.classList.toggle('open');
      burger.classList.toggle('open', open);
      document.body.classList.toggle('lock', open);
      var links = menu.querySelectorAll('a');
      for(var i = 0; i < links.length; i++){
        links[i].style.transitionDelay = open ? (0.12 + i * 0.05) + 's' : '0s';
      }
    });
    menu.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){
        menu.classList.remove('open');
        burger.classList.remove('open');
        document.body.classList.remove('lock');
      });
    });
  }

  /* REVEAL SCANNER — robust, exposed globally */
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  function scanReveal(root){
    var scope = root || document;
    var els = scope.querySelectorAll('[data-reveal]:not([data-observed])');
    els.forEach(function(el){
      el.setAttribute('data-observed', '1');
      io.observe(el);
    });
  }
  window.__scanReveal = scanReveal;
  scanReveal();

  /* Safety net — every 1.5s, force any in-viewport [data-reveal] visible */
  setInterval(function(){
    document.querySelectorAll('[data-reveal]:not(.in)').forEach(function(el){
      var r = el.getBoundingClientRect();
      if(r.top < window.innerHeight - 40 && r.bottom > 0){
        el.classList.add('in');
      }
    });
  }, 1500);
  /* And one hard fallback after 2.5s in case observer never fired */
  setTimeout(function(){
    document.querySelectorAll('[data-reveal]:not(.in)').forEach(function(el){
      var r = el.getBoundingClientRect();
      if(r.top < window.innerHeight + 200){
        el.classList.add('in');
      }
    });
  }, 2500);

  /* COUNTERS */
  var cio = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      var el = e.target;
      var target = parseFloat(el.dataset.count);
      var suffix = el.dataset.suffix || '';
      var dur = 1700, s = null;
      function tick(ts){
        if(!s) s = ts;
        var t = Math.min((ts - s) / dur, 1);
        var eased = 1 - Math.pow(1 - t, 4);
        el.textContent = Math.round(target * eased).toLocaleString() + suffix;
        if(t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
      cio.unobserve(el);
    });
  }, { threshold: 0.4 });
  document.querySelectorAll('[data-count]').forEach(function(c){ cio.observe(c); });

  /* CURSOR */
  var fine = window.matchMedia('(pointer:fine)').matches;
  if(fine && !reduced){
    document.body.classList.add('pointer-on');
    var cur = document.querySelector('.cursor');
    var dot = document.querySelector('.cursor-dot');
    if(cur && dot){
      var mx = innerWidth/2, my = innerHeight/2, cx = mx, cy = my;
      window.addEventListener('mousemove', function(e){
        mx = e.clientX; my = e.clientY;
        dot.style.transform = 'translate(' + mx + 'px,' + my + 'px)';
      });
      (function loop(){
        cx += (mx - cx) * 0.16; cy += (my - cy) * 0.16;
        cur.style.transform = 'translate(' + cx + 'px,' + cy + 'px)';
        requestAnimationFrame(loop);
      })();
      document.querySelectorAll('a, button, [data-cursor]').forEach(function(el){
        el.addEventListener('mouseenter', function(){ cur.classList.add('hover'); dot.classList.add('hover'); });
        el.addEventListener('mouseleave', function(){ cur.classList.remove('hover'); dot.classList.remove('hover'); });
      });
    }
  }

  /* MAGNETIC */
  if(fine && !reduced){
    document.querySelectorAll('.btn, .submit-btn, .nav-cta, .nav-magic, .rnav').forEach(function(el){
      el.addEventListener('mousemove', function(e){
        var r = el.getBoundingClientRect();
        var x = e.clientX - r.left - r.width/2;
        var y = e.clientY - r.top - r.height/2;
        el.style.transform = 'translate(' + (x*0.14) + 'px,' + (y*0.24) + 'px)';
      });
      el.addEventListener('mouseleave', function(){ el.style.transform = ''; });
    });
  }

  /* TOAST */
  window.__toast = function(msg, isErr){
    var t = document.getElementById('toast');
    var m = document.getElementById('toastMsg');
    if(!t || !m) return;
    m.textContent = msg;
    t.classList.toggle('err', !!isErr);
    t.classList.add('on');
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(function(){ t.classList.remove('on'); }, 3200);
  };

  /* MODAL */
  window.__openModal = function(name, url){
    var m = document.getElementById('videoModal');
    if(!m) return;
    document.getElementById('modalName').textContent = name || '';
    document.getElementById('modalFrame').src = url;
    document.getElementById('modalNew').href = url;
    document.getElementById('modalLoading').classList.remove('hide');
    m.classList.add('open');
    document.body.classList.add('lock');
    setTimeout(function(){ document.getElementById('modalLoading').classList.add('hide'); }, 1600);
  };
  window.__closeModal = function(){
    var m = document.getElementById('videoModal');
    if(!m) return;
    m.classList.remove('open');
    document.body.classList.remove('lock');
    setTimeout(function(){ document.getElementById('modalFrame').src = 'about:blank'; }, 400);
  };
  var mClose = document.getElementById('modalClose');
  if(mClose) mClose.addEventListener('click', window.__closeModal);
  var mEl = document.getElementById('videoModal');
  if(mEl){
    mEl.addEventListener('click', function(e){ if(e.target === mEl) window.__closeModal(); });
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape' && mEl.classList.contains('open')) window.__closeModal();
    });
  }

  /* MARQUEE */
  var mq = document.getElementById('marqueeTrack');
  if(mq) mq.innerHTML += mq.innerHTML;
})();
"""


# ============================================================
# HTML FRAGMENTS
# ============================================================
LOADER_HTML = """
<div id="loader">
  <div class="loader-inner">
    <div class="loader-logo-wrap">
      <img class="loader-logo" src="__LOGO__" alt="SR Physics">
    </div>
  </div>
</div>
"""

FOOTER_HTML = """
<footer class="footer">
  <div class="wrap">
    <div class="f-top">
      <div class="f-brand">
        <h4>Shamil Rathnayaka <em>|</em> Physics</h4>
        <p>Results oriented · Next gen physics · Island wide</p>
      </div>
      <div class="f-col">
        <h5>Portfolio</h5>
        <a href="/">Home</a>
        <a href="/#about">About</a>
        <a href="/#results">Results</a>
        <a href="/#reviews">Reviews</a>
      </div>
      <div class="f-col">
        <h5>✦ Magic</h5>
        <a href="/magic/sessions">Sessions</a>
        <a href="/magic/from-sir">From Sir</a>
        <a href="/magic/simulations">Simulations</a>
        <a href="/magic/visualizations">Visualizations</a>
      </div>
      <div class="f-col">
        <h5>Community</h5>
        <a href="/#news">News</a>
        <a href="/#join">Join Class</a>
        <a href="/#join">Leave a Comment</a>
        <a href="/#join">Ask a Doubt</a>
      </div>
    </div>
    <div class="f-bot">
      <span>© 2026 · Designed &amp; Developed by <b>P6 CREW</b></span>
      <a href="#top" class="f-top-btn" aria-label="Back to top" data-cursor>
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 19V5M6 11l6-6 6 6"/></svg>
      </a>
    </div>
  </div>
</footer>

<div class="modal" id="videoModal" role="dialog" aria-modal="true">
  <div class="modal-inner">
    <div class="modal-bar">
      <div class="modal-title"><span>Playing</span><span id="modalName">—</span></div>
      <div class="modal-actions">
        <a href="#" id="modalNew" class="modal-btn" target="_blank" rel="noopener" title="Open in new tab" data-cursor>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6M10 14 21 3"/></svg>
        </a>
        <button class="modal-btn" id="modalClose" data-cursor>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
    </div>
    <div class="modal-frame">
      <div class="modal-loading" id="modalLoading"><div class="modal-spin"></div><div>Loading</div></div>
      <iframe id="modalFrame" title="Video" allowfullscreen allow="fullscreen; clipboard-write; encrypted-media; picture-in-picture"></iframe>
    </div>
  </div>
</div>
"""


def build_nav(active=""):
    def c(n): return ' class="active"' if active == n else ""
    return """
<header class="nav" id="nav">
  <a href="/" class="nav-brand" data-cursor>
    <img class="brand-logo" src="__LOGO__" alt="">
    <span class="brand-txt"><strong>Shamil Rathnayake</strong><small>Physics · A/L</small></span>
  </a>
  <nav class="nav-links">
    <a href="/" data-cursor""" + c("home") + """>Home</a>
    <a href="/#about" data-cursor>About</a>
    <a href="/#results" data-cursor>Results</a>
    <a href="/#reviews" data-cursor>Reviews</a>
    <a href="/#news" data-cursor>News</a>
    <a href="/#join" data-cursor>Community</a>
  </nav>
  <a href="/magic" class="nav-magic" data-cursor>✦ Magic</a>
  <button class="burger" id="burger" aria-label="Menu"><i></i><i></i></button>
</header>

<div class="mobile-menu" id="mobileMenu">
  <a href="/"><span>01</span>Home</a>
  <a href="/#about"><span>02</span>About</a>
  <a href="/#results"><span>03</span>Results</a>
  <a href="/#reviews"><span>04</span>Reviews</a>
  <a href="/#news"><span>05</span>News</a>
  <a href="/#join"><span>06</span>Community</a>
  <a href="/magic"><span>✦</span>Magic</a>
</div>
"""


def page_shell(title, body, page_css="", page_js="", active=""):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>""" + title + """</title>
<meta name="theme-color" content="#070708">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500&family=Noto+Sans+Sinhala:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>""" + BASE_CSS + page_css + """</style>
</head>
<body id="top">
<div class="grain"></div>
<div class="vignette"></div>
<div class="cursor"></div>
<div class="cursor-dot"></div>
<div class="progress" id="progress"></div>
""" + LOADER_HTML + build_nav(active) + """
<main>""" + body + """</main>
""" + FOOTER_HTML + """
<div class="toast" id="toast"><span class="dot"></span><span id="toastMsg">Message</span></div>
<script>""" + BASE_JS + """</script>
<script>""" + page_js + """</script>
</body>
</html>"""
    return html.replace("__LOGO__", LOGO_URL)


# ============================================================
# MAGIC SHELL
# ============================================================
MAGIC_EXTRA_CSS = r"""
.magic-nav{position:fixed;top:0;left:0;right:0;z-index:8000;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:0 clamp(16px,3vw,40px);height:72px;background:rgba(5,5,7,.72);backdrop-filter:blur(22px) saturate(160%);-webkit-backdrop-filter:blur(22px) saturate(160%);border-bottom:1px solid rgba(245,196,81,.16);transition:height .4s var(--ease)}
.magic-nav .magic-brand{display:flex;align-items:center;gap:12px;flex-shrink:0}
.magic-nav .magic-brand img{width:40px;height:40px;border-radius:11px;object-fit:contain;background:rgba(245,196,81,.06);padding:4px;border:1px solid rgba(245,196,81,.3);transition:transform .5s var(--ease),border-color .4s}
.magic-nav .magic-brand:hover img{transform:rotate(-6deg) scale(1.04);border-color:var(--gold)}
.magic-nav .magic-brand span{font-family:var(--font-d);font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;line-height:1.1}
.magic-nav .magic-brand span b{display:block;color:var(--gold);font-size:14px;font-weight:700;letter-spacing:.18em}
.magic-links{display:flex;gap:4px;align-items:center;flex:1;justify-content:center}
.magic-links a{position:relative;font-family:var(--font-m);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);padding:10px 15px;border-radius:100px;transition:color .3s,background .3s}
.magic-links a::before{content:'';position:absolute;inset:0;border-radius:100px;background:linear-gradient(120deg,rgba(245,196,81,.08),transparent);opacity:0;transition:opacity .4s}
.magic-links a:hover{color:var(--text)}
.magic-links a:hover::before{opacity:1}
.magic-links a.active{color:var(--gold)}
.magic-links a.active::before{opacity:1;border:1px solid rgba(245,196,81,.35)}
.magic-back{font-family:var(--font-m);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);padding:10px 18px;border:1px solid var(--line-soft);border-radius:100px;transition:color .4s,border-color .4s,background .4s;flex-shrink:0;display:flex;align-items:center;gap:8px}
.magic-back:hover{color:var(--gold);border-color:var(--line);background:rgba(245,196,81,.04)}
.magic-mobile-burger{display:none;width:44px;height:44px;position:relative;z-index:8100}
.magic-mobile-burger i{position:absolute;left:11px;right:11px;height:1.5px;background:var(--text);transition:transform .4s var(--ease);border-radius:2px}
.magic-mobile-burger i:nth-child(1){top:17px}
.magic-mobile-burger i:nth-child(2){bottom:17px}
.magic-mobile-burger.open i:nth-child(1){transform:translateY(4px) rotate(45deg)}
.magic-mobile-burger.open i:nth-child(2){transform:translateY(-4px) rotate(-45deg)}
.magic-mobile-menu{position:fixed;inset:0;z-index:8050;background:#050506;display:flex;flex-direction:column;justify-content:center;padding:100px var(--gut) 40px;clip-path:inset(0 0 100% 0);transition:clip-path .8s var(--ease);overflow-y:auto}
.magic-mobile-menu.open{clip-path:inset(0 0 0 0)}
.magic-mobile-menu a{font-size:clamp(1.4rem,6vw,2.4rem);font-weight:600;letter-spacing:-.03em;padding:12px 0;border-bottom:1px solid var(--line-soft);opacity:0;transform:translateY(20px);transition:opacity .5s var(--ease),transform .5s var(--ease),color .3s;display:flex;align-items:center;gap:14px}
.magic-mobile-menu.open a{opacity:1;transform:translateY(0)}
.magic-mobile-menu a:hover{color:var(--gold)}
.magic-mobile-menu a span{font-family:var(--font-m);font-size:10px;color:var(--gold);letter-spacing:.1em;flex-shrink:0;width:24px}
.magic-mobile-menu a.active{color:var(--gold)}
.magic-hero{position:relative;padding:150px 0 70px;overflow:hidden;border-bottom:1px solid var(--line-soft);background:radial-gradient(ellipse at 20% 20%,rgba(245,196,81,.09),transparent 55%),radial-gradient(ellipse at 80% 80%,rgba(245,196,81,.05),transparent 55%)}
.magic-hero-inner{position:relative;z-index:2;max-width:1400px;margin:0 auto;padding:0 var(--gut)}
.magic-hero .kicker{font-family:var(--font-m);font-size:10px;letter-spacing:.4em;text-transform:uppercase;color:var(--gold);margin-bottom:24px;display:inline-flex;align-items:center;gap:11px}
.magic-hero .kicker::before{content:'';width:36px;height:1px;background:var(--gold)}
.magic-hero h1{font-size:clamp(2.6rem,7vw,6rem);font-weight:600;line-height:.94;letter-spacing:-.05em;margin-bottom:24px}
.magic-hero h1 em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep) 0%,var(--gold-bright) 50%,var(--gold-deep) 100%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 5s linear infinite}
.magic-hero p{font-size:clamp(1rem,1.5vw,1.18rem);color:var(--muted);max-width:62ch;font-weight:300}
.magic-footer{border-top:1px solid var(--line);margin-top:clamp(60px,9vh,110px);padding:36px 0}
.magic-footer-inner{max-width:1400px;margin:0 auto;padding:0 var(--gut);display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap;font-family:var(--font-m);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted-2)}
.magic-footer-inner b{color:var(--gold);font-weight:400}
.magic-footer-links{display:flex;gap:22px;flex-wrap:wrap}
.magic-footer-links a{color:var(--muted);transition:color .3s}
.magic-footer-links a:hover{color:var(--gold)}
@media(max-width:1080px){
  .magic-links{display:none}
  .magic-back{display:none}
  .magic-mobile-burger{display:block}
}
@media(max-width:640px){
  .magic-nav{height:64px}
  .magic-nav .magic-brand img{width:36px;height:36px}
  .magic-nav .magic-brand span{font-size:11px}
  .magic-nav .magic-brand span b{font-size:12px}
  .magic-hero{padding:110px 0 50px}
  .magic-footer-inner{flex-direction:column;align-items:flex-start;text-align:left}
}
"""


def magic_shell(title, body, active="magic", page_css="", page_js=""):
    def c(n): return ' class="active"' if active == n else ""
    nav = """
<header class="magic-nav" id="magicNav">
  <a href="/magic" class="magic-brand" data-cursor>
    <img src="__LOGO__" alt="">
    <span><b>SR</b>MAGIC</span>
  </a>
  <nav class="magic-links">
    <a href="/magic/sessions" data-cursor""" + c("sessions") + """>Sessions</a>
    <a href="/magic/from-sir" data-cursor""" + c("from-sir") + """>From Sir</a>
    <a href="/magic/simulations" data-cursor""" + c("simulations") + """>Simulations</a>
    <a href="/magic/visualizations" data-cursor""" + c("visualizations") + """>Visualizations</a>
  </nav>
  <a href="/" class="magic-back" data-cursor>← Portfolio</a>
  <button class="magic-mobile-burger" id="magicBurger" aria-label="Menu"><i></i><i></i></button>
</header>

<div class="magic-mobile-menu" id="magicMobileMenu">
  <a href="/magic"><span>01</span>Magic Home</a>
  <a href="/magic/sessions"><span>02</span>Sessions</a>
  <a href="/magic/from-sir"><span>03</span>From Sir</a>
  <a href="/magic/simulations"><span>04</span>Simulations</a>
  <a href="/magic/visualizations"><span>05</span>Visualizations</a>
  <a href="/"><span>←</span>Back to Portfolio</a>
</div>
"""
    magic_js = r"""
(function(){
  var burger = document.getElementById('magicBurger');
  var menu = document.getElementById('magicMobileMenu');
  if(burger && menu){
    burger.addEventListener('click', function(){
      var open = menu.classList.toggle('open');
      burger.classList.toggle('open', open);
      document.body.classList.toggle('lock', open);
      var links = menu.querySelectorAll('a');
      for(var i = 0; i < links.length; i++){
        links[i].style.transitionDelay = open ? (0.1 + i * 0.05) + 's' : '0s';
      }
    });
    menu.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){
        menu.classList.remove('open');
        burger.classList.remove('open');
        document.body.classList.remove('lock');
      });
    });
  }
})();
"""
    footer = """
<footer class="magic-footer">
  <div class="magic-footer-inner">
    <span>© 2026 · <b>SR MAGIC</b> · A separate world by P6 CREW</span>
    <div class="magic-footer-links">
      <a href="/magic/sessions">Sessions</a>
      <a href="/magic/from-sir">From Sir</a>
      <a href="/magic/simulations">Simulations</a>
      <a href="/magic/visualizations">Visualizations</a>
      <a href="/">← Portfolio</a>
    </div>
  </div>
</footer>

<div class="modal" id="videoModal" role="dialog" aria-modal="true">
  <div class="modal-inner">
    <div class="modal-bar">
      <div class="modal-title"><span>Playing</span><span id="modalName">—</span></div>
      <div class="modal-actions">
        <a href="#" id="modalNew" class="modal-btn" target="_blank" rel="noopener" title="Open in new tab" data-cursor>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6M10 14 21 3"/></svg>
        </a>
        <button class="modal-btn" id="modalClose" data-cursor>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
    </div>
    <div class="modal-frame">
      <div class="modal-loading" id="modalLoading"><div class="modal-spin"></div><div>Loading</div></div>
      <iframe id="modalFrame" title="Video" allowfullscreen allow="fullscreen; clipboard-write; encrypted-media; picture-in-picture"></iframe>
    </div>
  </div>
</div>
"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>""" + title + """</title>
<meta name="theme-color" content="#050506">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500&family=Noto+Sans+Sinhala:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>""" + BASE_CSS + MAGIC_EXTRA_CSS + page_css + """</style>
</head>
<body id="top" class="magic-body">
<div class="grain"></div>
<div class="vignette"></div>
<div class="cursor"></div>
<div class="cursor-dot"></div>
<div class="progress" id="progress"></div>
""" + LOADER_HTML + nav + """
<main>""" + body + """</main>
""" + footer + """
<div class="toast" id="toast"><span class="dot"></span><span id="toastMsg">Message</span></div>
<script>""" + BASE_JS + magic_js + """</script>
<script>""" + page_js + """</script>
</body>
</html>"""
    return html.replace("__LOGO__", LOGO_URL)

# ============================================================
# PORTFOLIO PAGE CSS
# ============================================================
PORTFOLIO_CSS = r"""
.hero{position:relative;min-height:100svh;display:flex;flex-direction:column;justify-content:center;padding:150px 0 40px;overflow:hidden}
#hero-canvas{position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none}
.hero-grid-bg{position:absolute;inset:0;z-index:0;pointer-events:none;opacity:.5;background-image:linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);background-size:88px 88px;mask-image:radial-gradient(ellipse 90% 70% at 50% 45%,#000 20%,transparent 78%);-webkit-mask-image:radial-gradient(ellipse 90% 70% at 50% 45%,#000 20%,transparent 78%)}
.hero-inner{position:relative;z-index:3;width:100%;max-width:1400px;margin:0 auto;padding:0 var(--gut);display:grid;grid-template-columns:1.22fr .78fr;gap:48px;align-items:center}
.eyebrow{display:inline-flex;align-items:center;gap:11px;font-family:var(--font-m);font-size:10px;letter-spacing:.3em;text-transform:uppercase;color:var(--muted);margin-bottom:30px;border:1px solid var(--line-soft);border-radius:100px;padding:8px 16px 8px 12px;background:rgba(255,255,255,.015)}
.eyebrow .pulse{width:6px;height:6px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 0 rgba(245,196,81,.7);animation:pulse 2.2s infinite}
.hero-title{font-size:clamp(2.9rem,7.4vw,7.4rem);font-weight:600;line-height:.9;letter-spacing:-.045em;margin-bottom:26px}
.hero-title .ln{display:block;overflow:hidden}
.hero-title .ln > span{display:block;transform:translateY(105%);transition:transform 1.15s var(--ease)}
body.loaded .hero-title .ln > span{transform:translateY(0)}
body.loaded .hero-title .ln:nth-child(2) > span{transition-delay:.11s}
.hero-title .accent{font-family:var(--font-s);font-style:italic;font-weight:400;letter-spacing:-.02em;background:linear-gradient(100deg,var(--gold-deep) 0%,var(--gold) 30%,var(--gold-bright) 50%,var(--gold) 70%,var(--gold-deep) 100%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 5.5s linear infinite}
.hero-sub{font-size:clamp(1rem,1.5vw,1.18rem);color:var(--muted);max-width:44ch;margin-bottom:22px;font-weight:300}
.hero-sub em{font-family:var(--font-s);font-style:italic;font-size:1.14em;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4s linear infinite}
.hero-hash{font-family:var(--font-m);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);margin-bottom:38px}
.hero-hash b{color:var(--gold);font-weight:400}
.hero-cta{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.hero-side{display:flex;flex-direction:column;gap:0;position:relative}
.side-label{font-family:var(--font-m);font-size:9.5px;letter-spacing:.32em;text-transform:uppercase;color:var(--muted-2);margin-bottom:18px;display:flex;align-items:center;gap:12px}
.side-label::after{content:'';flex:1;height:1px;background:var(--line-soft)}
.loc{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0;border-bottom:1px solid var(--line-soft);position:relative;overflow:hidden;cursor:default;opacity:0;transform:translateX(28px);transition:opacity .8s var(--ease),transform .8s var(--ease)}
body.loaded .loc{opacity:1;transform:translateX(0)}
body.loaded .loc:nth-child(2){transition-delay:.5s}
body.loaded .loc:nth-child(3){transition-delay:.6s}
body.loaded .loc:nth-child(4){transition-delay:.7s}
body.loaded .loc:nth-child(5){transition-delay:.8s}
.loc::before{content:'';position:absolute;left:0;bottom:-1px;height:1px;width:100%;background:linear-gradient(90deg,var(--gold),transparent);transform:scaleX(0);transform-origin:left;transition:transform .7s var(--ease)}
.loc:hover::before{transform:scaleX(1)}
.loc-name{font-size:15.5px;font-weight:500;letter-spacing:-.01em;transition:color .3s,transform .5s var(--ease)}
.loc:hover .loc-name{color:var(--gold);transform:translateX(6px)}
.loc-place{font-family:var(--font-m);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted-2)}
.loc.live .loc-place{color:#ff5a5a;display:flex;align-items:center;gap:7px}
.loc.live .loc-place::before{content:'';width:6px;height:6px;border-radius:50%;background:#ff3b3b;box-shadow:0 0 9px #ff3b3b;animation:pulse 1.6s infinite}
.hero-foot{position:relative;z-index:3;max-width:1400px;margin:56px auto 0;padding:0 var(--gut);display:flex;justify-content:space-between;align-items:flex-end;gap:24px}
.scroll-cue{display:flex;align-items:center;gap:13px;font-family:var(--font-m);font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--muted-2)}
.scroll-line{width:1px;height:44px;background:linear-gradient(180deg,var(--gold),transparent);position:relative;overflow:hidden}
.scroll-line::after{content:'';position:absolute;top:0;left:0;width:100%;height:14px;background:var(--gold-bright);animation:scrollDot 2.1s cubic-bezier(.65,0,.35,1) infinite}
@keyframes scrollDot{0%{transform:translateY(-16px)}100%{transform:translateY(46px)}}
.hero-foot-note{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);text-align:right}
.hero-foot-note b{color:var(--gold);font-weight:400}
.marquee{position:relative;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:22px 0;overflow:hidden;background:linear-gradient(180deg,rgba(245,196,81,.028),transparent)}
.marquee-track{display:flex;white-space:nowrap;width:max-content;animation:marq 38s linear infinite}
.marquee:hover .marquee-track{animation-play-state:paused}
@keyframes marq{to{transform:translateX(-50%)}}
.marquee-track > *{display:inline-flex;align-items:center;gap:34px;padding:0 34px;font-size:clamp(1rem,2vw,1.5rem);font-weight:500;letter-spacing:-.02em}
.marquee-track .sep{color:var(--gold);font-size:.6em;padding:0;gap:0}
.marquee-track .out{-webkit-text-stroke:1px rgba(245,196,81,.5);color:transparent;font-weight:600}
/* ABOUT */
.about-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:clamp(30px,5vw,80px);align-items:start}
.about-visual{position:relative;border:1px solid var(--line);border-radius:6px;overflow:hidden;aspect-ratio:4/5;background:#0A0A0C}
.tutor-slider{position:absolute;inset:0;overflow:hidden}
.tutor-slide{position:absolute;inset:0;opacity:0;transition:opacity 1.3s var(--ease)}
.tutor-slide.on{opacity:1}
.tutor-slide .bg{position:absolute;inset:0;background:radial-gradient(ellipse at 30% 20%,rgba(245,196,81,.14),transparent 58%),radial-gradient(ellipse at 75% 85%,rgba(245,196,81,.09),transparent 58%),#0C0C0E}
.tutor-slide img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform:scale(1.14);transition:transform 7s var(--ease)}
.tutor-slide.on img{transform:scale(1)}
.tutor-slide .fallback{position:absolute;inset:0;display:grid;place-items:center;font-family:var(--font-m);font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2);text-align:center;padding:20px;line-height:2}
.slider-chrome{position:absolute;inset:0;z-index:4;pointer-events:none;background:linear-gradient(180deg,rgba(7,7,8,.22) 0%,transparent 30%,transparent 62%,rgba(7,7,8,.85) 100%)}
.slider-meta{position:absolute;left:0;right:0;bottom:0;z-index:5;padding:22px 24px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px}
.slider-cap{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:rgba(237,234,228,.72);line-height:1.9}
.slider-cap b{display:block;color:var(--gold);font-weight:400;letter-spacing:.2em;margin-bottom:3px}
.slider-dots{display:flex;gap:6px;pointer-events:auto}
.slider-dot{width:22px;height:2px;background:rgba(255,255,255,.18);border-radius:2px;transition:background .4s,width .4s var(--ease);cursor:pointer}
.slider-dot.on{background:var(--gold);width:38px;box-shadow:0 0 12px rgba(245,196,81,.6)}
.about-visual .corner{position:absolute;width:16px;height:16px;border:1px solid var(--gold);opacity:.55;z-index:6}
.about-visual .c1{top:12px;left:12px;border-right:0;border-bottom:0}
.about-visual .c2{top:12px;right:12px;border-left:0;border-bottom:0}
.about-visual .c3{bottom:12px;left:12px;border-right:0;border-top:0}
.about-visual .c4{bottom:12px;right:12px;border-left:0;border-top:0}
.about-visual .fig{position:absolute;top:22px;left:26px;z-index:6;font-family:var(--font-m);font-size:9px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2)}
.about-visual .fig b{color:var(--gold);font-weight:400}
.about-visual .rec{position:absolute;top:22px;right:26px;z-index:6;display:flex;align-items:center;gap:7px;font-family:var(--font-m);font-size:9px;letter-spacing:.24em;text-transform:uppercase;color:rgba(237,234,228,.55)}
.about-visual .rec::before{content:'';width:6px;height:6px;border-radius:50%;background:#ff3b3b;box-shadow:0 0 9px #ff3b3b;animation:pulse 1.6s infinite}
.about-body p{font-family:var(--sinhala);font-size:clamp(.95rem,1.15vw,1.04rem);line-height:2.05;color:#B9B7B1;font-weight:300;margin-bottom:34px}
.about-body p::first-letter{font-family:var(--font-s);font-size:3.2em;line-height:.82;float:left;margin:6px 12px 0 0;background:linear-gradient(160deg,var(--gold-bright),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent}
.about-name{display:flex;align-items:baseline;gap:14px;margin-bottom:26px;flex-wrap:wrap}
.about-name h3{font-size:clamp(1.5rem,2.4vw,2.1rem);font-weight:600;letter-spacing:-.03em}
.about-name span{font-family:var(--font-m);font-size:10px;letter-spacing:.26em;text-transform:uppercase;color:var(--gold)}
.stats{display:grid;grid-template-columns:repeat(2,1fr);border-top:1px solid var(--line-soft);border-left:1px solid var(--line-soft)}
.stat{padding:26px 22px;border-bottom:1px solid var(--line-soft);border-right:1px solid var(--line-soft);position:relative;overflow:hidden;transition:background .5s}
.stat::after{content:'';position:absolute;left:0;top:0;width:100%;height:100%;background:linear-gradient(135deg,rgba(245,196,81,.09),transparent 65%);opacity:0;transition:opacity .5s}
.stat:hover::after{opacity:1}
.stat-n{font-size:clamp(1.9rem,3.4vw,2.9rem);font-weight:600;letter-spacing:-.045em;line-height:1;color:var(--gold);margin-bottom:9px;font-variant-numeric:tabular-nums}
.stat-l{font-family:var(--font-m);font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted-2)}
/* RESULTS */
.results-top{display:flex;justify-content:space-between;align-items:flex-end;gap:34px;flex-wrap:wrap;margin-bottom:44px}
.results-nav{display:flex;gap:10px}
.rnav{width:50px;height:50px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;transition:background .4s,border-color .4s,transform .4s var(--ease)}
.rnav svg{width:16px;height:16px;stroke:var(--gold);transition:stroke .4s}
.rnav:hover{background:var(--gold);border-color:var(--gold);transform:scale(1.06)}
.rnav:hover svg{stroke:#0a0a0a}
.rnav:disabled{opacity:.28;pointer-events:none}
.perf-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:20px;cursor:grab;scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.perf-track::-webkit-scrollbar{display:none}
.perf-track.dragging{cursor:grabbing;scroll-snap-type:none}
.perf{flex:0 0 clamp(280px,26vw,350px);scroll-snap-align:start;border:1px solid var(--line-soft);border-radius:6px;background:var(--surface);padding:28px 24px 24px;position:relative;overflow:hidden;transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s}
.perf::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);transform:scaleX(0);transition:transform .7s var(--ease)}
.perf:hover{border-color:rgba(245,196,81,.42);background:var(--surface-2)}
.perf:hover::before{transform:scaleX(1)}
.perf:hover .perf-rank{color:var(--gold);text-shadow:0 0 34px rgba(245,196,81,.45)}
.perf:hover .perf-av{border-color:rgba(245,196,81,.75);transform:scale(1.06)}
.perf-idx{position:absolute;top:20px;right:22px;font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;color:var(--muted-2)}
.perf-av{width:72px;height:72px;border-radius:50%;position:relative;overflow:hidden;background:linear-gradient(140deg,rgba(245,196,81,.28),rgba(245,196,81,.05));border:1px solid rgba(245,196,81,.3);display:grid;place-items:center;font-family:var(--font-m);font-size:16px;color:var(--gold);font-weight:500;margin-bottom:22px;transition:border-color .5s,transform .55s var(--ease)}
.perf-av img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:2}
.perf-av span{position:relative;z-index:1}
.perf-rank{font-size:clamp(2.6rem,5vw,3.8rem);font-weight:600;letter-spacing:-.06em;line-height:.92;color:#2C2C31;transition:color .6s var(--ease),text-shadow .6s var(--ease);margin-bottom:6px;font-variant-numeric:tabular-nums}
.perf-rank small{font-size:.34em;letter-spacing:.02em;vertical-align:super;font-weight:500;margin-right:2px}
.perf-role{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);margin-bottom:22px}
.perf-name{font-size:1.14rem;font-weight:600;letter-spacing:-.02em;line-height:1.3;margin-bottom:7px}
.perf-school{font-family:var(--sinhala);font-size:12.5px;color:var(--muted);line-height:1.6;margin-bottom:22px;min-height:40px}
.perf-foot{display:flex;align-items:center;gap:9px;padding-top:16px;border-top:1px solid var(--line-soft);font-family:var(--font-m);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted-2)}
.perf-foot b{color:var(--text);font-weight:500}
.perf-foot .dot{width:4px;height:4px;border-radius:50%;background:var(--gold)}
/* REVIEWS */
.reviews-head{text-align:center;max-width:660px;margin:0 auto clamp(40px,6vh,64px)}
.rev-marquee{overflow:hidden;position:relative;padding:6px 0}
.rev-marquee::before,.rev-marquee::after{content:'';position:absolute;top:0;bottom:0;width:14vw;z-index:3;pointer-events:none}
.rev-marquee::before{left:0;background:linear-gradient(90deg,var(--bg),transparent)}
.rev-marquee::after{right:0;background:linear-gradient(270deg,var(--bg),transparent)}
.rev-row{display:flex;gap:18px;width:max-content;padding:12px 0}
.rev-row.a{animation:marq 62s linear infinite}
.rev-row.b{animation:marq 74s linear infinite reverse}
.rev-marquee:hover .rev-row{animation-play-state:paused}
.rev{flex:0 0 clamp(300px,31vw,410px);border:1px solid var(--line-soft);border-radius:6px;background:var(--surface);padding:28px 26px;display:flex;flex-direction:column;gap:16px}
.rev-stars{display:flex;gap:3px;color:var(--gold);font-size:11px;letter-spacing:2px}
.rev-q{font-family:var(--sinhala);font-size:13.2px;line-height:2;color:#B4B2AC;font-weight:300;flex:1}
.rev-a{display:flex;align-items:center;gap:12px;padding-top:16px;border-top:1px solid var(--line-soft)}
.rev-av{width:42px;height:42px;border-radius:50%;flex-shrink:0;position:relative;overflow:hidden;background:linear-gradient(140deg,rgba(245,196,81,.3),rgba(245,196,81,.06));border:1px solid var(--line);display:grid;place-items:center;font-family:var(--font-m);font-size:11px;color:var(--gold);font-weight:500}
.rev-av img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:2}
.rev-av span{position:relative;z-index:1}
.rev-n{font-size:12.8px;font-weight:500;letter-spacing:-.01em}
.rev-r{font-family:var(--font-m);font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2)}
/* GALLERY */
.gal{position:relative;border:1px solid var(--line-soft);border-radius:6px;overflow:hidden;background:var(--surface)}
.gal-view{position:relative;aspect-ratio:16/8;overflow:hidden}
.gal-slide{position:absolute;inset:0;opacity:0;transform:scale(1.06);transition:opacity 1.1s var(--ease),transform 1.5s var(--ease);display:grid;place-items:center;background:radial-gradient(ellipse at 30% 30%,rgba(245,196,81,.11),transparent 55%),radial-gradient(ellipse at 72% 72%,rgba(245,196,81,.06),transparent 55%),#0C0C0E}
.gal-slide.on{opacity:1;transform:scale(1)}
.gal-slide .ph{width:min(78%,720px);aspect-ratio:16/9;border:1px dashed rgba(245,196,81,.24);border-radius:4px;display:grid;place-items:center;gap:8px;text-align:center;padding:20px}
.gal-slide .ph b{font-family:var(--font-m);font-size:10px;letter-spacing:.26em;text-transform:uppercase;color:var(--gold);font-weight:400}
.gal-slide .ph small{font-family:var(--font-m);font-size:9px;letter-spacing:.16em;color:var(--muted-2);text-transform:uppercase}
.gal-ui{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 24px;border-top:1px solid var(--line-soft);background:rgba(0,0,0,.25);flex-wrap:wrap}
.gal-count{font-family:var(--font-m);font-size:10.5px;letter-spacing:.24em;color:var(--muted);font-variant-numeric:tabular-nums}
.gal-count b{color:var(--gold);font-weight:500}
.gal-btns{display:flex;gap:8px}
.gal-btn{width:42px;height:42px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;transition:background .4s,border-color .4s,transform .4s var(--ease)}
.gal-btn svg{width:14px;height:14px;stroke:var(--gold);transition:stroke .4s}
.gal-btn:hover{background:var(--gold);border-color:var(--gold);transform:scale(1.06)}
.gal-btn:hover svg{stroke:#0a0a0a}
.gal-cap{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2)}
/* CLASSES */
.classes-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.class-card{position:relative;border:1px solid var(--line-soft);border-radius:6px;overflow:hidden;padding:32px 28px 28px;background:var(--surface);transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s;display:flex;flex-direction:column;gap:6px;min-height:220px}
.class-card::after{content:'';position:absolute;inset:0;background:radial-gradient(circle at 100% 0%,rgba(245,196,81,.11),transparent 58%);opacity:0;transition:opacity .6s}
.class-card:hover{border-color:rgba(245,196,81,.4);transform:translateY(-6px);background:var(--surface-2)}
.class-card:hover::after{opacity:1}
.class-card:hover .class-go{transform:translate(5px,-5px);color:var(--gold)}
.class-year{font-size:clamp(2.4rem,4vw,3.4rem);font-weight:600;letter-spacing:-.06em;line-height:1;color:var(--text);position:relative;z-index:2}
.class-type{font-family:var(--font-m);font-size:10px;letter-spacing:.26em;text-transform:uppercase;color:var(--gold);margin-top:6px;position:relative;z-index:2}
.class-handle{font-family:var(--font-m);font-size:11.5px;letter-spacing:.06em;color:var(--muted);margin-top:auto;position:relative;z-index:2;padding-top:22px}
.class-go{position:absolute;top:26px;right:26px;font-size:15px;color:var(--muted-2);z-index:2;transition:transform .5s var(--ease),color .4s}
/* NEWS */
.news-slider{position:relative}
.news-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;padding:6px 0 24px;cursor:grab;scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.news-track::-webkit-scrollbar{display:none}
.news-card{flex:0 0 clamp(260px,24vw,320px);scroll-snap-align:start;border:1px solid var(--line-soft);border-radius:8px;background:var(--surface);overflow:hidden;display:flex;flex-direction:column;transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s}
.news-card:hover{border-color:rgba(245,196,81,.4);background:var(--surface-2);transform:translateY(-6px)}
.news-img{aspect-ratio:1/1;position:relative;overflow:hidden;background:#0C0C0E;display:grid;place-items:center}
.news-img::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(7,7,8,.55) 100%);pointer-events:none}
.news-img img{width:100%;height:100%;object-fit:cover;transition:transform .9s var(--ease)}
.news-card:hover .news-img img{transform:scale(1.06)}
.news-img .placeholder{font-family:var(--font-m);font-size:9px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2);text-align:center;padding:20px;line-height:2}
.news-body{padding:22px 22px 24px;display:flex;flex-direction:column;gap:10px;flex:1}
.news-date{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}
.news-title{font-size:1.06rem;font-weight:600;letter-spacing:-.02em;line-height:1.32;color:var(--text)}
.news-desc{font-family:var(--sinhala);font-size:12.8px;line-height:1.75;color:var(--muted);font-weight:300;flex:1;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
/* PAPER FEEDBACK */
.paper-active-chip{display:inline-flex;align-items:center;gap:10px;font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);border:1px solid var(--line);border-radius:100px;padding:9px 16px;background:rgba(245,196,81,.04);margin-top:18px;margin-bottom:28px}
.paper-active-chip .dot{width:6px;height:6px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 0 rgba(245,196,81,.7);animation:pulse 2.2s infinite;flex-shrink:0}
.paper-active-chip b{color:var(--gold);font-weight:500}
.paper-card{padding:clamp(26px,3.4vw,40px)}
.paper-meta{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:8px}
@media(max-width:800px){.paper-meta{grid-template-columns:1fr}}
.paper-block{padding-top:22px;margin-top:22px;border-top:1px solid var(--line-soft)}
.paper-block-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.paper-block-head h4{font-size:1.02rem;font-weight:600;letter-spacing:-.02em}
.paper-pick{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);transition:color .3s}
.paper-pick.full{color:var(--gold)}
.paper-hint{font-family:var(--font-m);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted-2);line-height:1.8;margin-bottom:14px}
.q-grid{display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(56px,1fr))}
.q-grid.is-mcq{grid-template-columns:repeat(10,1fr)}
.q-grid.is-essay{grid-template-columns:repeat(7,1fr)}
@media(max-width:640px){
  .q-grid.is-mcq{grid-template-columns:repeat(5,1fr);gap:6px}
  .q-grid.is-essay{grid-template-columns:repeat(4,1fr);gap:6px}
}
.q-chip{aspect-ratio:1;border:1px solid var(--line-soft);border-radius:6px;display:grid;place-items:center;font-family:var(--font-m);font-size:11px;font-weight:500;color:var(--muted);background:rgba(255,255,255,.015);transition:color .3s,border-color .3s,background .3s,transform .3s var(--ease),box-shadow .3s;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;padding:0}
.q-chip:hover{color:var(--gold);border-color:rgba(245,196,81,.4);transform:translateY(-2px)}
.q-chip.on{color:#0a0a0a;background:var(--gold);border-color:var(--gold);box-shadow:0 6px 22px -6px rgba(245,196,81,.6)}
.q-chip.wide{aspect-ratio:auto;padding:14px 8px;font-size:11.5px;letter-spacing:.06em}
/* CONTACT */
.contact-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
.cc{border:1px solid var(--line-soft);border-radius:6px;padding:36px 30px;background:var(--surface);position:relative;overflow:hidden;transition:border-color .55s var(--ease),background .55s,transform .55s var(--ease);display:flex;flex-direction:column;gap:14px;min-height:230px}
.cc:hover{border-color:rgba(245,196,81,.4);background:var(--surface-2);transform:translateY(-6px)}
.cc-ico{width:46px;height:46px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;transition:background .5s,border-color .5s}
.cc-ico svg{width:19px;height:19px;stroke:var(--gold);transition:stroke .5s}
.cc:hover .cc-ico{background:var(--gold);border-color:var(--gold)}
.cc:hover .cc-ico svg{stroke:#0a0a0a}
.cc-t{font-size:1.28rem;font-weight:600;letter-spacing:-.025em;margin-top:auto}
.cc-s{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2)}
.cc-arrow{position:absolute;bottom:30px;right:28px;font-size:16px;color:var(--muted-2);transition:transform .5s var(--ease),color .4s}
.cc:hover .cc-arrow{transform:translate(5px,-5px);color:var(--gold)}
/* COMMUNITY STACK */
.community-stack{margin-top:clamp(40px,6vh,70px);display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:900px){.community-stack{grid-template-columns:1fr}}
.community-card{position:relative;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:linear-gradient(160deg,rgba(245,196,81,.045),transparent 55%),#0A0A0C;padding:clamp(26px,3.4vw,40px);transition:border-color .5s var(--ease),background .5s}
.community-card::before{content:'';position:absolute;top:0;left:15%;right:15%;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);opacity:.9}
.community-card:hover{border-color:rgba(245,196,81,.4)}
.community-head{display:flex;align-items:center;gap:14px;margin-bottom:22px}
.community-icon{width:44px;height:44px;border:1px solid rgba(245,196,81,.35);border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 30% 30%,rgba(245,196,81,.15),transparent 65%);flex-shrink:0}
.community-icon svg{width:20px;height:20px;stroke:var(--gold)}
.community-head-txt{flex:1;min-width:0}
.community-head h3{font-size:clamp(1.1rem,1.6vw,1.35rem);font-weight:600;letter-spacing:-.025em;line-height:1.2;margin-bottom:3px}
.community-head h3 em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.community-head p{font-family:var(--font-m);font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted-2);line-height:1.8}
.community-card .form{grid-template-columns:1fr 1fr}
@media(max-width:640px){.community-card .form{grid-template-columns:1fr}}
.stars-input{display:flex;gap:6px;font-size:26px;color:rgba(255,255,255,.12);cursor:pointer;user-select:none;line-height:1}
.stars-input span{transition:color .25s,transform .3s var(--ease)}
.stars-input span.on{color:var(--gold);text-shadow:0 0 16px rgba(245,196,81,.55)}
.stars-input:hover span:hover{transform:scale(1.15)}
.community-success{display:none;padding:28px 20px;text-align:center}
.community-success.on{display:block;animation:successFade .7s var(--ease)}
@keyframes successFade{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.community-success-ico{width:70px;height:70px;margin:0 auto 20px;border-radius:50%;border:1px solid rgba(245,196,81,.4);display:grid;place-items:center;background:radial-gradient(circle,rgba(245,196,81,.15),transparent 70%);animation:pulse 2s infinite}
.community-success-ico svg{width:28px;height:28px;stroke:var(--gold)}
.community-success h4{font-size:1.2rem;font-weight:600;letter-spacing:-.025em;margin-bottom:8px}
.community-success h4 em{font-family:var(--font-s);font-style:italic;font-weight:400;color:var(--gold)}
.community-success p{color:var(--muted);font-weight:300;font-size:13px;line-height:1.85;max-width:36ch;margin:0 auto 20px}
.community-again{font-family:var(--font-m);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);border:1px solid var(--line);border-radius:100px;padding:11px 22px;transition:background .4s,color .4s}
.community-again:hover{background:var(--gold);color:#0a0a0a}
/* MAGIC TEASER */
.magic-teaser{margin-top:clamp(50px,8vh,90px);border:1px solid rgba(245,196,81,.28);border-radius:12px;overflow:hidden;background:linear-gradient(140deg,rgba(245,196,81,.08),transparent 60%),#0A0A0C;position:relative;padding:clamp(34px,5vw,64px)}
.magic-teaser::before{content:'';position:absolute;top:0;left:15%;right:15%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-bright),transparent)}
.magic-teaser-grid{position:relative;z-index:2;display:grid;grid-template-columns:1.4fr 1fr;gap:40px;align-items:center}
@media(max-width:900px){.magic-teaser-grid{grid-template-columns:1fr;gap:26px}}
.magic-teaser .kicker{font-family:var(--font-m);font-size:10px;letter-spacing:.4em;text-transform:uppercase;color:var(--gold);margin-bottom:18px;display:inline-flex;align-items:center;gap:11px}
.magic-teaser .kicker::before{content:'';width:32px;height:1px;background:var(--gold)}
.magic-teaser h2{font-size:clamp(1.8rem,3.6vw,3.2rem);font-weight:600;line-height:1.05;letter-spacing:-.04em;margin-bottom:18px}
.magic-teaser h2 em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.magic-teaser p{font-size:clamp(.95rem,1.2vw,1.05rem);color:var(--muted);font-weight:300;max-width:56ch;margin-bottom:26px}
.magic-teaser .magic-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.magic-pill{border:1px solid var(--line-soft);border-radius:6px;padding:14px 16px;font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:10px;transition:color .3s,border-color .3s,background .3s}
.magic-pill::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--gold);flex-shrink:0}
.magic-pill:hover{color:var(--gold);border-color:rgba(245,196,81,.4);background:rgba(245,196,81,.04)}
@media(max-width:1080px){
  .hero-inner{grid-template-columns:1fr;gap:40px}
  .about-grid{grid-template-columns:1fr}
  .about-visual{aspect-ratio:4/5;max-width:520px;margin:0 auto;width:100%}
  .classes-grid,.contact-grid{grid-template-columns:1fr}
}
@media(max-width:640px){
  .hero{padding-top:118px;min-height:auto;padding-bottom:60px}
  .hero-title{font-size:clamp(2.4rem,11vw,3.8rem)}
  .stats{grid-template-columns:1fr 1fr}
  .news-card{flex:0 0 78vw}
  .rev{flex:0 0 84vw;padding:24px 22px}
  .rev-q{font-size:12.8px}
  .perf{flex:0 0 82vw}
  .stars-input{font-size:22px}
}
"""


# ============================================================
# PORTFOLIO BODY
# ============================================================
PORTFOLIO_BODY = """
<section class="hero" id="home">
  <div class="hero-grid-bg"></div>
  <canvas id="hero-canvas"></canvas>
  <div class="hero-inner">
    <div class="hero-left">
      <div class="eyebrow"><span class="pulse"></span> Results Oriented · A/L Physics</div>
      <h1 class="hero-title">
        <span class="ln"><span>Shamil</span></span>
        <span class="ln"><span class="accent">Rathnayake</span></span>
      </h1>
      <p class="hero-sub">The leader in delivering <em>Results</em>.</p>
      <div class="hero-hash"><b>#</b>Next gen physics</div>
      <div class="hero-cta">
        <a href="#join" class="btn btn-gold" data-cursor><span>Join Class</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </a>
        <a href="/magic" class="btn btn-ghost" data-cursor><span>✦ Enter Magic</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </a>
      </div>
    </div>
    <div class="hero-side">
      <div class="side-label">Class Locations</div>
      <div class="loc"><span class="loc-name">Nenik</span><span class="loc-place">Gampaha</span></div>
      <div class="loc"><span class="loc-name">Siyathmin</span><span class="loc-place">Kurunegala</span></div>
      <div class="loc"><span class="loc-name">Reliance</span><span class="loc-place">Kandy</span></div>
      <div class="loc live"><span class="loc-name">All Island</span><span class="loc-place">Online</span></div>
    </div>
  </div>
  <div class="hero-foot">
    <div class="scroll-cue"><div class="scroll-line"></div>Scroll</div>
    <div class="hero-foot-note">Physics · <b>Since day one</b><br>Results that speak</div>
  </div>
</section>

<div class="marquee" aria-hidden="true">
  <div class="marquee-track" id="marqueeTrack">
    <span>Results Oriented</span><span class="sep">✦</span>
    <span class="out">#Next Gen Physics</span><span class="sep">✦</span>
    <span>A/L Physics</span><span class="sep">✦</span>
    <span class="out">Theory · Revision · Papers</span><span class="sep">✦</span>
    <span>Island Wide</span><span class="sep">✦</span>
    <span class="out">Shamil Rathnayake</span><span class="sep">✦</span>
  </div>
</div>

<section class="sec" id="about">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">01</span><span class="sec-label">About the Tutor</span><span class="sec-rule"></span></div>
    <div class="about-grid">
      <div class="about-visual" data-reveal>
        <div class="tutor-slider" id="tutorSlider">
          <div class="tutor-slide on"><div class="bg"></div><div class="fallback">assets/tutor/tutor-1.jpg</div><img src="https://i.ibb.co/6RX9fZqc/mypic2.webp" alt="" loading="lazy" onerror="this.remove()"></div>
          <div class="tutor-slide"><div class="bg"></div><div class="fallback">assets/tutor/tutor-2.jpg</div><img src="https://i.ibb.co/5XgYKqZL/mypic3.webp" alt="" loading="lazy" onerror="this.remove()"></div>
          <div class="tutor-slide"><div class="bg"></div><div class="fallback">assets/tutor/tutor-3.jpg</div><img src="https://i.ibb.co/C5SbZx0M/mypic4.webp" alt="" loading="lazy" onerror="this.remove()"></div>
        </div>
        <div class="slider-chrome"></div>
        <span class="corner c1"></span><span class="corner c2"></span><span class="corner c3"></span><span class="corner c4"></span>
        <div class="fig">Fig. <b>01</b> — The Tutor</div>
        <div class="rec">Live</div>
        <div class="slider-meta">
          <div class="slider-cap"><b id="tutorCapTop">Physics · A/L</b><span id="tutorCapBot">Shamil Rathnayake</span></div>
          <div class="slider-dots" id="tutorDots"></div>
        </div>
      </div>
      <div class="about-body">
        <div class="about-name" data-reveal><h3>Shamil Rathnayaka</h3><span>Electrical &amp; Electronic Engineer</span></div>
        <p data-reveal>මම ශමිල් රත්නායක. පළපුරුදු විද්‍යුත් හා විදුලි ඉංජිනේරුවෙකු මෙන්ම කැපවීමෙන් කටයුතු කරන ගුරුවරයෙකු ලෙස, සංකීර්ණ තාක්ෂණික සංකල්ප සරල, පැහැදිලි සහ ප්‍රායෝගික පාඩම් බවට පත් කිරීම මගේ ප්‍රධාන අරමුණයි. සිසුන් තුළ ශක්තිමත් විශ්ලේෂණාත්මක චින්තනය සහ ගැටලු විසඳීමේ හැකියාව වර්ධනය කරමින්, අභියෝගාත්මක විෂය කරුණු සාර්ථකව ජයගෙන, ඔවුන්ගේ උපරිම අධ්‍යාපනික හැකියාව කරා ළඟා වීමට අවශ්‍ය දැනුම, අවබෝධය සහ විශ්වාසය ගොඩනැගීම සඳහා මම කැපවී සිටිමි.</p>
        <div class="stats" data-reveal>
          <div class="stat"><div class="stat-n" data-count="1000" data-suffix="+">0</div><div class="stat-l">Total A Passes</div></div>
          <div class="stat"><div class="stat-n" data-count="5" data-suffix="+">0</div><div class="stat-l">Years Experience</div></div>
          <div class="stat"><div class="stat-n" data-count="15" data-suffix="+">0</div><div class="stat-l">Classes</div></div>
          <div class="stat"><div class="stat-n" data-count="5000" data-suffix="+">0</div><div class="stat-l">Students Reached</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sec" id="results" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">02</span><span class="sec-label">Results</span><span class="sec-rule"></span></div>
    <div class="results-top">
      <div data-reveal>
        <h2 class="sec-title">Top <em>Performers</em></h2>
        <p class="sec-lead">Numbers don't flatter. They simply report. Here are the students who turned theory into ranks.</p>
      </div>
      <div class="results-nav" data-reveal>
        <button class="rnav" id="perfPrev" aria-label="Previous" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M15 6l-6 6 6 6"/></svg></button>
        <button class="rnav" id="perfNext" aria-label="Next" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M9 6l6 6-6 6"/></svg></button>
      </div>
    </div>
    <div class="perf-track" id="perfTrack"></div>
  </div>
</section>

<section class="sec" id="reviews" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">03</span><span class="sec-label">Student Reviews</span><span class="sec-rule"></span></div>
  </div>
  <div class="reviews-head" data-reveal>
    <h2 class="sec-title">What students say about <em>Sir's class</em>.</h2>
    <p class="sec-lead" style="margin:0 auto">Real words. Real results. Straight from the students who sat the paper.</p>
  </div>
  <div class="rev-marquee"><div class="rev-row a" id="revRowA"></div></div>
  <div class="rev-marquee" style="margin-top:6px"><div class="rev-row b" id="revRowB"></div></div>
</section>

<section class="sec" id="gallery" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">04</span><span class="sec-label">Gallery</span><span class="sec-rule"></span></div>
    <div style="margin-bottom:clamp(30px,4vh,44px)" data-reveal>
      <h2 class="sec-title">Class <em>Moments</em></h2>
      <p class="sec-lead">A look inside Sir's physics classes — sessions, discussions and milestones.</p>
    </div>
    <div class="gal" data-reveal>
      <div class="gal-view" id="galView">
        <div class="gal-slide on"><div class="ph"><div><b>Class Photo 01</b><br><small>Replace with your image</small></div></div></div>
        <div class="gal-slide"><div class="ph"><div><b>Class Photo 02</b><br><small>Replace with your image</small></div></div></div>
      </div>
      <div class="gal-ui">
        <span class="gal-cap" id="galCap">Session · Theory Discussion</span>
        <span class="gal-count"><b id="galNow">01</b> / <span id="galTotal">02</span></span>
        <div class="gal-btns">
          <button class="gal-btn" id="galPrev" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M15 6l-6 6 6 6"/></svg></button>
          <button class="gal-btn" id="galNext" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M9 6l6 6-6 6"/></svg></button>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sec" id="class" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">05</span><span class="sec-label">Class</span><span class="sec-rule"></span></div>
    <div style="margin-bottom:clamp(30px,4vh,44px)" data-reveal>
      <h2 class="sec-title">Join the <em>batch</em>.</h2>
      <p class="sec-lead">Theory and revision channels are live on Telegram. Pick your year and step in.</p>
    </div>
    <div class="classes-grid">
      <a href="#" class="class-card" data-cursor data-reveal><span class="class-go">↗</span><div class="class-year">2028</div><div class="class-type">Theory</div><div class="class-handle">@SR_28THD</div></a>
      <a href="#" class="class-card" data-cursor data-reveal><span class="class-go">↗</span><div class="class-year">2027</div><div class="class-type">Theory</div><div class="class-handle">@SR_27THD</div></a>
      <a href="#" class="class-card" data-cursor data-reveal><span class="class-go">↗</span><div class="class-year">2026</div><div class="class-type">2027 Revision</div><div class="class-handle">@SR_REV27</div></a>
    </div>
  </div>
</section>

<section class="sec" id="news" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">06</span><span class="sec-label">Latest News</span><span class="sec-rule"></span></div>
    <div class="results-top" style="margin-bottom:34px">
      <div data-reveal>
        <h2 class="sec-title">What's <em>new</em>.</h2>
        <p class="sec-lead">Class updates, announcements and the latest from Sir — refreshed from the P6 Crew console.</p>
      </div>
      <div class="results-nav" data-reveal>
        <button class="rnav" id="newsPrev" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M15 6l-6 6 6 6"/></svg></button>
        <button class="rnav" id="newsNext" data-cursor><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M9 6l6 6-6 6"/></svg></button>
      </div>
    </div>
    <div class="news-slider">
      <div class="news-track" id="newsTrack"></div>
    </div>
  </div>
</section>

<section class="sec" id="paper" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">07</span><span class="sec-label">Paper Feedback</span><span class="sec-rule"></span></div>
    <div id="paperSection" data-reveal></div>
  </div>
</section>

<section class="sec" id="contact" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">08</span><span class="sec-label">Contact</span><span class="sec-rule"></span></div>
    <div style="margin-bottom:clamp(30px,4vh,48px)" data-reveal>
      <h2 class="sec-title">Get in touch with <em>Sir</em>.</h2>
      <p class="sec-lead">Reach out on WhatsApp, Telegram or the phone — or scroll down for the community forms.</p>
    </div>
    <div class="contact-grid">
      <a href="#" class="cc" data-cursor data-reveal>
        <div class="cc-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg></div>
        <div class="cc-t">WhatsApp</div><div class="cc-s">Chat instantly</div><span class="cc-arrow">↗</span>
      </a>
      <a href="#" class="cc" data-cursor data-reveal>
        <div class="cc-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg></div>
        <div class="cc-t">Telegram</div><div class="cc-s">Join the channel</div><span class="cc-arrow">↗</span>
      </a>
      <a href="tel:+" class="cc" data-cursor data-reveal>
        <div class="cc-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg></div>
        <div class="cc-t">Call</div><div class="cc-s">Speak directly</div><span class="cc-arrow">↗</span>
      </a>
    </div>

    <div class="community-stack" id="join">

      <div class="community-card" data-reveal>
        <div class="community-head">
          <div class="community-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
          <div class="community-head-txt">
            <h3>Join <em>Class</em></h3>
            <p>Request a seat · 24h response</p>
          </div>
        </div>
        <form class="form" id="formJoin" novalidate>
          <div class="field"><label for="jName">Full Name *</label><input type="text" id="jName" placeholder="e.g. Kavindu Perera" required></div>
          <div class="field"><label for="jPhone">Phone *</label><input type="tel" id="jPhone" placeholder="07X XXX XXXX" required></div>
          <div class="field"><label for="jEmail">Email</label><input type="email" id="jEmail" placeholder="you@example.com"></div>
          <div class="field"><label for="jBatch">Batch</label><select id="jBatch"><option value="2028">2028 Theory</option><option value="2027">2027 Theory</option><option value="2026" selected>2026 / 2027 Revision</option></select></div>
          <div class="field full"><label for="jLocation">Preferred Class</label><select id="jLocation"><option value="Nenik - Gampaha">Nenik · Gampaha</option><option value="Siyathmin - Kurunegala">Siyathmin · Kurunegala</option><option value="Reliance - Kandy">Reliance · Kandy</option><option value="Online - All Island" selected>Online · All Island</option></select></div>
          <div class="field full"><label for="jMessage">Message</label><textarea id="jMessage" placeholder="Tell Sir a bit about your current level."></textarea></div>
          <div class="submit-row"><div class="submit-note">Secured · <b>P6 Crew only</b></div><button type="submit" class="submit-btn" data-cursor><span>Send Request</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div>
        </form>
        <div class="community-success" id="okJoin">
          <div class="community-success-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
          <h4>Request <em>received</em>.</h4>
          <p>The P6 Crew will reach out within 24 hours.</p>
          <button type="button" class="community-again" data-again="join" data-cursor>Send another request</button>
        </div>
      </div>

      <div class="community-card" data-reveal>
        <div class="community-head">
          <div class="community-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
          <div class="community-head-txt">
            <h3>Leave a <em>Comment</em></h3>
            <p>Share your experience</p>
          </div>
        </div>
        <form class="form" id="formComment" novalidate>
          <div class="field"><label for="cName">Your Name *</label><input type="text" id="cName" placeholder="e.g. Dewmini A." required></div>
          <div class="field"><label for="cBatch">Batch</label><select id="cBatch"><option value="2028">2028</option><option value="2027">2027</option><option value="2026" selected>2026</option><option value="Past Student">Past Student</option></select></div>
          <div class="field full"><label>Rating</label><div class="stars-input" id="cStars" data-value="5"><span data-star="1" class="on">★</span><span data-star="2" class="on">★</span><span data-star="3" class="on">★</span><span data-star="4" class="on">★</span><span data-star="5" class="on">★</span></div></div>
          <div class="field full"><label for="cMessage">Your Comment *</label><textarea id="cMessage" placeholder="Share your experience — what worked, what helped, how you improved." required></textarea></div>
          <div class="submit-row"><div class="submit-note">Moderated by <b>P6 Crew</b></div><button type="submit" class="submit-btn" data-cursor><span>Post Comment</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div>
        </form>
        <div class="community-success" id="okComment">
          <div class="community-success-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
          <h4>Comment <em>submitted</em>.</h4>
          <p>Thank you for the kind words. The P6 Crew will review it.</p>
          <button type="button" class="community-again" data-again="comment" data-cursor>Write another</button>
        </div>
      </div>

      <div class="community-card" data-reveal>
        <div class="community-head">
          <div class="community-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg></div>
          <div class="community-head-txt">
            <h3>Feedback / <em>Complaint</em></h3>
            <p>Bugs · issues · suggestions</p>
          </div>
        </div>
        <form class="form" id="formComplaint" novalidate>
          <div class="field"><label for="fName">Your Name (optional)</label><input type="text" id="fName" placeholder="Anonymous is fine too"></div>
          <div class="field"><label for="fContact">Phone / Email (optional)</label><input type="text" id="fContact" placeholder="So we can follow up"></div>
          <div class="field full"><label for="fCategory">Category *</label><select id="fCategory" required><option value="bug" selected>Website Bug</option><option value="content">Content / Lesson Issue</option><option value="behavior">Class Behavior</option><option value="suggestion">Suggestion</option><option value="other">Other</option></select></div>
          <div class="field full"><label for="fMessage">Your Message *</label><textarea id="fMessage" placeholder="Describe the issue or suggestion clearly." required></textarea></div>
          <div class="submit-row"><div class="submit-note">Private · <b>P6 Crew</b></div><button type="submit" class="submit-btn" data-cursor><span>Send Feedback</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div>
        </form>
        <div class="community-success" id="okComplaint">
          <div class="community-success-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
          <h4>Feedback <em>received</em>.</h4>
          <p>Thank you. The P6 Crew reads every message.</p>
          <button type="button" class="community-again" data-again="complaint" data-cursor>Send another</button>
        </div>
      </div>

      <div class="community-card" data-reveal>
        <div class="community-head">
          <div class="community-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"/></svg></div>
          <div class="community-head-txt">
            <h3>Ask a <em>Doubt</em></h3>
            <p>Topic · question · past paper</p>
          </div>
        </div>
        <form class="form" id="formDoubt" novalidate>
          <div class="field"><label for="dName">Your Name *</label><input type="text" id="dName" placeholder="e.g. Kavindu P." required></div>
          <div class="field"><label for="dBatch">Batch</label><select id="dBatch"><option value="2028">2028</option><option value="2027">2027</option><option value="2026" selected>2026 / 2027 Revision</option></select></div>
          <div class="field full"><label for="dTopic">Topic / Chapter *</label><input type="text" id="dTopic" placeholder="e.g. Rotational Dynamics, 2019 Q7(b)" required></div>
          <div class="field full"><label for="dQuestion">Your Question *</label><textarea id="dQuestion" placeholder="Explain the doubt clearly." required></textarea></div>
          <div class="submit-row"><div class="submit-note">Answered in <b>upcoming classes</b></div><button type="submit" class="submit-btn" data-cursor><span>Send Doubt</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div>
        </form>
        <div class="community-success" id="okDoubt">
          <div class="community-success-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
          <h4>Doubt <em>submitted</em>.</h4>
          <p>Noted. Sir will address it in an upcoming session.</p>
          <button type="button" class="community-again" data-again="doubt" data-cursor>Ask another</button>
        </div>
      </div>

    </div>

    <div class="magic-teaser" data-reveal>
      <div class="magic-teaser-grid">
        <div>
          <div class="kicker">✦ NEW · SEPARATE WORLD</div>
          <h2>Enter <em>Magic</em>.</h2>
          <p>A completely separate interface built for learning and momentum. Class recordings from Sir, vertical motivation reels, 25+ interactive simulations, and 6 hand-built 3D visualizations — all in one clean space with its own navigation.</p>
          <a href="/magic" class="btn btn-gold" data-cursor><span>✦ Open Magic</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </a>
        </div>
        <div class="magic-grid">
          <a href="/magic/sessions" class="magic-pill">Sessions</a>
          <a href="/magic/from-sir" class="magic-pill">From Sir</a>
          <a href="/magic/simulations" class="magic-pill">Simulations</a>
          <a href="/magic/visualizations" class="magic-pill">Visualizations</a>
        </div>
      </div>
    </div>

  </div>
</section>
"""


# ============================================================
# PORTFOLIO JS
# ============================================================
PORTFOLIO_JS = r"""
(function(){
  'use strict';

  /* Helper: safely run each section */
  function safe(name, fn){
    try { fn(); }
    catch(err){ if(window.console) console.error('[' + name + ']', err); }
  }

  /* 1. TUTOR SLIDER */
  safe('tutor-slider', function(){
    var slider = document.getElementById('tutorSlider');
    if(!slider) return;
    var slides = [].slice.call(slider.querySelectorAll('.tutor-slide'));
    var dotsWrap = document.getElementById('tutorDots');
    var capTop = document.getElementById('tutorCapTop');
    var capBot = document.getElementById('tutorCapBot');
    var captions = [
      { top: 'Physics · A/L', bot: 'Shamil Rathnayake' },
      { top: 'Theory Session', bot: 'Concept Build' },
      { top: 'Paper Discussion', bot: 'Exam Practice' },
      { top: 'With Students', bot: 'Class Moments' }
    ];
    var idx = 0, timer = null;
    slides.forEach(function(_, i){
      var d = document.createElement('button');
      d.className = 'slider-dot' + (i === 0 ? ' on' : '');
      d.addEventListener('click', function(){ go(i); });
      dotsWrap.appendChild(d);
    });
    var dots = [].slice.call(dotsWrap.children);
    function go(n){
      idx = (n + slides.length) % slides.length;
      slides.forEach(function(s, i){ s.classList.toggle('on', i === idx); });
      dots.forEach(function(d, i){ d.classList.toggle('on', i === idx); });
      if(captions[idx]){ capTop.textContent = captions[idx].top; capBot.textContent = captions[idx].bot; }
      restart();
    }
    function restart(){
      clearInterval(timer);
      if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      timer = setInterval(function(){ go(idx + 1); }, 5600);
    }
    restart();
    var visual = document.querySelector('.about-visual');
    if(visual){
      visual.addEventListener('mouseenter', function(){ clearInterval(timer); });
      visual.addEventListener('mouseleave', restart);
    }
  });

  /* 2. TOP PERFORMERS — fixed observer */
  safe('rankers', function(){
    var RANKERS = [
      { n: 'Lahurini Edirisingha', s: 'Maliyadeva Balika Vidyalaya', rank: '1', img: 'https://i.ibb.co/QZBn1n9/images-1.jpg' },
      { n: 'Induwara Bandara', s: 'Maliyadeva Boys College', rank: '2', img: 'https://i.ibb.co/VY42sb06/d.webp' },
      { n: 'Nirali Edirisingha', s: 'Maliyadeva Balika Vidyalaya', rank: '3', img: 'https://i.ibb.co/kVNQWxcL/E-jpg.webp' },
      { n: 'Pasindu Hasaranaga', s: 'Maliyadeva College', rank: '3', img: 'https://i.ibb.co/SXtQR1y8/F-jpg.webp' },
      { n: 'Raindu Rashmina', s: 'Maliyadeva College', rank: '3', img: 'https://i.ibb.co/G4DW1Tw2/G-jpg.webp' },
      { n: 'Linali Athukorala', s: 'Maliyadeva Balika Vidyalaya', rank: '4', img: 'https://i.ibb.co/QZBn1n9/images-1.jpg' }
    ];
    function initials(name){
      return name.split(' ').map(function(w){ return w[0]; }).slice(0,2).join('').toUpperCase();
    }
    var perfTrack = document.getElementById('perfTrack');
    if(!perfTrack) return;

    var localIO = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting){ e.target.classList.add('in'); localIO.unobserve(e.target); }
      });
    }, { threshold: 0.08 });

    RANKERS.forEach(function(r, i){
      var el = document.createElement('article');
      el.className = 'perf';
      el.setAttribute('data-reveal', '');
      el.style.transitionDelay = (i * 0.05) + 's';
      el.innerHTML =
        '<span class="perf-idx">' + String(i+1).padStart(2,'0') + ' / ' + String(RANKERS.length).padStart(2,'0') + '</span>' +
        '<div class="perf-av"><span>' + initials(r.n) + '</span><img src="' + r.img + '" alt="" loading="lazy" onerror="this.remove()"></div>' +
        '<div class="perf-rank"><small>#</small>' + r.rank + '</div>' +
        '<div class="perf-role">District Rank</div>' +
        '<div class="perf-name">' + r.n + '</div>' +
        '<div class="perf-school">' + r.s + '</div>' +
        '<div class="perf-foot"><span class="dot"></span>Institute: <b>Siyathmin</b></div>';
      perfTrack.appendChild(el);
      localIO.observe(el);
      var rect = el.getBoundingClientRect();
      if(rect.top < window.innerHeight && rect.bottom > 0){ el.classList.add('in'); }
    });

    var prev = document.getElementById('perfPrev');
    var next = document.getElementById('perfNext');
    function cardStep(){
      var card = perfTrack.querySelector('.perf');
      if(!card) return 320;
      var gap = parseFloat(getComputedStyle(perfTrack).gap) || 20;
      return card.getBoundingClientRect().width + gap;
    }
    if(prev) prev.addEventListener('click', function(){ perfTrack.scrollBy({ left: -cardStep(), behavior: 'smooth' }); });
    if(next) next.addEventListener('click', function(){ perfTrack.scrollBy({ left: cardStep(), behavior: 'smooth' }); });
    function updateNav(){
      if(!prev || !next) return;
      var max = perfTrack.scrollWidth - perfTrack.clientWidth - 2;
      prev.disabled = perfTrack.scrollLeft <= 2;
      next.disabled = perfTrack.scrollLeft >= max;
    }
    perfTrack.addEventListener('scroll', updateNav, { passive: true });
    window.addEventListener('resize', updateNav);
    setTimeout(updateNav, 300);

    var down = false, sx = 0, sl = 0;
    perfTrack.addEventListener('pointerdown', function(e){
      down = true; sx = e.clientX; sl = perfTrack.scrollLeft;
      perfTrack.classList.add('dragging');
      try { perfTrack.setPointerCapture(e.pointerId); } catch(_){}
    });
    perfTrack.addEventListener('pointermove', function(e){
      if(!down) return;
      perfTrack.scrollLeft = sl - (e.clientX - sx);
    });
    function up(e){
      down = false;
      perfTrack.classList.remove('dragging');
      try { perfTrack.releasePointerCapture(e.pointerId); } catch(_){}
    }
    perfTrack.addEventListener('pointerup', up);
    perfTrack.addEventListener('pointercancel', up);
  });

  /* 3. REVIEWS */
  safe('reviews', function(){
    function initials(name){
      return name.split(' ').map(function(w){ return w[0]; }).slice(0,2).join('').toUpperCase();
    }
    var REVIEWS = [
      { n: 'Dewmini Amarasinghe', img: 'assets/reviews/dewmini.jpg', t: 'Physics වලට මට තිබුණු ලොකුම ප්‍රශ්නය තමයි theory එක තේරුණත් questions කරන්න ගියාම stuck වෙන එක. Sirගේ class එකෙන් theory එකත් එක්ක ඒක questions වලට apply කරන විදිහ හොඳටම තේරුම් ගත්තා. ඒ නිසා exam එක ළං වෙද්දි Physics ගැන ලොකු confidence එකක් තිබුණා. අවසානයේ Physics වලට A එකක් ගන්න පුළුවන් වුණේ Sirගේ guidance එක නිසා. ❤️' },
      { n: 'Hasith Nettikumara', img: 'assets/reviews/hasith.jpg', t: 'Sirගේ class එකේ මට වැඩියෙන්ම කැමති දෙයක් තමයි කිසිම theory එකක් මතක තියාගන්න විතරක් නොදී, ඒක ඇත්තටම තේරුම් කරලා දෙන එක. අමාරු පාඩම් පවා සරලව තේරුම් ගන්න පුළුවන් විදිහට Sir explain කරනවා. 🔥' },
      { n: 'Induwara Bandara', img: 'assets/reviews/induwara.jpg', t: 'Physics වලින් A එකක් ගන්න මගේ target එක තිබුණත්, ඒකට යන correct path එක මුලින්ම මට තේරුණේ නෑ. Sirගේ class එකෙන් theory, questions, past papers හැමදේම systematic විදිහට කරපු නිසා මට මගේම study plan එකක් හදාගන්න පුළුවන් වුණා. ❤️‍🔥' },
      { n: 'Nirali Heshala', img: 'assets/reviews/nirali.jpg', t: 'Sirගේ Physics class එක මට වෙනස් වුණේ Physics විෂය ගැන මගේ attitude එකම වෙනස් කරපු නිසා. මුලදී අමාරුයි කියලා හිතුණු concepts පස්සේ questions වලට confidently use කරන්න පුළුවන් වුණා. 💯' },
      { n: 'Pasindu Hasaranaga', img: 'assets/reviews/pasindu.jpg', t: 'A/L Physics වලින් A එකක් ගන්න මට ලැබුණු support එක ගැන මම ගොඩක් සතුටුයි. Sirගේ explanations හරිම clear. ❤️⚡' },
      { n: 'Raindu Rashmina', img: 'assets/reviews/raindhu.jpg', t: 'Sirගේ Physics class එකට ආවට පස්සේ Physics ගැන තිබුණු මගේ අදහස ගොඩක් වෙනස් වුණා. මුලදී අමාරුයි කියලා හිතුණු දේවල් Sir සරලව තේරුම් කරලා දුන්න නිසා questions කරන්නත් ලේසි වුණා. ❤️' }
    ];

    function reviewCard(r){
      var el = document.createElement('article');
      el.className = 'rev';
      el.innerHTML =
        '<div class="rev-stars">★★★★★</div>' +
        '<p class="rev-q">"' + r.t + '"</p>' +
        '<div class="rev-a"><div class="rev-av"><span>' + initials(r.n) + '</span><img src="' + r.img + '" alt="" loading="lazy" onerror="this.remove()"></div>' +
        '<div><div class="rev-n">' + r.n + '</div><div class="rev-r">A/L Physics Student</div></div></div>';
      return el;
    }

    var rowA = document.getElementById('revRowA');
    var rowB = document.getElementById('revRowB');
    if(rowA && rowB){
      var setA = [REVIEWS[0], REVIEWS[1], REVIEWS[2]];
      var setB = [REVIEWS[3], REVIEWS[4], REVIEWS[5]];
      setA.concat(setA).forEach(function(r){ rowA.appendChild(reviewCard(r)); });
      setB.concat(setB).forEach(function(r){ rowB.appendChild(reviewCard(r)); });
    }
  });

  /* 4. GALLERY */
  safe('gallery', function(){
    var gs = [].slice.call(document.querySelectorAll('.gal-slide'));
    var galNow = document.getElementById('galNow');
    var galTotal = document.getElementById('galTotal');
    var galCap = document.getElementById('galCap');
    var caps = ['Session · Theory Discussion', 'Class · Paper Review'];
    var gi = 0;
    if(galTotal) galTotal.textContent = String(gs.length).padStart(2,'0');
    function go(n){
      gi = (n + gs.length) % gs.length;
      gs.forEach(function(s, i){ s.classList.toggle('on', i === gi); });
      if(galNow) galNow.textContent = String(gi + 1).padStart(2,'0');
      if(galCap) galCap.textContent = caps[gi] || '';
    }
    var pv = document.getElementById('galPrev');
    var nx = document.getElementById('galNext');
    if(pv) pv.addEventListener('click', function(){ go(gi - 1); });
    if(nx) nx.addEventListener('click', function(){ go(gi + 1); });
  });

  /* 5. NEWS */
  safe('news', function(){
    var track = document.getElementById('newsTrack');
    if(!track) return;
    function render(items){
      if(!items || !items.length){
        track.innerHTML = '<div class="empty" style="flex:1;min-width:100%"><h3>No news yet.</h3><p>Check back soon</p></div>';
        return;
      }
      track.innerHTML = items.map(function(n){
        var img = n.image_url ? '<img src="' + n.image_url + '" alt="" loading="lazy" onerror="this.remove()">' : '<div class="placeholder">No image</div>';
        var date = n.created_at ? new Date(n.created_at.replace(' ', 'T')).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : '';
        return '<article class="news-card">' +
          '<div class="news-img">' + img + '</div>' +
          '<div class="news-body">' +
            '<div class="news-date">' + date + '</div>' +
            '<div class="news-title">' + (n.title || '') + '</div>' +
            '<div class="news-desc">' + (n.description || '') + '</div>' +
          '</div></article>';
      }).join('');
    }
    fetch('/api/news').then(function(r){ return r.json(); })
      .then(function(d){ if(d && d.ok) render(d.items); })
      .catch(function(){ render([]); });
    var p = document.getElementById('newsPrev');
    var n2 = document.getElementById('newsNext');
    function step(){
      var card = track.querySelector('.news-card');
      if(!card) return 300;
      var gap = parseFloat(getComputedStyle(track).gap) || 20;
      return card.getBoundingClientRect().width + gap;
    }
    if(p) p.addEventListener('click', function(){ track.scrollBy({ left: -step()*2, behavior: 'smooth' }); });
    if(n2) n2.addEventListener('click', function(){ track.scrollBy({ left: step()*2, behavior: 'smooth' }); });
  });

  /* 6. STARS */
  safe('stars', function(){
    var wrap = document.getElementById('cStars');
    if(!wrap) return;
    var stars = [].slice.call(wrap.querySelectorAll('span'));
    var value = 5;
    function paint(v){ stars.forEach(function(s, i){ s.classList.toggle('on', i < v); }); }
    stars.forEach(function(s, i){
      s.addEventListener('mouseenter', function(){ paint(i + 1); });
      s.addEventListener('click', function(){ value = i + 1; wrap.dataset.value = value; paint(value); });
    });
    wrap.addEventListener('mouseleave', function(){ paint(value); });
    paint(value);
  });

  /* 7. FORMS */
  safe('forms', function(){
    function post(url, payload, okEl, btn, label, hideForm){
      btn.disabled = true;
      var span = btn.querySelector('span');
      if(span) span.textContent = 'Sending...';
      fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        .then(function(r){ return r.json().then(function(d){ return { ok: r.ok, data: d }; }); })
        .then(function(res){
          if(res.ok && res.data.ok){
            okEl.classList.add('on');
            if(hideForm) hideForm.style.display = 'none';
            if(window.__toast) window.__toast('Sent · ID #' + res.data.id);
          } else {
            if(window.__toast) window.__toast(res.data.error || 'Failed', true);
            btn.disabled = false;
            if(span) span.textContent = label;
          }
        })
        .catch(function(){
          if(window.__toast) window.__toast('Network error', true);
          btn.disabled = false;
          if(span) span.textContent = label;
        });
    }
    function bind(formId, okId, endpoint, collect, label){
      var form = document.getElementById(formId);
      if(!form) return;
      var ok = document.getElementById(okId);
      var btn = form.querySelector('.submit-btn');
      form.addEventListener('submit', function(e){
        e.preventDefault();
        var payload = collect();
        if(!payload) return;
        post(endpoint, payload, ok, btn, label, form);
      });
    }
    bind('formJoin', 'okJoin', '/api/join-request', function(){
      var n = document.getElementById('jName').value.trim();
      var p = document.getElementById('jPhone').value.trim();
      if(!n || !p){ if(window.__toast) window.__toast('Name and phone are required', true); return null; }
      return { name: n, phone: p, email: document.getElementById('jEmail').value.trim(), batch: document.getElementById('jBatch').value, location: document.getElementById('jLocation').value, message: document.getElementById('jMessage').value.trim() };
    }, 'Send Request');
    bind('formComment', 'okComment', '/api/comment', function(){
      var n = document.getElementById('cName').value.trim();
      var m = document.getElementById('cMessage').value.trim();
      if(!n || !m){ if(window.__toast) window.__toast('Name and comment required', true); return null; }
      return { name: n, batch: document.getElementById('cBatch').value, rating: parseInt(document.getElementById('cStars').dataset.value || '5', 10), message: m };
    }, 'Post Comment');
    bind('formComplaint', 'okComplaint', '/api/complaint', function(){
      var m = document.getElementById('fMessage').value.trim();
      if(!m){ if(window.__toast) window.__toast('Message required', true); return null; }
      return { name: document.getElementById('fName').value.trim(), contact: document.getElementById('fContact').value.trim(), category: document.getElementById('fCategory').value, message: m };
    }, 'Send Feedback');
    bind('formDoubt', 'okDoubt', '/api/doubt', function(){
      var n = document.getElementById('dName').value.trim();
      var t = document.getElementById('dTopic').value.trim();
      var q = document.getElementById('dQuestion').value.trim();
      if(!n || !t || !q){ if(window.__toast) window.__toast('Name, topic, question required', true); return null; }
      return { name: n, batch: document.getElementById('dBatch').value, topic: t, question: q };
    }, 'Send Doubt');

    document.querySelectorAll('[data-again]').forEach(function(b){
      b.addEventListener('click', function(){
        var card = b.closest('.community-card');
        var form = card.querySelector('form');
        var ok = card.querySelector('.community-success');
        ok.classList.remove('on');
        if(form){ form.style.display = ''; form.reset(); }
        var btn = card.querySelector('.submit-btn');
        if(btn){
          btn.disabled = false;
          var which = b.dataset.again;
          var labels = { join: 'Send Request', comment: 'Post Comment', complaint: 'Send Feedback', doubt: 'Send Doubt', paper: 'Send Paper Feedback' };
          var span = btn.querySelector('span');
          if(span) span.textContent = labels[which] || 'Send';
        }
        if(b.dataset.again === 'comment'){
          document.querySelectorAll('#cStars span').forEach(function(s, i){ s.classList.toggle('on', i < 5); });
          var wrap = document.getElementById('cStars');
          if(wrap) wrap.dataset.value = 5;
        }
      });
    });
  });

  /* 8. PAPER FEEDBACK — Latest paper only */
  safe('paper-feedback', function(){
    var host = document.getElementById('paperSection');
    if(!host) return;

    var MCQ_VALUES = [];
    for(var i = 1; i <= 50; i++) MCQ_VALUES.push(i);
    var STRUCT_VALUES = [1, 2, 3, 4];
    var ESSAY_VALUES = ['6', '7', '8', '9A', '9B', '10A', '10B'];

    var state = { mcq: [], structured: [], essays: [] };
    var limits = { mcq: 5, structured: 2, essays: 3 };

    function paintCount(key){
      var el = document.querySelector('[data-pick="' + key + '"]');
      if(!el) return;
      var n = state[key].length, max = limits[key];
      el.textContent = n + ' / ' + max + ' selected';
      el.classList.toggle('full', n >= max);
    }
    function buildGrid(el, values, key, wide){
      if(!el) return;
      el.innerHTML = values.map(function(v){
        return '<button type="button" class="q-chip' + (wide ? ' wide' : '') + '" data-val="' + v + '">' + v + '</button>';
      }).join('');
      el.querySelectorAll('.q-chip').forEach(function(chip){
        chip.addEventListener('click', function(){
          var v = chip.dataset.val;
          var arr = state[key];
          var idx = arr.indexOf(v);
          if(idx >= 0){
            arr.splice(idx, 1);
            chip.classList.remove('on');
          } else {
            if(arr.length >= limits[key]){
              if(window.__toast) window.__toast('Max ' + limits[key] + ' for this section', true);
              return;
            }
            arr.push(v);
            chip.classList.add('on');
          }
          paintCount(key);
        });
      });
    }

    function renderEmpty(){
      host.innerHTML = '<div class="empty" style="max-width:720px">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.4" stroke-linecap="round"><path d="M9 11l3 3 8-8"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>' +
        '<h3>No active paper yet.</h3>' +
        '<p>Sir will announce the paper soon</p></div>';
    }

    function renderPaper(paper){
      host.innerHTML =
        '<div style="margin-bottom:clamp(24px,3vh,36px)">' +
          '<h2 class="sec-title">Which questions were <em>hardest</em>?</h2>' +
          '<p class="sec-lead">Just finished the paper? Flag the questions that gave you the most trouble. Sir reviews the hardest and most-flagged questions first in the next discussion class.</p>' +
          '<div class="paper-active-chip"><span class="dot"></span> Now reviewing · <b>' + (paper.name || 'Untitled Paper') + '</b></div>' +
        '</div>' +
        '<div class="community-card paper-card">' +
          '<div class="community-head">' +
            '<div class="community-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg></div>' +
            '<div class="community-head-txt"><h3>Paper <em>Feedback</em></h3><p>MCQ · Structured · Essay</p></div>' +
          '</div>' +
          '<form id="formPaper" novalidate>' +
            '<div class="paper-meta">' +
              '<div class="field"><label for="pName">Your Name</label><input type="text" id="pName" placeholder="Optional — anonymous is fine"></div>' +
              '<div class="field"><label for="pBatch">Batch</label><select id="pBatch"><option value="2028">2028</option><option value="2027">2027</option><option value="2026" selected>2026 / 2027 Revision</option><option value="Past Student">Past Student</option></select></div>' +
            '</div>' +
            '<div class="paper-block">' +
              '<div class="paper-block-head"><h4>MCQ — Hardest Questions</h4><span class="paper-pick" data-pick="mcq">0 / 5 selected</span></div>' +
              '<p class="paper-hint">Tap the MCQ numbers that gave you the most trouble (up to 5).</p>' +
              '<div class="q-grid is-mcq" id="mcqGrid"></div>' +
            '</div>' +
            '<div class="paper-block">' +
              '<div class="paper-block-head"><h4>Structured Essay — Hardest</h4><span class="paper-pick" data-pick="structured">0 / 2 selected</span></div>' +
              '<p class="paper-hint">Pick up to 2 structured essay questions.</p>' +
              '<div class="q-grid is-essay" id="structGrid"></div>' +
            '</div>' +
            '<div class="paper-block">' +
              '<div class="paper-block-head"><h4>Essay — Hardest</h4><span class="paper-pick" data-pick="essays">0 / 3 selected</span></div>' +
              '<p class="paper-hint">Pick up to 3 essay questions.</p>' +
              '<div class="q-grid is-essay" id="essayGrid"></div>' +
            '</div>' +
            '<div class="field full" style="margin-top:22px">' +
              '<label for="pComment">Anything else? (optional)</label>' +
              '<textarea id="pComment" placeholder="Which part confused you? Time management? A specific concept?"></textarea>' +
            '</div>' +
            '<div class="submit-row" style="margin-top:18px">' +
              '<div class="submit-note">Goes straight to <b>Sir</b> · Reviewed before the next discussion</div>' +
              '<button type="submit" class="submit-btn" data-cursor>' +
                '<span>Send Paper Feedback</span>' +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>' +
              '</button>' +
            '</div>' +
          '</form>' +
          '<div class="community-success" id="okPaper">' +
            '<div class="community-success-ico"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>' +
            '<h4>Feedback <em>received</em>.</h4>' +
            '<p>Thank you — Sir will go through the hardest questions first.</p>' +
            '<button type="button" class="community-again" data-again="paper" data-cursor>Send another</button>' +
          '</div>' +
        '</div>';

      buildGrid(document.getElementById('mcqGrid'), MCQ_VALUES, 'mcq', false);
      buildGrid(document.getElementById('structGrid'), STRUCT_VALUES, 'structured', true);
      buildGrid(document.getElementById('essayGrid'), ESSAY_VALUES, 'essays', true);
      paintCount('mcq'); paintCount('structured'); paintCount('essays');

      var form = document.getElementById('formPaper');
      if(!form) return;
      form.addEventListener('submit', function(e){
        e.preventDefault();
        if(!state.mcq.length && !state.structured.length && !state.essays.length){
          if(window.__toast) window.__toast('Pick at least one question', true);
          return;
        }
        var btn = form.querySelector('.submit-btn');
        var span = btn.querySelector('span');
        btn.disabled = true;
        if(span) span.textContent = 'Sending...';
        fetch('/api/paper-feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            paper_id: paper.id,
            name: document.getElementById('pName').value.trim(),
            batch: document.getElementById('pBatch').value,
            mcq: state.mcq.map(Number),
            structured: state.structured.map(Number),
            essays: state.essays,
            comment: document.getElementById('pComment').value.trim()
          })
        })
        .then(function(r){ return r.json().then(function(d){ return { ok: r.ok, data: d }; }); })
        .then(function(res){
          if(res.ok && res.data.ok){
            document.getElementById('okPaper').classList.add('on');
            form.style.display = 'none';
            if(window.__toast) window.__toast('Sent · ID #' + res.data.id);
          } else {
            if(window.__toast) window.__toast((res.data && res.data.error) || 'Failed', true);
            btn.disabled = false;
            if(span) span.textContent = 'Send Paper Feedback';
          }
        })
        .catch(function(){
          if(window.__toast) window.__toast('Network error', true);
          btn.disabled = false;
          if(span) span.textContent = 'Send Paper Feedback';
        });
      });

      var again = host.querySelector('[data-again="paper"]');
      if(again){
        again.addEventListener('click', function(){
          state.mcq = []; state.structured = []; state.essays = [];
          host.querySelectorAll('.q-chip.on').forEach(function(c){ c.classList.remove('on'); });
          paintCount('mcq'); paintCount('structured'); paintCount('essays');
        });
      }
    }

    fetch('/api/paper/current').then(function(r){ return r.json(); }).then(function(d){
      if(d && d.ok && d.paper){ renderPaper(d.paper); }
      else { renderEmpty(); }
    }).catch(function(){ renderEmpty(); });
  });
})();
"""


# ============================================================
# MAGIC HUB
# ============================================================
MAGIC_HUB_CSS = r"""
.hub-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:22px;margin-top:clamp(40px,6vh,70px)}
@media(max-width:800px){.hub-grid{grid-template-columns:1fr}}
.hub-card{position:relative;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:linear-gradient(160deg,rgba(245,196,81,.05),transparent 55%),#0A0A0C;padding:clamp(28px,3.4vw,44px);transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s;display:flex;flex-direction:column;gap:18px;min-height:300px}
.hub-card::before{content:'';position:absolute;top:0;left:15%;right:15%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-bright),transparent)}
.hub-card:hover{border-color:rgba(245,196,81,.55);transform:translateY(-8px);background:linear-gradient(160deg,rgba(245,196,81,.09),transparent 55%),#0E0E10}
.hub-card:hover .hub-arrow{transform:translate(6px,-6px);color:var(--gold)}
.hub-card:hover .hub-icon{background:var(--gold);border-color:var(--gold)}
.hub-card:hover .hub-icon svg{stroke:#0a0a0a}
.hub-icon{width:60px;height:60px;border:1px solid rgba(245,196,81,.35);border-radius:14px;display:grid;place-items:center;transition:background .5s,border-color .5s;flex-shrink:0;background:radial-gradient(circle at 30% 30%,rgba(245,196,81,.1),transparent 65%)}
.hub-icon svg{width:26px;height:26px;stroke:var(--gold);transition:stroke .5s}
.hub-num{position:absolute;top:24px;right:26px;font-family:var(--font-m);font-size:10px;letter-spacing:.22em;color:var(--muted-2)}
.hub-card h3{font-size:clamp(1.5rem,2.6vw,2.2rem);font-weight:600;letter-spacing:-.035em;line-height:1.1;margin-top:auto}
.hub-card h3 em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.hub-card p{font-size:13.5px;color:var(--muted);font-weight:300;line-height:1.75;max-width:44ch}
.hub-foot{display:flex;justify-content:space-between;align-items:center;padding-top:20px;border-top:1px solid var(--line-soft);margin-top:auto}
.hub-tag{font-family:var(--font-m);font-size:9.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted-2)}
.hub-arrow{font-size:18px;color:var(--muted-2);transition:transform .5s var(--ease),color .4s}
"""

MAGIC_HUB_BODY = """
<section class="magic-hero">
  <div class="magic-hero-inner">
    <div class="kicker">✦ A SEPARATE WORLD</div>
    <h1>Welcome to <em>Magic</em>.</h1>
    <p>A dedicated space built for learning, momentum, and going deeper. Everything a student needs outside the classroom — class recordings, motivation reels, live simulations, and interactive visualizations — with its own clean interface.</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(50px,7vh,90px)">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">01</span><span class="sec-label">Choose Your Path</span><span class="sec-rule"></span></div>
    <div class="hub-grid" data-reveal>
      <a href="/magic/sessions" class="hub-card" data-cursor>
        <span class="hub-num">01 / 04</span>
        <div class="hub-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="14" rx="3"/><path d="M10 11l5 3-5 3v-6z"/><path d="M8 2h8"/></svg></div>
        <h3>Sessions <em>from Sir</em></h3>
        <p>Every published class recording, paper discussion and theory walkthrough — laid out in one clean hub. Click any card to play.</p>
        <div class="hub-foot"><span class="hub-tag">YouTube Library</span><span class="hub-arrow">↗</span></div>
      </a>
      <a href="/magic/from-sir" class="hub-card" data-cursor>
        <span class="hub-num">02 / 04</span>
        <div class="hub-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
        <h3>From <em>Sir</em></h3>
        <p>Short, sharp, and straight from the source. Vertical scroll — like TikTok — through Sir's motivational reels. Scroll up or down to move between clips.</p>
        <div class="hub-foot"><span class="hub-tag">TikTok Feed</span><span class="hub-arrow">↗</span></div>
      </a>
      <a href="/magic/simulations" class="hub-card" data-cursor>
        <span class="hub-num">03 / 04</span>
        <div class="hub-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/></svg></div>
        <h3>Simulations</h3>
        <p>25+ interactive simulations across Mechanics, Fields, Current Electricity and Electronics. Powered by PhET — drag, tune, and watch the laws of physics respond in real time.</p>
        <div class="hub-foot"><span class="hub-tag">25+ Live Sims</span><span class="hub-arrow">↗</span></div>
      </a>
      <a href="/magic/visualizations" class="hub-card" data-cursor>
        <span class="hub-num">04 / 04</span>
        <div class="hub-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="10" ry="4.4"/><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(120 12 12)"/></svg></div>
        <h3>Visualizations</h3>
        <p>Six hand-built 3D visualizations — one per major topic. Electric, magnetic and gravitational fields, wave interference, projectile motion and the simple pendulum.</p>
        <div class="hub-foot"><span class="hub-tag">6 × 3D Scenes</span><span class="hub-arrow">↗</span></div>
      </a>
    </div>
  </div>
</section>
"""


# ============================================================
# SIMULATIONS
# ============================================================
SIMS_CSS = r"""
.sim-cat-section{margin-bottom:clamp(38px,5vh,60px)}
.sim-cat-section:last-child{margin-bottom:0}
.sim-cat-head{display:flex;align-items:center;gap:16px;margin-bottom:26px;flex-wrap:wrap}
.sim-cat-num{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;color:var(--gold);border:1px solid var(--line);border-radius:100px;padding:5px 12px;flex-shrink:0}
.sim-cat-title{font-size:clamp(1.3rem,2.4vw,1.9rem);font-weight:600;letter-spacing:-.03em;color:var(--text)}
.sim-cat-title em{font-family:var(--font-s);font-style:italic;font-weight:400;color:var(--gold)}
.sim-cat-rule{flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent);min-width:30px}
.sim-cat-count{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);flex-shrink:0}
.sims-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:1080px){.sims-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.sims-grid{grid-template-columns:1fr}}
.sim{position:relative;border:1px solid var(--line-soft);border-radius:8px;overflow:hidden;background:var(--surface);cursor:pointer;text-align:left;padding:26px 24px 24px;min-height:210px;display:flex;flex-direction:column;transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s}
.sim::before{content:'';position:absolute;inset:0;background:radial-gradient(circle at 100% 0%,rgba(245,196,81,.14),transparent 60%);opacity:0;transition:opacity .6s}
.sim::after{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);transform:scaleX(0);transition:transform .7s var(--ease)}
.sim:hover{border-color:rgba(245,196,81,.42);background:var(--surface-2);transform:translateY(-6px)}
.sim:hover::before{opacity:1}.sim:hover::after{transform:scaleX(1)}
.sim:hover .sim-play{background:var(--gold);border-color:var(--gold);color:#0a0a0a;transform:scale(1.08) rotate(0)}
.sim:hover .sim-ico{color:var(--gold);transform:translateY(-3px) rotate(-6deg)}
.sim-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:auto}
.sim-ico{width:48px;height:48px;display:grid;place-items:center;color:var(--muted);transition:color .5s,transform .6s var(--ease)}
.sim-ico svg{width:28px;height:28px}
.sim-play{width:36px;height:36px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;flex-shrink:0;color:var(--gold);transition:background .5s,border-color .5s,color .4s,transform .55s var(--ease);transform:rotate(-12deg)}
.sim-play svg{width:13px;height:13px}
.sim-t{font-size:clamp(1rem,1.35vw,1.15rem);font-weight:600;letter-spacing:-.025em;line-height:1.28;margin:22px 0 6px;position:relative;z-index:2}
.sim-d{font-size:12.5px;color:var(--muted);line-height:1.65;font-weight:300;position:relative;z-index:2}
"""

SIMS_BODY = """
<section class="magic-hero">
  <div class="magic-hero-inner">
    <div class="kicker">✦ 03 / 04</div>
    <h1>Play with the <em>physics</em>.</h1>
    <p>25+ live simulations across every A/L topic. Powered by PhET — every simulation runs in a full-screen modal.</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(50px,7vh,90px)">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">01</span><span class="sec-label">Simulations</span><span class="sec-rule"></span></div>
    <div id="simsRoot"></div>
  </div>
</section>
"""

SIMS_JS = r"""
(function(){
  'use strict';
  var SIMS = [
    { cat: 'mechanics', name: 'Projectile Motion', slug: 'projectile-motion', desc: 'Launch objects and study trajectory, range and air resistance.', icon: '<path d="M4 18c4-10 10-14 16-14"/><circle cx="4" cy="18" r="1.4"/><path d="M15 4h5v5"/>' },
    { cat: 'mechanics', name: 'Forces and Motion: Basics', slug: 'forces-and-motion-basics', desc: "Push a crate, tune friction, and watch Newton's laws play out.", icon: '<path d="M3 12h12M12 8l4 4-4 4M18 5v14"/>' },
    { cat: 'mechanics', name: 'Energy Skate Park: Basics', slug: 'energy-skate-park-basics', desc: 'Track kinetic and potential energy as a skater rides ramps and loops.', icon: '<path d="M3 18c3-2 4-12 8-12s5 10 8 12"/><circle cx="12" cy="8" r="1.5"/>' },
    { cat: 'mechanics', name: 'Pendulum Lab', slug: 'pendulum-lab', desc: 'Swing a pendulum and study period, gravity, length and mass.', icon: '<circle cx="12" cy="4" r="1.5"/><path d="M12 5.5v8"/><circle cx="12" cy="16" r="2.5"/>' },
    { cat: 'mechanics', name: 'Masses and Springs', slug: 'masses-and-springs', desc: 'Hang masses, change spring constants, and observe SHM.', icon: '<path d="M6 3v18M6 6h3M6 10h3M6 14h3M6 18h3"/><path d="M14 6h6M14 18h6"/>' },
    { cat: 'mechanics', name: 'Collision Lab', slug: 'collision-lab', desc: 'Explore elastic and inelastic collisions in 1D and 2D.', icon: '<circle cx="7" cy="12" r="4"/><circle cx="17" cy="12" r="4"/>' },
    { cat: 'mechanics', name: "Hooke's Law", slug: 'hookes-law', desc: 'Stretch springs and see force-extension graphs live.', icon: '<path d="M6 3v4l4 2-4 2 4 2-4 2 4 2v4"/>' },
    { cat: 'mechanics', name: 'The Ramp', slug: 'the-ramp', desc: 'Slide objects down an inclined plane and study forces.', icon: '<path d="M3 19L20 19 3 5z"/>' },
    { cat: 'fields', name: 'Charges and Fields', slug: 'charges-and-fields', desc: 'Place charges and visualize electric field lines and equipotentials.', icon: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>' },
    { cat: 'fields', name: 'Magnet and Compass', slug: 'magnet-and-compass', desc: 'See how a bar magnet shapes the magnetic field around it.', icon: '<path d="M6 3v18M18 3v18"/><rect x="4" y="8" width="4" height="8" rx="1"/><rect x="16" y="8" width="4" height="8" rx="1"/>' },
    { cat: 'fields', name: "Faraday's Electromagnetic Lab", slug: 'faradays-electromagnetic-lab', desc: "Explore Faraday's law with magnets, coils, pickups and transformers.", icon: '<circle cx="10" cy="12" r="4"/><path d="M16 6c4 3 4 9 0 12M19 3c6 5 6 13 0 18"/>' },
    { cat: 'fields', name: 'Gravity and Orbits', slug: 'gravity-and-orbits', desc: 'Move the Sun, Earth and Moon to see how gravity and orbits change.', icon: '<circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="9" ry="5"/><ellipse cx="12" cy="12" rx="9" ry="5" transform="rotate(60 12 12)"/>' },
    { cat: 'fields', name: 'Electric Field of Dreams', slug: 'electric-field-of-dreams', desc: 'Drag charges and watch vector fields update in real time.', icon: '<path d="M4 12h6M14 12h6"/><circle cx="12" cy="12" r="2"/>' },
    { cat: 'fields', name: "Faraday's Law", slug: 'faradays-law', desc: 'Move a magnet through a coil and watch the induced voltage spike.', icon: '<path d="M4 8h4M4 12h4M4 16h4M16 8h4M16 12h4M16 16h4"/><path d="M10 12h4"/>' },
    { cat: 'fields', name: 'Capacitor Lab: Basics', slug: 'capacitor-lab-basics', desc: 'Adjust plate area and separation, and observe capacitance.', icon: '<path d="M9 4v16M15 4v16M3 12h6M15 12h6"/>' },
    { cat: 'current', name: 'Circuit Construction Kit: DC', slug: 'circuit-construction-kit-dc', desc: 'Build DC circuits with batteries, bulbs and resistors.', icon: '<rect x="3" y="9" width="18" height="6" rx="1"/><path d="M7 12h2M12 12h2M17 12h.01"/>' },
    { cat: 'current', name: 'Resistance in a Wire', slug: 'resistance-in-a-wire', desc: 'Change length, area and resistivity and observe resistance.', icon: '<path d="M3 12h3l2-4 3 8 3-8 2 4h5"/>' },
    { cat: 'current', name: "Ohm's Law", slug: 'ohms-law', desc: 'Adjust voltage and resistance and see current respond instantly.', icon: '<path d="M3 12h4l2-6 4 12 2-6h6"/>' },
    { cat: 'current', name: 'Battery-Resistor Circuit', slug: 'battery-resistor-circuit', desc: 'A simplified circuit showing voltage, current and resistance.', icon: '<rect x="3" y="10" width="10" height="4" rx="1"/><path d="M17 8v8M20 8v8"/>' },
    { cat: 'current', name: 'Capacitor Lab', slug: 'capacitor-lab', desc: 'Full capacitor lab with dielectric and stored energy.', icon: '<path d="M8 4v16M16 4v16M3 12h5M16 12h5"/>' },
    { cat: 'electronics', name: 'Semiconductors', slug: 'semiconductors', desc: 'Dope silicon with donors and acceptors, and build a diode.', icon: '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 5v14M15 5v14"/>' },
    { cat: 'electronics', name: 'Signal Circuit', slug: 'signal-circuit', desc: 'Control a signal circuit with switches and gates.', icon: '<path d="M3 12h4l2-4v8l3-10v14l3-8v4h6"/>' },
    { cat: 'electronics', name: 'Circuit Construction Kit: AC', slug: 'circuit-construction-kit-ac', desc: 'Build AC circuits with inductors, capacitors and oscilloscopes.', icon: '<path d="M3 12c3-6 6 6 9 0s6-6 9 0"/>' },
    { cat: 'electronics', name: 'Photoelectric Effect', slug: 'photoelectric', desc: 'Shine light on metal and observe electron emission.', icon: '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1"/>' },
    { cat: 'electronics', name: 'Neon Lights & Discharge Lamps', slug: 'neon-lights-and-other-discharge-lamps', desc: 'Excite gas atoms and watch them emit their colours.', icon: '<path d="M9 3h6v8a3 3 0 0 1-1 2.2V19h-4v-5.8A3 3 0 0 1 9 11z"/>' }
  ];
  var CATS = [
    { id: 'mechanics', label: 'Mechanics', num: '01' },
    { id: 'fields', label: 'Fields', num: '02' },
    { id: 'current', label: 'Current Electricity', num: '03' },
    { id: 'electronics', label: 'Electronics', num: '04' }
  ];
  var BASE = 'https://phet.colorado.edu/sims/html/';
  var simsRoot = document.getElementById('simsRoot');
  if(!simsRoot) return;
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.08 });
  CATS.forEach(function(c){
    var list = SIMS.filter(function(s){ return s.cat === c.id; });
    if(!list.length) return;
    var section = document.createElement('div');
    section.className = 'sim-cat-section';
    section.setAttribute('data-reveal', '');
    section.innerHTML =
      '<div class="sim-cat-head"><span class="sim-cat-num">' + c.num + ' / ' + CATS.length + '</span>' +
      '<span class="sim-cat-title">' + c.label + '</span><span class="sim-cat-rule"></span>' +
      '<span class="sim-cat-count">' + list.length + ' Simulations</span></div>' +
      '<div class="sims-grid"></div>';
    var grid = section.querySelector('.sims-grid');
    list.forEach(function(s){
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'sim';
      btn.setAttribute('data-cursor', '');
      btn.innerHTML =
        '<div class="sim-top">' +
          '<div class="sim-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">' + s.icon + '</svg></div>' +
          '<div class="sim-play"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 5v14l11-7z"/></svg></div>' +
        '</div>' +
        '<div class="sim-t">' + s.name + '</div>' +
        '<div class="sim-d">' + s.desc + '</div>';
      btn.addEventListener('click', function(){
        window.__openModal(s.name, BASE + s.slug + '/latest/' + s.slug + '_en.html');
      });
      grid.appendChild(btn);
    });
    simsRoot.appendChild(section);
    io.observe(section);
  });
})();
"""


# ============================================================
# SESSIONS
# ============================================================
SESSIONS_CSS = r"""
.session-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
@media(max-width:1080px){.session-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.session-grid{grid-template-columns:1fr}}
.session-card{position:relative;border:1px solid var(--line-soft);border-radius:8px;overflow:hidden;background:var(--surface);cursor:pointer;text-align:left;transition:border-color .55s var(--ease),transform .55s var(--ease),background .55s;display:flex;flex-direction:column}
.session-card:hover{border-color:rgba(245,196,81,.42);background:var(--surface-2);transform:translateY(-6px)}
.session-thumb{position:relative;aspect-ratio:16/9;overflow:hidden;background:#0C0C0E}
.session-thumb img{width:100%;height:100%;object-fit:cover;transition:transform .9s var(--ease)}
.session-card:hover .session-thumb img{transform:scale(1.06)}
.session-thumb::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,transparent 45%,rgba(7,7,8,.65) 100%);pointer-events:none}
.session-play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:64px;height:64px;border-radius:50%;background:rgba(245,196,81,.92);color:#0a0a0a;display:grid;place-items:center;z-index:2;box-shadow:0 12px 40px rgba(245,196,81,.4);transition:transform .5s var(--ease)}
.session-card:hover .session-play{transform:translate(-50%,-50%) scale(1.1)}
.session-play svg{width:22px;height:22px;margin-left:2px}
.session-meta{position:absolute;left:0;right:0;bottom:0;padding:16px 18px;z-index:3;display:flex;align-items:center;gap:10px;font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:rgba(237,234,228,.85)}
.session-meta b{color:var(--gold);font-weight:400}
.session-body{padding:22px 22px 24px;display:flex;flex-direction:column;gap:10px;flex:1}
.session-t{font-size:1.1rem;font-weight:600;letter-spacing:-.025em;line-height:1.3;color:var(--text);transition:color .35s}
.session-card:hover .session-t{color:var(--gold)}
.session-d{font-family:var(--sinhala);font-size:12.8px;line-height:1.75;color:var(--muted);font-weight:300;flex:1;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.session-foot{display:flex;justify-content:space-between;align-items:center;padding-top:14px;border-top:1px solid var(--line-soft);font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2)}
.session-foot .go{color:var(--gold);transition:transform .4s var(--ease)}
.session-card:hover .session-foot .go{transform:translateX(4px)}
"""

SESSIONS_BODY = """
<section class="magic-hero">
  <div class="magic-hero-inner">
    <div class="kicker">✦ 01 / 04</div>
    <h1>Sessions from <em>Sir</em>.</h1>
    <p>Every published class recording, paper discussion and theory walkthrough — laid out in one clean hub. Click any card to play.</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(50px,7vh,90px)">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">01</span><span class="sec-label">Library</span><span class="sec-rule"></span></div>
    <div id="sessionsRoot" class="session-grid"></div>
  </div>
</section>
"""

SESSIONS_JS = r"""
(function(){
  'use strict';
  var root = document.getElementById('sessionsRoot');
  if(!root) return;
  function ytId(url){
    if(!url) return '';
    var m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{6,})/);
    return m ? m[1] : '';
  }
  fetch('/api/sessions').then(function(r){ return r.json(); }).then(function(d){
    var items = (d && d.items) || [];
    if(!items.length){
      root.innerHTML = '<div class="empty" style="grid-column:1/-1"><h3>No sessions yet.</h3><p>Check back soon — Sir is uploading</p></div>';
      return;
    }
    root.innerHTML = items.map(function(s){
      var id = ytId(s.youtube_url);
      var thumb = id ? 'https://img.youtube.com/vi/' + id + '/maxresdefault.jpg' : '';
      var date = s.created_at ? new Date(s.created_at.replace(' ', 'T')).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : '';
      return '<article class="session-card" data-vid="' + id + '">' +
        '<div class="session-thumb">' +
          (thumb ? '<img src="' + thumb + '" alt="" loading="lazy" onerror="this.src=\'https://img.youtube.com/vi/' + id + '/hqdefault.jpg\'">' : '') +
          '<div class="session-play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div>' +
          '<div class="session-meta"><b>●</b> Class Session</div>' +
        '</div>' +
        '<div class="session-body">' +
          '<div class="session-t">' + (s.title || 'Untitled Session') + '</div>' +
          '<div class="session-d">' + (s.description || '') + '</div>' +
          '<div class="session-foot"><span>' + date + '</span><span class="go">Play ↗</span></div>' +
        '</div>' +
      '</article>';
    }).join('');
    root.querySelectorAll('.session-card').forEach(function(card){
      card.addEventListener('click', function(){
        var id = card.dataset.vid;
        if(!id) return;
        var title = card.querySelector('.session-t').textContent;
        window.__openModal(title, 'https://www.youtube.com/embed/' + id + '?autoplay=1&rel=0');
      });
    });
  }).catch(function(){
    root.innerHTML = '<div class="empty" style="grid-column:1/-1"><h3>Could not load</h3><p>Check your connection</p></div>';
  });
})();
"""


# ============================================================
# FROM SIR (TikTok feed)
# ============================================================
FROMSIR_CSS = r"""
.feed{height:calc(100vh - 240px);min-height:560px;overflow-y:auto;scroll-snap-type:y mandatory;scrollbar-width:none;-ms-overflow-style:none;background:#050506;position:relative;border:1px solid var(--line);border-radius:12px;margin-top:8px}
.feed::-webkit-scrollbar{display:none}
.feed-item{height:100%;min-height:560px;scroll-snap-align:start;scroll-snap-stop:always;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;padding:20px}
.feed-item::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(245,196,81,.08),transparent 60%);pointer-events:none}
.feed-inner{position:relative;z-index:2;width:100%;max-width:420px;display:flex;flex-direction:column;gap:14px}
.feed-video{position:relative;width:100%;aspect-ratio:9/16;background:#000;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 30px 90px -30px rgba(0,0,0,.9)}
.feed-video iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#000}
.feed-meta{padding:0 6px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.feed-title{font-size:.98rem;font-weight:500;letter-spacing:-.015em;color:var(--text);line-height:1.35;flex:1}
.feed-tag{font-family:var(--font-m);font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(245,196,81,.3);border-radius:100px;padding:5px 10px;flex-shrink:0}
.feed-hint{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);font-family:var(--font-m);font-size:9.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted-2);display:flex;align-items:center;gap:10px;z-index:3;pointer-events:none;opacity:.7;animation:hintFade 3s ease-in-out infinite}
.feed-hint .chev{animation:hintBounce 1.6s ease-in-out infinite}
@keyframes hintFade{0%,100%{opacity:.35}50%{opacity:.85}}
@keyframes hintBounce{0%,100%{transform:translateY(0)}50%{transform:translateY(4px)}}
.feed-loading{height:100%;display:grid;place-items:center;gap:16px;color:var(--muted-2);font-family:var(--font-m);font-size:10px;letter-spacing:.3em;text-transform:uppercase;padding:60px 20px;text-align:center}
.feed-loading .sp{width:32px;height:32px;border:1px solid rgba(245,196,81,.2);border-top-color:var(--gold);border-radius:50%;animation:spin 1s linear infinite;margin:0 auto}
.feed-loading .msg{font-family:var(--font-s);font-style:italic;font-size:1.4rem;color:var(--gold);letter-spacing:0;text-transform:none;line-height:1.4}
@media(max-width:640px){
  .feed{height:calc(100vh - 200px);min-height:520px}
  .feed-item{padding:14px}
  .feed-inner{max-width:340px}
}
"""

FROMSIR_BODY = """
<section class="magic-hero">
  <div class="magic-hero-inner">
    <div class="kicker">✦ 02 / 04</div>
    <h1>From <em>Sir</em>.</h1>
    <p>Short, sharp, and straight from the source. Vertical scroll — like TikTok — through Sir's motivational reels.</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(40px,5vh,60px)">
  <div class="wrap">
    <div class="feed" id="feed">
      <div class="feed-loading"><div class="sp"></div><div>Loading feed</div></div>
    </div>
  </div>
</section>
"""

FROMSIR_JS = r"""
(function(){
  'use strict';
  var feed = document.getElementById('feed');
  if(!feed) return;
  function ttId(url){
    if(!url) return '';
    var m = url.match(/\/video\/(\d+)/);
    if(m) return m[1];
    m = url.match(/(\d{15,25})/);
    return m ? m[1] : '';
  }
  fetch('/api/motivations').then(function(r){ return r.json(); }).then(function(d){
    var items = (d && d.items) || [];
    if(!items.length){
      feed.innerHTML = '<div class="feed-loading"><div style="max-width:400px"><div class="msg">Nothing here yet.</div><div style="margin-top:14px">Sir is filming — check back</div></div></div>';
      return;
    }
    feed.innerHTML = items.map(function(m, i){
      var id = ttId(m.tiktok_url);
      return '<div class="feed-item">' +
        '<div class="feed-inner">' +
          '<div class="feed-video">' +
            '<iframe src="https://www.tiktok.com/embed/v2/' + id + '" allowfullscreen scrolling="no" allow="encrypted-media;"></iframe>' +
          '</div>' +
          '<div class="feed-meta">' +
            '<div class="feed-title">' + (m.title || 'Motivation') + '</div>' +
            '<div class="feed-tag">From Sir</div>' +
          '</div>' +
        '</div>' +
        (i === 0 ? '<div class="feed-hint"><span class="chev">▲</span> Scroll for more <span class="chev" style="animation-delay:.4s">▼</span></div>' : '') +
      '</div>';
    }).join('');
  }).catch(function(){
    feed.innerHTML = '<div class="feed-loading"><div>Could not load feed</div></div>';
  });
})();
"""


# ============================================================
# VISUALIZATIONS
# ============================================================
VIZ_CSS = r"""
.viz-panel{position:relative;border:1px solid var(--line-soft);border-radius:8px;overflow:hidden;background:radial-gradient(ellipse at 50% 100%,rgba(245,196,81,.05),transparent 65%),#0A0A0C;aspect-ratio:21/9;min-height:400px}
@media(max-width:900px){.viz-panel{aspect-ratio:4/3;min-height:0}}
#viz-canvas{position:absolute;inset:0;width:100%;height:100%}
.viz-ui{position:absolute;inset:0;z-index:3;pointer-events:none;display:flex;flex-direction:column;justify-content:space-between;padding:clamp(18px,2.4vw,28px)}
.viz-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.viz-label{font-family:var(--font-m);font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--muted-2)}
.viz-label b{color:var(--gold);font-weight:400}
.viz-tabs{display:flex;gap:6px;pointer-events:auto;flex-wrap:wrap;justify-content:flex-end;max-width:70%}
.viz-btn{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;padding:8px 14px;border:1px solid var(--line-soft);border-radius:100px;color:var(--muted);transition:color .4s,border-color .4s,background .4s,box-shadow .4s;white-space:nowrap}
.viz-btn.on{color:#0a0a0a;background:var(--gold);border-color:var(--gold);box-shadow:0 0 24px -4px rgba(245,196,81,.5)}
.viz-btn:hover:not(.on){color:var(--gold);border-color:var(--line)}
.viz-bottom{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}
.viz-title{font-size:clamp(1.3rem,2.6vw,2.1rem);font-weight:600;letter-spacing:-.035em;line-height:1.1}
.viz-title em{font-family:var(--font-s);font-style:italic;font-weight:400;background:linear-gradient(100deg,var(--gold-deep),var(--gold-bright),var(--gold-deep));background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;animation:shine 4.5s linear infinite}
.viz-desc{font-family:var(--font-m);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted-2);text-align:right;max-width:42ch;line-height:1.9}
@media(max-width:640px){
  .viz-tabs{max-width:100%;justify-content:flex-start}
  .viz-btn{padding:7px 11px;font-size:9px;letter-spacing:.14em}
  .viz-title{font-size:1.15rem}
  .viz-desc{font-size:9px;text-align:left;max-width:none}
  .viz-bottom{flex-direction:column;align-items:flex-start;gap:10px}
}
"""

VIZ_BODY = """
<section class="magic-hero">
  <div class="magic-hero-inner">
    <div class="kicker">✦ 04 / 04</div>
    <h1>See the field <em>live</em>.</h1>
    <p>Six hand-built 3D visualizations — one per major topic. Switch modes to explore electric, magnetic and gravitational fields, wave interference, projectile motion and the simple pendulum.</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(50px,7vh,90px)">
  <div class="wrap">
    <div class="sec-head" data-reveal><span class="sec-num">01</span><span class="sec-label">Field Visualizer</span><span class="sec-rule"></span></div>
    <div class="viz-panel" data-reveal>
      <canvas id="viz-canvas"></canvas>
      <div class="viz-ui">
        <div class="viz-top">
          <div class="viz-label">Fig. <b>01</b> — 3D Scene</div>
          <div class="viz-tabs" id="vizTabs">
            <button class="viz-btn on" data-viz="electric" data-cursor>Electric</button>
            <button class="viz-btn" data-viz="magnetic" data-cursor>Magnetic</button>
            <button class="viz-btn" data-viz="gravity" data-cursor>Gravity</button>
            <button class="viz-btn" data-viz="wave" data-cursor>Wave</button>
            <button class="viz-btn" data-viz="projectile" data-cursor>Projectile</button>
            <button class="viz-btn" data-viz="pendulum" data-cursor>Pendulum</button>
          </div>
        </div>
        <div class="viz-bottom">
          <div class="viz-title" id="vizTitle"><em>Electric Field</em></div>
          <div class="viz-desc" id="vizDesc">Radial field lines from a point charge — Coulomb's law in motion.</div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

VIZ_JS = r"""
(function(){
  'use strict';
  var vizBtns = document.querySelectorAll('.viz-btn');
  var vizTitle = document.getElementById('vizTitle');
  var vizDesc = document.getElementById('vizDesc');
  var META = {
    electric:   { title: '<em>Electric Field</em>',    desc: "Radial field lines from a point charge — Coulomb's law in motion." },
    magnetic:   { title: '<em>Magnetic Field</em>',    desc: "Dipole field lines looping from north to south — Ampère's model." },
    gravity:    { title: '<em>Gravitational Field</em>', desc: 'Spacetime curvature well — mass bends the grid around it.' },
    wave:       { title: '<em>Wave Interference</em>', desc: 'Two coherent sources create constructive and destructive patterns.' },
    projectile: { title: '<em>Projectile Motion</em>',  desc: 'Launch angle and velocity define the parabolic trajectory.' },
    pendulum:   { title: '<em>Simple Pendulum</em>',    desc: 'Period depends only on length and gravity — never on mass.' }
  };
  window.__setVizMode = function(mode){
    vizBtns.forEach(function(b){ b.classList.toggle('on', b.dataset.viz === mode); });
    if(META[mode]){ vizTitle.innerHTML = META[mode].title; vizDesc.textContent = META[mode].desc; }
    if(window.__vizCycle) window.__vizCycle(mode);
  };
  vizBtns.forEach(function(b){
    b.addEventListener('click', function(){ window.__setVizMode(b.dataset.viz); });
  });
})();
"""


# ============================================================
# 3D MODULES
# ============================================================
HERO_MODULE = r"""
import * as THREE from 'three';
var isMobile = window.matchMedia('(max-width: 900px)').matches;
function glowTex(){
  var s = 128; var c = document.createElement('canvas');
  c.width = c.height = s;
  var ctx = c.getContext('2d');
  var g = ctx.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  g.addColorStop(0,'rgba(255,236,186,1)');
  g.addColorStop(0.18,'rgba(245,196,81,0.75)');
  g.addColorStop(0.45,'rgba(245,196,81,0.16)');
  g.addColorStop(1,'rgba(245,196,81,0)');
  ctx.fillStyle = g; ctx.fillRect(0,0,s,s);
  return new THREE.CanvasTexture(c);
}
var GLOW = glowTex();
(function heroAtom(){
  var canvas = document.getElementById('hero-canvas');
  if(!canvas) return;
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.4 : 1.8));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  var scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x070708, 0.014);
  var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 300);
  camera.position.set(0, 2.6, 12.5);

  scene.add(new THREE.AmbientLight(0xffffff, 0.25));
  var coreLight = new THREE.PointLight(0xFFE39B, 55, 55, 1.6); coreLight.position.set(0, 0, 0); scene.add(coreLight);
  var coreLight2 = new THREE.PointLight(0xF5C451, 32, 45, 1.8); coreLight2.position.set(0, 0, 0); scene.add(coreLight2);
  var keyLight = new THREE.DirectionalLight(0xFFE39B, 0.55); keyLight.position.set(4, 5, 6); scene.add(keyLight);
  var fill = new THREE.DirectionalLight(0x6a5a2a, 0.35); fill.position.set(-5, 4, -6); scene.add(fill);

  /* STARS */
  var starCount = isMobile ? 400 : 850;
  var starGeo = new THREE.BufferGeometry();
  var pos = new Float32Array(starCount * 3);
  var col = new Float32Array(starCount * 3);
  var c1 = new THREE.Color(0xF5C451); var c2 = new THREE.Color(0xEDEAE4);
  for(var i = 0; i < starCount; i++){
    var r = 20 + Math.random()*60;
    var th = Math.random()*Math.PI*2;
    var ph = Math.acos(2*Math.random()-1);
    pos[i*3] = Math.sin(ph)*Math.cos(th)*r;
    pos[i*3+1] = Math.sin(ph)*Math.sin(th)*r*0.7;
    pos[i*3+2] = Math.cos(ph)*r - 20;
    var cc = Math.random() > 0.75 ? c1 : c2;
    var b = 0.3 + Math.random()*0.6;
    col[i*3] = cc.r*b; col[i*3+1] = cc.g*b; col[i*3+2] = cc.b*b;
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  starGeo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  var stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
    size: 0.09, vertexColors: true, transparent: true, opacity: 0.75,
    blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true
  }));
  scene.add(stars);

  /* ATOM */
  var atom = new THREE.Group();
  scene.add(atom);

  /* Nucleus — cluster of protons & neutrons */
  var nucleus = new THREE.Group();
  atom.add(nucleus);

  var protonMat = new THREE.MeshStandardMaterial({
    color: 0xF5C451, emissive: 0xF5C451, emissiveIntensity: 0.85,
    roughness: 0.35, metalness: 0.55
  });
  var neutronMat = new THREE.MeshStandardMaterial({
    color: 0x5F5F68, emissive: 0x2A2A32, emissiveIntensity: 0.5,
    roughness: 0.55, metalness: 0.45
  });

  var nucleonGeo = new THREE.SphereGeometry(0.17, 18, 18);
  var nucleonCount = isMobile ? 14 : 22;
  var nucleusRadius = 0.48;
  var nucleons = [];
  for(var n = 0; n < nucleonCount; n++){
    var isProton = (n % 2 === 0) ? Math.random() < 0.9 : Math.random() < 0.25;
    var mat = isProton ? protonMat : neutronMat;
    var mesh = new THREE.Mesh(nucleonGeo, mat);
    var thN = Math.random()*Math.PI*2;
    var phN = Math.acos(2*Math.random()-1);
    var rN = nucleusRadius * Math.cbrt(Math.random());
    mesh.position.set(
      Math.sin(phN)*Math.cos(thN)*rN,
      Math.sin(phN)*Math.sin(thN)*rN,
      Math.cos(phN)*rN
    );
    mesh.userData = { basePos: mesh.position.clone(), seed: Math.random()*Math.PI*2 };
    nucleus.add(mesh);
    nucleons.push(mesh);
  }

  var nucleusGlow = new THREE.Sprite(new THREE.SpriteMaterial({
    map: GLOW, color: 0xFFE39B, transparent: true,
    blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.95
  }));
  nucleusGlow.scale.set(3.0, 3.0, 1);
  nucleus.add(nucleusGlow);

  /* Orbits — 3 ellipses all sharing a common diameter, classic atom look */
  var orbitRingMat = new THREE.MeshBasicMaterial({
    color: 0xF5C451, transparent: true, opacity: 0.22,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
  });
  var orbitRingMat2 = orbitRingMat.clone(); orbitRingMat2.opacity = 0.16;
  var electronMat = new THREE.MeshBasicMaterial({ color: 0xFFF3D0 });

  var orbits = [];

  function makeOrbit(radius, rotX, rotY, speed, electronCount, ringOpacity){
    var outer = new THREE.Group();
    outer.rotation.set(rotX, rotY, 0);
    atom.add(outer);

    var ringMat = orbitRingMat.clone();
    ringMat.opacity = ringOpacity;
    var ring = new THREE.Mesh(
      new THREE.RingGeometry(radius - 0.008, radius + 0.008, 128),
      ringMat
    );
    outer.add(ring);

    var electrons = [];
    for(var k = 0; k < electronCount; k++){
      var e = new THREE.Mesh(new THREE.SphereGeometry(0.075, 14, 14), electronMat);
      var eGlow = new THREE.Sprite(new THREE.SpriteMaterial({
        map: GLOW, color: 0xFFE39B, transparent: true,
        blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.95
      }));
      eGlow.scale.set(0.85, 0.85, 1);
      e.add(eGlow);
      var startAngle = (k / electronCount) * Math.PI * 2;
      e.position.set(Math.cos(startAngle) * radius, Math.sin(startAngle) * radius, 0);
      outer.add(e);
      electrons.push({ mesh: e, angle: startAngle, speed: speed, radius: radius });
    }

    orbits.push({ group: outer, electrons: electrons });
  }

  var baseR = isMobile ? 1.85 : 2.15;
  makeOrbit(baseR,         0,             0,             0.55, 2, 0.24);
  makeOrbit(baseR * 1.1,   0,             Math.PI/3,     0.70, 2, 0.20);
  makeOrbit(baseR * 1.2,   0,            -Math.PI/3,     0.85, 2, 0.16);

  var targetX = 0, targetY = 0, targetScale = 1;
  function resize(){
    var w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w/h; camera.updateProjectionMatrix();
    var aspect = w/h;
    if(aspect > 1.15){
      targetX = Math.min(3.0, camera.aspect * 1.35); targetY = 0.4;
      targetScale = Math.min(1.05, aspect/1.9);
      camera.position.set(0, 2.4, 13);
      canvas.style.opacity = '1';
    } else {
      targetX = 0; targetY = 2.2; targetScale = 0.7;
      camera.position.set(0, 3.0, 14);
      canvas.style.opacity = '0.6';
    }
    atom.position.x = targetX; atom.position.y = targetY;
    atom.scale.setScalar(targetScale);
    camera.lookAt(targetX*0.4, targetY*0.4, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  var mx = 0, my = 0, tmx = 0, tmy = 0;
  window.addEventListener('mousemove', function(e){
    tmx = (e.clientX/window.innerWidth)*2 - 1;
    tmy = (e.clientY/window.innerHeight)*2 - 1;
  }, { passive: true });

  var scrollY = 0;
  window.addEventListener('scroll', function(){ scrollY = window.scrollY; }, { passive: true });

  var visible = true;
  var heroEl = document.getElementById('home');
  var vio = new IntersectionObserver(function(es){ visible = es[0].isIntersecting; }, { threshold: 0 });
  if(heroEl) vio.observe(heroEl);

  var clock = new THREE.Clock();
  var lastT = 0;

  function tick(){
    requestAnimationFrame(tick);
    if(!visible) return;
    var t = clock.getElapsedTime();
    var dt = t - lastT;
    lastT = t;
    if(dt > 0.1) dt = 0.1;

    mx += (tmx - mx)*0.05; my += (tmy - my)*0.05;

    /* Nucleus jiggle */
    for(var i = 0; i < nucleons.length; i++){
      var nu = nucleons[i];
      var bp = nu.userData.basePos;
      var sd = nu.userData.seed;
      nu.position.x = bp.x + Math.sin(t*1.4 + sd)*0.03;
      nu.position.y = bp.y + Math.cos(t*1.6 + sd)*0.03;
      nu.position.z = bp.z + Math.sin(t*1.2 + sd*1.3)*0.03;
    }
    nucleus.rotation.y = t*0.35;
    nucleus.rotation.x = Math.sin(t*0.3)*0.18;

    var pulse = 1 + Math.sin(t*1.6)*0.05;
    nucleusGlow.scale.set(3.0*pulse, 3.0*pulse, 1);
    nucleusGlow.material.opacity = 0.82 + Math.sin(t*2.2)*0.13;

    /* Electrons */
    for(var oi = 0; oi < orbits.length; oi++){
      var orbit = orbits[oi];
      for(var ei = 0; ei < orbit.electrons.length; ei++){
        var el = orbit.electrons[ei];
        el.angle += dt * el.speed;
        el.mesh.position.set(
          Math.cos(el.angle) * el.radius,
          Math.sin(el.angle) * el.radius,
          0
        );
      }
    }

    atom.rotation.z = mx*0.07;
    atom.rotation.x = my*0.06;
    atom.position.x = targetX + mx*0.45;
    atom.position.y = targetY - my*0.35 - scrollY*0.0009;

    stars.rotation.y = t*0.008 + mx*0.03;
    stars.rotation.x = my*0.02;

    camera.position.x = mx*0.25;
    camera.position.y = 2.4 - my*0.25;

    renderer.render(scene, camera);
  }
  tick();
})();
"""

VIZ_MODULE = r"""
import * as THREE from 'three';
var isMobile = window.matchMedia('(max-width: 900px)').matches;
function glowTexture(){
  var s = 128; var c = document.createElement('canvas');
  c.width = c.height = s;
  var ctx = c.getContext('2d');
  var g = ctx.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  g.addColorStop(0,'rgba(255,236,186,1)');
  g.addColorStop(0.18,'rgba(245,196,81,0.75)');
  g.addColorStop(0.45,'rgba(245,196,81,0.16)');
  g.addColorStop(1,'rgba(245,196,81,0)');
  ctx.fillStyle = g; ctx.fillRect(0,0,s,s);
  return new THREE.CanvasTexture(c);
}
var GLOW = glowTexture();
(function visualizations(){
  var canvas = document.getElementById('viz-canvas');
  if(!canvas) return;
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 1.9));
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  scene.add(new THREE.AmbientLight(0xffffff, 0.4));
  var l1 = new THREE.PointLight(0xF5C451, 20, 30); l1.position.set(4, 4, 6); scene.add(l1);
  var l2 = new THREE.PointLight(0xB98A24, 10, 30); l2.position.set(-5, -3, 4); scene.add(l2);
  var root = new THREE.Group(); scene.add(root);
  var COL = { electric: 0xF5C451, magnetic: 0xFFE39B, gravity: 0xB98A24, wave: 0xF5C451, projectile: 0xFFE39B, pendulum: 0xF5C451 };
  function buildElectric(){
    var g = new THREE.Group();
    var core = new THREE.Mesh(new THREE.SphereGeometry(0.32, 22, 22),
      new THREE.MeshBasicMaterial({ color: 0xFFE39B, transparent: true, opacity: 0.95 }));
    g.add(core);
    var coreGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.9 }));
    coreGlow.scale.set(1.9, 1.9, 1); g.add(coreGlow);
    var lines = new THREE.Group();
    var N = isMobile ? 14 : 26;
    for(var i = 0; i < N; i++){
      var th = Math.random()*Math.PI*2, ph = Math.acos(2*Math.random()-1);
      var dir = new THREE.Vector3(Math.sin(ph)*Math.cos(th), Math.sin(ph)*Math.sin(th), Math.cos(ph));
      var len = 2.0 + Math.random()*1.6;
      var pts = [];
      for(var j = 0; j <= 12; j++){ var t = j/12; pts.push(new THREE.Vector3(dir.x*len*t, dir.y*len*t, dir.z*len*t)); }
      lines.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: COL.electric, transparent: true, opacity: 0.28, blending: THREE.AdditiveBlending, depthWrite: false })));
    }
    g.add(lines);
    var particles = new THREE.Group();
    var pMat = new THREE.MeshBasicMaterial({ color: 0xFFF3D0 });
    var pCount = isMobile ? 20 : 44;
    var pData = [];
    for(var k = 0; k < pCount; k++){
      var th2 = Math.random()*Math.PI*2, ph2 = Math.acos(2*Math.random()-1);
      var dir2 = new THREE.Vector3(Math.sin(ph2)*Math.cos(th2), Math.sin(ph2)*Math.sin(th2), Math.cos(ph2));
      var p = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8), pMat);
      pData.push({ mesh: p, dir: dir2, t: Math.random(), speed: 0.22 + Math.random()*0.22 });
      particles.add(p);
    }
    g.add(particles);
    g.userData = { core: core, coreGlow: coreGlow, pData: pData };
    return g;
  }
  function buildMagnetic(){
    var g = new THREE.Group();
    var magH = 1.2, magR = 0.28;
    var north = new THREE.Mesh(new THREE.BoxGeometry(magR*2, magH, magR*2),
      new THREE.MeshStandardMaterial({ color: 0xF5C451, emissive: 0xF5C451, emissiveIntensity: 0.35, roughness: 0.4, metalness: 0.6 }));
    north.position.y = magH/2; g.add(north);
    var south = new THREE.Mesh(new THREE.BoxGeometry(magR*2, magH, magR*2),
      new THREE.MeshStandardMaterial({ color: 0x2A2A30, emissive: 0x111114, emissiveIntensity: 0.4, roughness: 0.5, metalness: 0.5 }));
    south.position.y = -magH/2; g.add(south);
    var lines = new THREE.Group();
    var planes = isMobile ? 5 : 8, perPlane = isMobile ? 3 : 4;
    for(var pi = 0; pi < planes; pi++){
      var planeRot = (pi/planes)*Math.PI*2;
      for(var li = 0; li < perPlane; li++){
        var R = 0.9 + li*0.55;
        var pts = [];
        for(var j = 0; j <= 72; j++){
          var a = (j/72)*Math.PI*2;
          pts.push(new THREE.Vector3(Math.sin(a)*R, Math.cos(a)*magH*1.05, 0));
        }
        var line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({ color: COL.magnetic, transparent: true, opacity: 0.24, blending: THREE.AdditiveBlending, depthWrite: false }));
        line.rotation.y = planeRot; lines.add(line);
      }
    }
    g.add(lines);
    var particles = new THREE.Group();
    var pMat = new THREE.MeshBasicMaterial({ color: 0xFFF3D0 });
    var pCount = isMobile ? 10 : 18;
    var pData = [];
    for(var k = 0; k < pCount; k++){
      var p = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 8), pMat);
      pData.push({ mesh: p, t: Math.random(), speed: 0.14 + Math.random()*0.14, R: 1.6 + Math.random()*1.4, plane: Math.random()*Math.PI*2 });
      particles.add(p);
    }
    g.add(particles);
    g.userData = { north: north, south: south, pData: pData, magH: magH };
    return g;
  }
  function buildGravity(){
    var g = new THREE.Group();
    var size = 7, seg = isMobile ? 26 : 40;
    var geo = new THREE.PlaneGeometry(size, size, seg, seg);
    var posAttr = geo.attributes.position;
    for(var i = 0; i < posAttr.count; i++){
      var x = posAttr.getX(i), y = posAttr.getY(i);
      var r = Math.sqrt(x*x + y*y);
      posAttr.setZ(i, -1.6 / (1 + r*r*0.55));
    }
    geo.computeVertexNormals();
    var grid = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: COL.gravity, wireframe: true, transparent: true, opacity: 0.3 }));
    grid.rotation.x = -Math.PI/2.35; grid.position.y = 0.4; g.add(grid);
    var mass = new THREE.Mesh(new THREE.SphereGeometry(0.42, 26, 26),
      new THREE.MeshStandardMaterial({ color: 0xF5C451, emissive: 0xF5C451, emissiveIntensity: 0.9, roughness: 0.35, metalness: 0.7 }));
    mass.position.y = -0.75; g.add(mass);
    var massGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.85 }));
    massGlow.scale.set(2.2, 2.2, 1); mass.add(massGlow);
    var orbit = new THREE.Mesh(new THREE.TorusGeometry(2.1, 0.005, 8, 140),
      new THREE.MeshBasicMaterial({ color: COL.gravity, transparent: true, opacity: 0.32, blending: THREE.AdditiveBlending, depthWrite: false }));
    orbit.rotation.x = Math.PI/2 + 0.1; orbit.position.y = -0.3; g.add(orbit);
    var sat = new THREE.Mesh(new THREE.SphereGeometry(0.1, 14, 14), new THREE.MeshBasicMaterial({ color: 0xFFE39B }));
    g.add(sat);
    var satGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.9 }));
    satGlow.scale.set(1.3, 1.3, 1); sat.add(satGlow);
    var particles = new THREE.Group();
    var pMat = new THREE.MeshBasicMaterial({ color: 0xFFE39B });
    var pCount = isMobile ? 24 : 46;
    var pData = [];
    for(var k = 0; k < pCount; k++){
      var p = new THREE.Mesh(new THREE.SphereGeometry(0.025, 6, 6), pMat);
      pData.push({ mesh: p, angle: Math.random()*Math.PI*2, r: 1.4 + Math.random()*2.4, y: 0.5 + Math.random()*2, speed: 0.1 + Math.random()*0.2, fall: 0.2 + Math.random()*0.4 });
      particles.add(p);
    }
    g.add(particles);
    g.userData = { mass: mass, massGlow: massGlow, orbit: orbit, sat: sat, pData: pData };
    return g;
  }
  function buildWave(){
    var g = new THREE.Group();
    var size = 8, seg = isMobile ? 60 : 90;
    var geo = new THREE.PlaneGeometry(size, size, seg, seg);
    var count = geo.attributes.position.count;
    var baseX = new Float32Array(count), baseY = new Float32Array(count);
    for(var i = 0; i < count; i++){
      baseX[i] = geo.attributes.position.getX(i);
      baseY[i] = geo.attributes.position.getY(i);
    }
    var waveMesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: COL.wave, wireframe: true, transparent: true, opacity: 0.42, blending: THREE.AdditiveBlending, depthWrite: false }));
    waveMesh.rotation.x = -Math.PI/2.2; g.add(waveMesh);
    var sA = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 16), new THREE.MeshBasicMaterial({ color: 0xFFE39B }));
    sA.position.set(-1.6, 0.05, 0); g.add(sA);
    var sB = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 16), new THREE.MeshBasicMaterial({ color: 0xFFE39B }));
    sB.position.set(1.6, 0.05, 0); g.add(sB);
    g.userData = { waveMesh: waveMesh, sA: sA, sB: sB, baseX: baseX, baseY: baseY, count: count };
    return g;
  }
  function buildProjectile(){
    var g = new THREE.Group();
    var ground = new THREE.Mesh(new THREE.PlaneGeometry(9, 0.5),
      new THREE.MeshBasicMaterial({ color: 0xF5C451, transparent: true, opacity: 0.18, blending: THREE.AdditiveBlending, depthWrite: false }));
    ground.rotation.x = -Math.PI/2; ground.position.y = -2.2; g.add(ground);
    var grid = new THREE.GridHelper(10, 20, 0xF5C451, 0x333333);
    grid.material.transparent = true; grid.material.opacity = 0.08; grid.position.y = -2.19; g.add(grid);
    var launcher = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.7, 12),
      new THREE.MeshStandardMaterial({ color: 0xF5C451, emissive: 0xF5C451, emissiveIntensity: 0.35, roughness: 0.4, metalness: 0.6 }));
    launcher.position.set(-4, -1.85, 0); launcher.rotation.z = -Math.PI/4; g.add(launcher);
    var ball = new THREE.Mesh(new THREE.SphereGeometry(0.16, 20, 20),
      new THREE.MeshStandardMaterial({ color: 0xFFE39B, emissive: 0xFFE39B, emissiveIntensity: 0.8, roughness: 0.3 }));
    g.add(ball);
    var ballGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.85 }));
    ballGlow.scale.set(1.6, 1.6, 1); ball.add(ballGlow);
    var trailLen = 90;
    var trailGeo = new THREE.BufferGeometry();
    var trailPos = new Float32Array(trailLen * 3);
    for(var i = 0; i < trailLen; i++){ trailPos[i*3+1] = -999; }
    trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPos, 3));
    var trail = new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color: 0xF5C451, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false }));
    g.add(trail);
    g.userData = { ball: ball, trail: trail, trailPos: trailPos, trailLen: trailLen, pos: new THREE.Vector3(-4, -1.85, 0), vel: new THREE.Vector3(3.4, 4.6, 0), g: -6.2, launched: false, timer: 0, trailIdx: 0 };
    return g;
  }
  function buildPendulum(){
    var g = new THREE.Group();
    var bar = new THREE.Mesh(new THREE.BoxGeometry(3, 0.05, 0.3),
      new THREE.MeshStandardMaterial({ color: 0xF5C451, emissive: 0xF5C451, emissiveIntensity: 0.3, roughness: 0.4, metalness: 0.6 }));
    bar.position.y = 2; g.add(bar);
    var pivot = new THREE.Group(); pivot.position.y = 2; g.add(pivot);
    var rodLen = 2.2;
    var rod = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, rodLen, 8),
      new THREE.MeshBasicMaterial({ color: 0xF5C451, transparent: true, opacity: 0.75 }));
    rod.position.y = -rodLen/2; pivot.add(rod);
    var bob = new THREE.Mesh(new THREE.SphereGeometry(0.24, 24, 24),
      new THREE.MeshStandardMaterial({ color: 0xFFE39B, emissive: 0xFFE39B, emissiveIntensity: 1.0, roughness: 0.3, metalness: 0.5 }));
    bob.position.y = -rodLen; pivot.add(bob);
    var bobGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.85 }));
    bobGlow.scale.set(2.0, 2.0, 1); bob.add(bobGlow);
    var trailLen = 80;
    var trailGeo = new THREE.BufferGeometry();
    var trailPos = new Float32Array(trailLen * 3);
    for(var i = 0; i < trailLen; i++){ trailPos[i*3+1] = -999; }
    trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPos, 3));
    var trail = new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color: 0xF5C451, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false }));
    g.add(trail);
    g.userData = { pivot: pivot, bob: bob, trail: trail, trailPos: trailPos, trailLen: trailLen, theta: Math.PI/3, omega: 0, L: rodLen/2, g: 4.5, trailIdx: 0 };
    return g;
  }
  var builders = { electric: buildElectric, magnetic: buildMagnetic, gravity: buildGravity, wave: buildWave, projectile: buildProjectile, pendulum: buildPendulum };
  var currentMode = 'electric';
  var currentGroup, nextGroup;
  var transition = 1, transitioning = false;
  function setGroupOpacity(group, o){
    group.traverse(function(obj){
      if(obj.material){
        var mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        mats.forEach(function(m){
          if(m.userData.baseOpacity === undefined) m.userData.baseOpacity = m.opacity;
          m.transparent = true;
          m.opacity = m.userData.baseOpacity * o;
        });
      }
    });
  }
  function buildAndAdd(mode){
    var g = builders[mode]();
    g.visible = false; root.add(g); setGroupOpacity(g, 0);
    return g;
  }
  var groups = {
    electric: buildAndAdd('electric'),
    magnetic: buildAndAdd('magnetic'),
    gravity: buildAndAdd('gravity'),
    wave: buildAndAdd('wave'),
    projectile: buildAndAdd('projectile'),
    pendulum: buildAndAdd('pendulum')
  };
  currentGroup = groups.electric;
  currentGroup.visible = true;
  setGroupOpacity(currentGroup, 1);
  function applyMode(mode){
    if(mode === currentMode || transitioning) return;
    nextGroup = groups[mode];
    nextGroup.visible = true;
    setGroupOpacity(nextGroup, 0);
    transition = 0; transitioning = true; currentMode = mode;
  }
  window.__vizCycle = function(mode){ applyMode(mode); };
  function resize(){
    var w = canvas.clientWidth || 800, h = canvas.clientHeight || 380;
    renderer.setSize(w, h, false);
    camera.aspect = w/h; camera.updateProjectionMatrix();
    var s = Math.min(w/900, h/420);
    var scale = Math.max(0.55, Math.min(1.4, s*1.05));
    root.scale.setScalar(scale);
    if(w < 640){ camera.position.set(0, 2.6, 8.6); }
    else { camera.position.set(0, 1.4, 7.2); }
    camera.lookAt(0, -0.2, 0);
  }
  resize();
  window.addEventListener('resize', resize);
  var visible = false;
  var vio = new IntersectionObserver(function(es){ visible = es[0].isIntersecting; }, { threshold: 0.05 });
  vio.observe(canvas);
  var clock = new THREE.Clock();
  function tick(){
    requestAnimationFrame(tick);
    if(!visible) return;
    var t = clock.getElapsedTime();
    if(transitioning){
      transition += 0.045;
      if(transition >= 1){
        transition = 1;
        setGroupOpacity(currentGroup, 0); currentGroup.visible = false;
        setGroupOpacity(nextGroup, 1); currentGroup = nextGroup; nextGroup = null;
        transitioning = false;
      } else {
        setGroupOpacity(currentGroup, 1 - transition);
        setGroupOpacity(nextGroup, transition);
      }
    }
    root.rotation.y = Math.sin(t*0.12)*0.18;
    if(groups.electric.visible){
      var d = groups.electric.userData;
      d.core.rotation.x = t*0.5; d.core.rotation.y = t*0.7;
      d.coreGlow.material.opacity = 0.75 + Math.sin(t*2.4)*0.2;
      d.pData.forEach(function(p){
        p.t += 0.0035*p.speed*3; if(p.t > 1) p.t -= 1;
        var r = 0.35 + p.t*2.6;
        p.mesh.position.set(p.dir.x*r, p.dir.y*r, p.dir.z*r);
        p.mesh.material.opacity = Math.sin(p.t*Math.PI);
      });
    }
    if(groups.magnetic.visible){
      var dm = groups.magnetic.userData;
      dm.north.rotation.y = Math.sin(t*0.4)*0.12;
      dm.south.rotation.y = Math.sin(t*0.4)*0.12;
      dm.pData.forEach(function(p){
        p.t += 0.0035*p.speed*3; if(p.t > 1) p.t -= 1;
        var a = p.t*Math.PI*2;
        var x = Math.sin(a)*p.R, y = Math.cos(a)*dm.magH*1.05;
        var c = Math.cos(p.plane), s = Math.sin(p.plane);
        p.mesh.position.set(x*c, y, x*s);
      });
    }
    if(groups.gravity.visible){
      var dg = groups.gravity.userData;
      var a2 = t*0.55;
      dg.sat.position.set(Math.cos(a2)*2.1, -0.3 + Math.sin(a2)*2.1*0.12, Math.sin(a2)*2.1);
      dg.orbit.rotation.z = t*0.06; dg.mass.rotation.y = t*0.4;
      dg.massGlow.material.opacity = 0.7 + Math.sin(t*2.1)*0.18;
      dg.pData.forEach(function(p){
        p.angle += 0.004*p.speed; p.r -= 0.004*p.fall; p.y -= 0.006*p.fall;
        if(p.r < 0.5){ p.r = 1.4 + Math.random()*2.4; p.y = 0.5 + Math.random()*2; }
        p.mesh.position.set(Math.cos(p.angle)*p.r, p.y - 0.4, Math.sin(p.angle)*p.r);
      });
    }
    if(groups.wave.visible){
      var dw = groups.wave.userData;
      var geoW = dw.waveMesh.geometry;
      var posAttr = geoW.attributes.position;
      var k = 2.4, omega = 4.2, amp = 0.55, ax = -1.6, bx = 1.6;
      for(var i = 0; i < dw.count; i++){
        var x = dw.baseX[i], y = dw.baseY[i];
        var rA = Math.sqrt((x-ax)*(x-ax) + y*y);
        var rB = Math.sqrt((x-bx)*(x-bx) + y*y);
        var zA = Math.sin(k*rA - omega*t) / (1 + rA*0.9);
        var zB = Math.sin(k*rB - omega*t) / (1 + rB*0.9);
        posAttr.setZ(i, (zA + zB) * amp);
      }
      posAttr.needsUpdate = true;
      geoW.computeVertexNormals();
      dw.sA.scale.setScalar(1 + Math.sin(t*6)*0.15);
      dw.sB.scale.setScalar(1 + Math.sin(t*6 + Math.PI)*0.15);
    }
    if(groups.projectile.visible){
      var dp = groups.projectile.userData;
      dp.timer += 1/60;
      if(!dp.launched){
        if(dp.timer > 1.2){
          dp.launched = true; dp.timer = 0;
          dp.pos.set(-4, -1.85, 0);
          dp.vel.set(3.4 + Math.random()*0.6, 4.4 + Math.random()*0.5, 0);
          for(var ii = 0; ii < dp.trailLen; ii++){ dp.trailPos[ii*3+1] = -999; }
          dp.trail.geometry.attributes.position.needsUpdate = true;
          dp.trailIdx = 0;
        }
      } else {
        dp.vel.y += dp.g * (1/60);
        dp.pos.x += dp.vel.x * (1/60);
        dp.pos.y += dp.vel.y * (1/60);
        dp.ball.position.copy(dp.pos);
        dp.trailIdx = (dp.trailIdx + 1) % dp.trailLen;
        dp.trailPos[dp.trailIdx*3] = dp.pos.x;
        dp.trailPos[dp.trailIdx*3+1] = dp.pos.y;
        dp.trailPos[dp.trailIdx*3+2] = dp.pos.z;
        dp.trail.geometry.attributes.position.needsUpdate = true;
        if(dp.pos.y < -2.2 || dp.pos.x > 5){ dp.launched = false; dp.timer = 0; }
      }
    }
    if(groups.pendulum.visible){
      var dpp = groups.pendulum.userData;
      var alpha = -(dpp.g / dpp.L) * Math.sin(dpp.theta);
      dpp.omega += alpha * (1/60);
      dpp.theta += dpp.omega * (1/60);
      dpp.omega *= 0.9995;
      dpp.pivot.rotation.z = dpp.theta;
      var bobWorld = new THREE.Vector3();
      dpp.bob.getWorldPosition(bobWorld);
      dpp.trailIdx = (dpp.trailIdx + 1) % dpp.trailLen;
      dpp.trailPos[dpp.trailIdx*3] = bobWorld.x;
      dpp.trailPos[dpp.trailIdx*3+1] = bobWorld.y;
      dpp.trailPos[dpp.trailIdx*3+2] = bobWorld.z;
      dpp.trail.geometry.attributes.position.needsUpdate = true;
    }
    renderer.render(scene, camera);
  }
  tick();
})();
"""


# ============================================================
# ADMIN HTML — with paper management & paper feedback
# ============================================================
ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>P6 CREW Console — SR Physics</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&family=Noto+Sans+Sinhala:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070708;--surface:#101012;--surface-2:#151518;
  --line:rgba(245,196,81,.13);--line-soft:rgba(255,255,255,.06);
  --gold:#F5C451;--gold-bright:#FFE39B;--gold-deep:#B98A24;
  --text:#EDEAE4;--muted:#84848E;--muted-2:#5A5A63;
  --font-d:'Space Grotesk',system-ui,sans-serif;
  --font-m:'JetBrains Mono',ui-monospace,monospace;
  --sinhala:'Noto Sans Sinhala',sans-serif;
  --ease:cubic-bezier(.22,1,.36,1);
}
html,body{background:var(--bg);color:var(--text);font-family:var(--font-d),var(--sinhala);min-height:100%}
body{line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
::selection{background:var(--gold);color:#0a0a0a}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-track{background:#0a0a0b}
::-webkit-scrollbar-thumb{background:#2a2a2e;border-radius:9px}
::-webkit-scrollbar-thumb:hover{background:var(--gold-deep)}
a{color:inherit;text-decoration:none}
button{font:inherit;color:inherit;background:none;border:none;cursor:pointer}
input,select,textarea{font:inherit;color:inherit}
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:
  radial-gradient(ellipse at 30% 20%,rgba(245,196,81,.09),transparent 55%),
  radial-gradient(ellipse at 70% 80%,rgba(245,196,81,.06),transparent 55%),#070708}
.login-card{width:100%;max-width:440px;border:1px solid var(--line);border-radius:8px;padding:clamp(28px,5vw,48px);background:linear-gradient(160deg,rgba(245,196,81,.04),transparent 55%),#0A0A0C;position:relative;overflow:hidden}
.login-card::before{content:'';position:absolute;top:-1px;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
.login-mark{width:56px;height:56px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;font-family:var(--font-d);font-weight:700;font-size:15px;color:var(--gold);margin-bottom:26px;position:relative}
.login-mark::after{content:'';position:absolute;inset:-5px;border-radius:50%;border:1px solid transparent;border-top-color:rgba(245,196,81,.4);animation:spin 5s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.login-title{font-size:clamp(1.5rem,3vw,2rem);font-weight:600;letter-spacing:-.035em;line-height:1.15;margin-bottom:10px}
.login-sub{font-family:var(--font-m);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:32px;line-height:1.9}
.login-field{margin-bottom:16px}
.login-field label{display:block;font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:9px}
.login-field input{width:100%;background:rgba(255,255,255,.015);border:1px solid var(--line-soft);border-radius:6px;padding:15px 18px;font-size:14px;font-weight:300;outline:none;transition:border-color .4s,background .4s,box-shadow .4s;letter-spacing:.06em;color:var(--text)}
.login-field input:focus{border-color:rgba(245,196,81,.55);background:rgba(245,196,81,.02);box-shadow:0 0 0 3px rgba(245,196,81,.08)}
.login-btn{width:100%;display:inline-flex;align-items:center;justify-content:center;gap:11px;padding:16px 30px;border-radius:100px;font-size:13.5px;font-weight:500;letter-spacing:.02em;background:linear-gradient(100deg,var(--gold) 0%,var(--gold-bright) 50%,var(--gold) 100%);background-size:220% 100%;color:#0a0a0a;animation:shine 6s linear infinite;box-shadow:0 0 0 0 rgba(245,196,81,.4);transition:box-shadow .5s;margin-top:12px}
.login-btn:hover{box-shadow:0 12px 44px -10px rgba(245,196,81,.55)}
.login-btn:disabled{opacity:.6;cursor:wait}
@keyframes shine{to{background-position:-220% 0}}
.login-err{margin-top:16px;font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#ff5a5a;display:none;text-align:center;line-height:1.9}
.login-err.on{display:block}
.login-ok{margin-top:16px;font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#4ade80;display:none;text-align:center;line-height:1.9}
.login-ok.on{display:block}
.login-back{display:inline-flex;align-items:center;gap:8px;margin-top:26px;font-family:var(--font-m);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);transition:color .3s}
.login-back:hover{color:var(--gold)}
.dash{min-height:100vh;display:none}
.dash.on{display:block}
.dash-head{position:sticky;top:0;z-index:100;background:rgba(7,7,8,.85);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-bottom:1px solid var(--line-soft);padding:16px clamp(20px,4vw,44px);display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.dash-brand{display:flex;align-items:center;gap:14px}
.dash-mark{width:40px;height:40px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:12px;color:var(--gold);position:relative}
.dash-mark::after{content:'';position:absolute;inset:-4px;border-radius:50%;border:1px solid transparent;border-top-color:rgba(245,196,81,.4);animation:spin 5s linear infinite}
.dash-brand-txt{display:flex;flex-direction:column;line-height:1.2}
.dash-brand-txt strong{font-size:13.5px;font-weight:600;letter-spacing:-.01em}
.dash-brand-txt small{font-family:var(--font-m);font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-top:3px}
.dash-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.dash-btn{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;padding:11px 18px;border:1px solid var(--line-soft);border-radius:100px;color:var(--muted);transition:color .3s,border-color .3s,background .3s}
.dash-btn:hover{color:var(--gold);border-color:var(--line);background:rgba(245,196,81,.04)}
.dash-btn.danger{color:#ff5a5a;border-color:rgba(255,90,90,.2)}
.dash-btn.danger:hover{background:rgba(255,90,90,.1);border-color:rgba(255,90,90,.45);color:#ff5a5a}
.dash-body{padding:32px clamp(20px,4vw,44px) 80px;max-width:1500px;margin:0 auto}
.dash-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:32px}
@media(max-width:900px){.dash-stats{grid-template-columns:repeat(2,1fr)}}
.stat-card{border:1px solid var(--line-soft);border-radius:6px;padding:22px;background:var(--surface);position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(245,196,81,.4),transparent)}
.stat-lbl{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:10px}
.stat-val{font-size:clamp(1.8rem,3vw,2.4rem);font-weight:600;letter-spacing:-.045em;line-height:1;color:var(--gold);font-variant-numeric:tabular-nums}
.stat-val.warn{color:#ff9a3c}.stat-val.ok{color:#4ade80}.stat-val.muted{color:var(--muted)}
.dash-controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--line-soft)}
.tabs{display:flex;gap:6px;flex-wrap:wrap}
.tab{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding:10px 16px;border:1px solid var(--line-soft);border-radius:100px;transition:color .3s,border-color .3s,background .3s;position:relative}
.tab .badge{display:inline-block;margin-left:6px;background:var(--gold);color:#0a0a0a;border-radius:100px;font-size:9px;font-weight:600;padding:1px 6px;min-width:18px;text-align:center}
.tab.on{color:#0a0a0a;background:var(--gold);border-color:var(--gold)}
.tab.on .badge{background:#0a0a0a;color:var(--gold)}
.tab:hover:not(.on){color:var(--gold);border-color:var(--line)}
.dash-search{flex:1;min-width:200px;position:relative}
.dash-search input{width:100%;background:rgba(255,255,255,.015);border:1px solid var(--line-soft);border-radius:100px;padding:12px 18px 12px 42px;font-size:13px;font-weight:300;outline:none;transition:border-color .4s,background .4s;color:var(--text)}
.dash-search input:focus{border-color:rgba(245,196,81,.55);background:rgba(245,196,81,.02)}
.dash-search svg{position:absolute;left:16px;top:50%;transform:translateY(-50%);width:14px;height:14px;stroke:var(--muted-2);pointer-events:none}
.dash-export{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);padding:11px 20px;border:1px solid var(--line);border-radius:100px;transition:background .3s,color .3s}
.dash-export:hover{background:var(--gold);color:#0a0a0a}
.create-wrap{border:1px solid var(--line);border-radius:8px;background:linear-gradient(160deg,rgba(245,196,81,.04),transparent 55%),#0A0A0C;margin-bottom:26px;overflow:hidden;display:none}
.create-wrap.on{display:block}
.create-head{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;border-bottom:1px solid var(--line-soft)}
.create-head h3{font-size:1rem;font-weight:600;letter-spacing:-.02em;color:var(--gold)}
.create-close{width:32px;height:32px;border-radius:50%;border:1px solid var(--line-soft);display:grid;place-items:center;color:var(--muted);transition:all .3s}
.create-close:hover{background:var(--gold);color:#0a0a0a;border-color:var(--gold)}
.create-body{padding:22px}
.create-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:640px){.create-grid{grid-template-columns:1fr}}
.create-grid .full{grid-column:1/-1}
.cf label{display:block;font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:9px}
.cf input,.cf textarea{width:100%;background:rgba(255,255,255,.015);border:1px solid var(--line-soft);border-radius:6px;padding:14px 16px;font-size:14px;font-weight:300;outline:none;transition:border-color .4s,background .4s,box-shadow .4s;color:var(--text);font-family:var(--font-d)}
.cf textarea{min-height:100px;resize:vertical}
.cf input:focus,.cf textarea:focus{border-color:rgba(245,196,81,.55);background:rgba(245,196,81,.02);box-shadow:0 0 0 3px rgba(245,196,81,.08)}
.create-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px;grid-column:1/-1}
.create-submit{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;padding:12px 26px;border-radius:100px;background:linear-gradient(100deg,var(--gold) 0%,var(--gold-bright) 50%,var(--gold) 100%);background-size:220% 100%;color:#0a0a0a;animation:shine 6s linear infinite;transition:box-shadow .3s}
.create-submit:hover{box-shadow:0 10px 40px -8px rgba(245,196,81,.5)}
.create-submit:disabled{opacity:.6;cursor:wait}
.req-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.req-card{border:1px solid var(--line-soft);border-radius:6px;background:var(--surface);padding:22px;position:relative;overflow:hidden;transition:border-color .4s,background .4s}
.req-card:hover{border-color:rgba(245,196,81,.28);background:var(--surface-2)}
.req-card.status-contacted,.req-card.status-read,.req-card.status-resolved,.req-card.status-archived{opacity:.68}
.req-card.status-contacted .req-name::after,.req-card.status-read .req-name::after,.req-card.status-resolved .req-name::after{content:'✓';color:#4ade80;margin-left:8px;font-size:12px}
.req-top{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:14px}
.req-id{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;color:var(--muted-2)}
.req-status{font-family:var(--font-m);font-size:9px;letter-spacing:.2em;text-transform:uppercase;padding:5px 10px;border-radius:100px;border:1px solid var(--line-soft);color:var(--muted)}
.req-status.new{color:var(--gold);border-color:rgba(245,196,81,.35);background:rgba(245,196,81,.06)}
.req-status.contacted,.req-status.read,.req-status.resolved,.req-status.published{color:#4ade80;border-color:rgba(74,222,128,.35);background:rgba(74,222,128,.06)}
.req-status.archived{color:#ff9a3c;border-color:rgba(255,154,60,.35);background:rgba(255,154,60,.06)}
.req-name{font-size:1.08rem;font-weight:600;letter-spacing:-.02em;margin-bottom:4px}
.req-phone{font-family:var(--font-m);font-size:12.5px;color:var(--gold);letter-spacing:.04em;margin-bottom:12px;display:block;word-break:break-all}
.req-phone:hover{text-decoration:underline}
.req-stars{display:flex;gap:2px;color:var(--gold);font-size:13px;letter-spacing:2px;margin-bottom:10px}
.req-meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.req-chip{font-family:var(--font-m);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;padding:5px 10px;border-radius:100px;background:rgba(255,255,255,.03);border:1px solid var(--line-soft);color:var(--muted)}
.req-chip.hot{color:var(--gold);border-color:rgba(245,196,81,.35);background:rgba(245,196,81,.06)}
.req-msg{font-size:12.8px;line-height:1.75;color:#B4B2AC;font-weight:300;padding:12px 14px;background:rgba(255,255,255,.018);border-radius:4px;border-left:2px solid rgba(245,196,81,.25);margin-bottom:14px;max-height:180px;overflow-y:auto;font-family:var(--sinhala)}
.req-msg:empty{display:none}
.req-thumb{width:100%;aspect-ratio:1/1;border-radius:6px;overflow:hidden;border:1px solid var(--line-soft);margin-bottom:14px;max-width:180px;background:#0C0C0E}
.req-thumb img{width:100%;height:100%;object-fit:cover}
.req-date{font-family:var(--font-m);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted-2);margin-bottom:14px}
.req-actions{display:flex;gap:8px;flex-wrap:wrap}
.req-btn{font-family:var(--font-m);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;padding:9px 14px;border:1px solid var(--line-soft);border-radius:100px;color:var(--muted);transition:color .3s,border-color .3s,background .3s;flex:1;text-align:center;min-width:0}
.req-btn:hover{color:var(--gold);border-color:var(--line)}
.req-btn.danger:hover{color:#ff5a5a;border-color:rgba(255,90,90,.4);background:rgba(255,90,90,.06)}
.req-btn.primary{color:var(--gold);border-color:rgba(245,196,81,.35)}
.req-btn.primary:hover{background:var(--gold);color:#0a0a0a;border-color:var(--gold)}
.empty-state{grid-column:1/-1;text-align:center;padding:80px 20px;border:1px dashed var(--line-soft);border-radius:8px}
.empty-state svg{width:52px;height:52px;stroke:var(--muted-2);margin:0 auto 20px;display:block;opacity:.5}
.empty-state h3{font-size:1.1rem;font-weight:600;letter-spacing:-.02em;margin-bottom:8px}
.empty-state p{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);line-height:1.9}
.paper-stats{grid-column:1/-1;border:1px solid var(--line);border-radius:8px;background:linear-gradient(160deg,rgba(245,196,81,.05),transparent 55%),#0A0A0C;padding:22px;margin-bottom:4px;position:relative;overflow:hidden}
.paper-stats::before{content:'';position:absolute;top:0;left:15%;right:15%;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
.pb-head{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line-soft)}
.pb-head h3{font-size:1.05rem;font-weight:600;letter-spacing:-.02em;color:var(--gold)}
.pb-total{font-family:var(--font-m);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2)}
.pb-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
@media(max-width:900px){.pb-grid{grid-template-columns:1fr}}
.pb-section h4{font-family:var(--font-m);font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted-2);margin-bottom:14px}
.pb-row{display:grid;grid-template-columns:70px 1fr 34px;align-items:center;gap:10px;margin-bottom:8px}
.pb-label{font-family:var(--font-m);font-size:11px;color:var(--text);letter-spacing:.02em}
.pb-track{height:6px;background:rgba(255,255,255,.05);border-radius:100px;overflow:hidden}
.pb-fill{display:block;height:100%;background:linear-gradient(90deg,var(--gold-deep),var(--gold-bright));border-radius:100px;box-shadow:0 0 12px rgba(245,196,81,.35)}
.pb-count{font-family:var(--font-m);font-size:11px;color:var(--gold);text-align:right;font-variant-numeric:tabular-nums}
.pb-empty{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted-2);padding:12px 0}
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(120%);z-index:9990;background:rgba(10,10,12,.95);border:1px solid var(--line);border-radius:100px;padding:14px 24px;font-family:var(--font-m);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--text);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);transition:transform .6s var(--ease);display:flex;align-items:center;gap:12px;max-width:calc(100vw - 40px)}
.toast.on{transform:translateX(-50%) translateY(0)}
.toast .dot{width:6px;height:6px;border-radius:50%;background:var(--gold);flex-shrink:0}
.toast.err{border-color:rgba(255,90,90,.4)}
.toast.err .dot{background:#ff5a5a}
@media(max-width:640px){
  .dash-head{padding:12px 14px}
  .dash-body{padding:20px 14px 60px}
  .req-grid{grid-template-columns:1fr}
  .tabs{width:100%}
  .tab{flex:1;text-align:center;padding:9px 10px;font-size:9px}
  .dash-search{min-width:100%}
}
</style>
</head>
<body>
<div class="login-wrap" id="loginWrap">
  <form class="login-card" id="loginForm" autocomplete="off">
    <div class="login-mark">P6</div>
    <h1 class="login-title">P6 CREW Console</h1>
    <p class="login-sub">Restricted access · SR Physics</p>
    <div class="login-field">
      <label for="pw">Console Password</label>
      <input type="password" id="pw" placeholder="••••••••••••••••" autocomplete="off" required>
    </div>
    <button type="submit" class="login-btn" id="loginBtn">Unlock Console</button>
    <div class="login-err" id="loginErr">Invalid password</div>
    <div class="login-ok" id="loginOk">Access granted · Loading console…</div>
    <a href="/" class="login-back">← Back to site</a>
  </form>
</div>

<div class="dash" id="dash">
  <div class="dash-head">
    <div class="dash-brand">
      <div class="dash-mark">P6</div>
      <div class="dash-brand-txt"><strong>P6 Crew Console</strong><small>SR Physics · Community Hub</small></div>
    </div>
    <div class="dash-actions">
      <button class="dash-btn" id="refreshBtn">↻ Refresh</button>
      <button class="dash-btn danger" id="logoutBtn">Log out</button>
    </div>
  </div>
  <div class="dash-body">
    <div class="dash-stats">
      <div class="stat-card"><div class="stat-lbl">Total Inbox</div><div class="stat-val" id="statTotal">0</div></div>
      <div class="stat-card"><div class="stat-lbl">Unread / New</div><div class="stat-val warn" id="statNew">0</div></div>
      <div class="stat-card"><div class="stat-lbl">Handled</div><div class="stat-val ok" id="statHandled">0</div></div>
      <div class="stat-card"><div class="stat-lbl">Last 24h</div><div class="stat-val muted" id="statRecent">0</div></div>
    </div>
    <div class="dash-controls">
      <div class="tabs" id="tabs">
        <button class="tab on" data-tab="requests">Requests <span class="badge" data-badge="requests">0</span></button>
        <button class="tab" data-tab="comments">Comments <span class="badge" data-badge="comments">0</span></button>
        <button class="tab" data-tab="complaints">Feedback <span class="badge" data-badge="complaints">0</span></button>
        <button class="tab" data-tab="doubts">Doubts <span class="badge" data-badge="doubts">0</span></button>
        <button class="tab" data-tab="news">News</button>
        <button class="tab" data-tab="sessions">Sessions</button>
        <button class="tab" data-tab="motivations">Motivations</button>
        <button class="tab" data-tab="papers">Papers</button>
        <button class="tab" data-tab="paper_feedback">Paper FB <span class="badge" data-badge="paper_feedback">0</span></button>
      </div>
      <div class="dash-search">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input type="text" id="searchInput" placeholder="Search...">
      </div>
      <button class="dash-export" id="exportBtn">↓ Export CSV</button>
    </div>
    <div class="create-wrap" id="createWrap">
      <div class="create-head">
        <h3 id="createTitle">Add New Item</h3>
        <button class="create-close" id="createClose">✕</button>
      </div>
      <div class="create-body">
        <div class="create-grid">
          <div class="cf full" data-cf="news" style="display:none"><label>Title</label><input type="text" id="nwTitle" placeholder="e.g. 2026 Revision Batch Open"></div>
          <div class="cf full" data-cf="news" style="display:none"><label>Image URL (square works best)</label><input type="text" id="nwImage" placeholder="https://..."></div>
          <div class="cf full" data-cf="news" style="display:none"><label>Description</label><textarea id="nwDesc" placeholder="Short description for the news card"></textarea></div>
          <div class="cf full" data-cf="sessions" style="display:none"><label>Session Title</label><input type="text" id="ssTitle" placeholder="e.g. Rotational Dynamics — Full Theory"></div>
          <div class="cf full" data-cf="sessions" style="display:none"><label>YouTube URL</label><input type="text" id="ssUrl" placeholder="https://youtu.be/..."></div>
          <div class="cf full" data-cf="sessions" style="display:none"><label>Description</label><textarea id="ssDesc" placeholder="Short description"></textarea></div>
          <div class="cf full" data-cf="motivations" style="display:none"><label>Title (optional)</label><input type="text" id="mtTitle" placeholder="e.g. Keep Going"></div>
          <div class="cf full" data-cf="motivations" style="display:none"><label>TikTok URL</label><input type="text" id="mtUrl" placeholder="https://www.tiktok.com/@user/video/1234..."></div>
          <div class="cf full" data-cf="papers" style="display:none"><label>Paper Name</label><input type="text" id="paName" placeholder="e.g. 2024 A/L Physics Paper"></div>
          <div class="cf full" data-cf="papers" style="display:none"><label>Description (optional)</label><textarea id="paDesc" placeholder="Short description — e.g. discussion on 2026-05-12"></textarea></div>
          <div class="create-actions">
            <button type="button" class="dash-btn" id="createCancel">Cancel</button>
            <button type="button" class="create-submit" id="createSubmit">Save</button>
          </div>
        </div>
      </div>
    </div>
    <div class="req-grid" id="reqGrid"></div>
  </div>
</div>
<div class="toast" id="toast"><span class="dot"></span><span id="toastMsg">Message</span></div>
<script>
(function(){
  var STORE = { requests: [], comments: [], complaints: [], doubts: [], news: [], sessions: [], motivations: [], papers: [], paper_feedback: [] };
  var activeTab = 'requests';
  var search = '';
  var createOpen = false;
  var loginWrap = document.getElementById('loginWrap');
  var dash = document.getElementById('dash');
  var loginForm = document.getElementById('loginForm');
  var loginBtn = document.getElementById('loginBtn');
  var loginErr = document.getElementById('loginErr');
  var loginOk = document.getElementById('loginOk');
  var pwInput = document.getElementById('pw');
  var reqGrid = document.getElementById('reqGrid');
  var toast = document.getElementById('toast');
  var toastMsg = document.getElementById('toastMsg');
  var toastTimer = null;
  var createWrap = document.getElementById('createWrap');
  var createTitle = document.getElementById('createTitle');

  function showToast(msg, isErr){
    clearTimeout(toastTimer);
    toastMsg.textContent = msg;
    toast.classList.toggle('err', !!isErr);
    toast.classList.add('on');
    toastTimer = setTimeout(function(){ toast.classList.remove('on'); }, 3000);
  }
  function esc(s){
    if(s == null) return '';
    return String(s).replace(/[&<>"']/g, function(m){
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[m];
    });
  }
  function fmtDate(s){
    if(!s) return '—';
    try {
      var d = new Date(s.replace(' ', 'T'));
      if(isNaN(d.getTime())) return s;
      var diff = (Date.now() - d.getTime()) / 1000;
      if(diff < 60) return 'just now';
      if(diff < 3600) return Math.floor(diff/60) + 'm ago';
      if(diff < 86400) return Math.floor(diff/3600) + 'h ago';
      if(diff < 604800) return Math.floor(diff/86400) + 'd ago';
      return d.toLocaleDateString();
    } catch(e){ return s; }
  }
  function parseJSONArr(s){ try { return JSON.parse(s || '[]'); } catch(e){ return []; } }

  function enterDashboard(){
    loginWrap.style.display = 'none';
    dash.classList.add('on');
    loadAll();
  }

  function login(password){
    loginErr.classList.remove('on');
    loginOk.classList.remove('on');
    fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password })
    })
    .then(function(r){
      return r.text().then(function(txt){
        var data = {};
        try { data = JSON.parse(txt); } catch(e){ data = { ok: false, error: 'Server error' }; }
        return { status: r.status, data: data };
      });
    })
    .then(function(res){
      if(res.status === 200 && res.data && res.data.ok){
        loginOk.classList.add('on');
        setTimeout(enterDashboard, 400);
      } else {
        loginErr.classList.add('on');
        pwInput.value = '';
        pwInput.focus();
        setTimeout(function(){ loginErr.classList.remove('on'); }, 3000);
        loginBtn.disabled = false;
        loginBtn.textContent = 'Unlock Console';
      }
    })
    .catch(function(err){
      console.error('login error', err);
      showToast('Network error', true);
      loginBtn.disabled = false;
      loginBtn.textContent = 'Unlock Console';
    });
  }
  loginForm.addEventListener('submit', function(e){
    e.preventDefault();
    var pw = pwInput.value;
    if(!pw) return;
    loginBtn.disabled = true;
    loginBtn.textContent = 'Verifying...';
    login(pw);
  });

  function loadAll(){
    var types = ['requests','comments','complaints','doubts','news','sessions','motivations','papers','paper_feedback'];
    Promise.all(types.map(function(t){
      return fetch('/api/admin/data/' + t)
        .then(function(r){
          if(r.status === 401) return { __unauth: true };
          return r.json().catch(function(){ return {}; });
        })
        .catch(function(){ return {}; });
    })).then(function(results){
      if(results[0] && results[0].__unauth){
        dash.classList.remove('on');
        loginWrap.style.display = 'flex';
        return;
      }
      types.forEach(function(t, i){
        var r = results[i] || {};
        STORE[t] = (r && r.items) || [];
      });
      renderAll();
    }).catch(function(err){
      console.error('loadAll error', err);
      showToast('Failed to load', true);
    });
  }
  function renderAll(){
    try { renderStats(); } catch(e){ console.error(e); }
    try { renderBadges(); } catch(e){ console.error(e); }
    try { renderList(); } catch(e){ console.error(e); }
  }
  function renderStats(){
    var all = STORE.requests.concat(STORE.comments, STORE.complaints, STORE.doubts, STORE.paper_feedback);
    var total = all.length;
    var nw = all.filter(function(r){ return (r.status || 'new') === 'new'; }).length;
    var hd = total - nw;
    var dayAgo = Date.now() - 86400000;
    var recent = all.filter(function(r){
      if(!r.created_at) return false;
      var d = new Date(r.created_at.replace(' ', 'T'));
      return !isNaN(d.getTime()) && d.getTime() > dayAgo;
    }).length;
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statNew').textContent = nw;
    document.getElementById('statHandled').textContent = hd;
    document.getElementById('statRecent').textContent = recent;
  }
  function renderBadges(){
    ['requests','comments','complaints','doubts','paper_feedback'].forEach(function(t){
      var unread = STORE[t].filter(function(r){ return (r.status || 'new') === 'new'; }).length;
      var b = document.querySelector('[data-badge="' + t + '"]');
      if(b){ b.textContent = unread; b.style.display = unread ? 'inline-block' : 'none'; }
    });
  }
  function renderList(){
    var items = (STORE[activeTab] || []).slice();
    if(search){
      var q = search.toLowerCase();
      items = items.filter(function(r){ return JSON.stringify(r).toLowerCase().indexOf(q) >= 0; });
    }
    var prefix = (activeTab === 'paper_feedback') ? '<div class="paper-stats" id="paperStats"></div>' : '';
    if(!items.length){
      reqGrid.innerHTML = prefix + '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.4" stroke-linecap="round"><path d="M3 7h18v13H3zM3 7l3-4h12l3 4M9 13h6"/></svg><h3>Nothing here yet.</h3><p>Try changing the tab</p></div>';
      if(activeTab === 'paper_feedback') loadPaperStats();
      return;
    }
    var html = '';
    items.forEach(function(r){
      var status = r.status || 'new';
      var cls = 'status-' + status;
      if(activeTab === 'requests') html += cardRequest(r, status, cls);
      else if(activeTab === 'comments') html += cardComment(r, status, cls);
      else if(activeTab === 'complaints') html += cardComplaint(r, status, cls);
      else if(activeTab === 'doubts') html += cardDoubt(r, status, cls);
      else if(activeTab === 'news') html += cardNews(r);
      else if(activeTab === 'sessions') html += cardSession(r);
      else if(activeTab === 'motivations') html += cardMotivation(r);
      else if(activeTab === 'papers') html += cardPaperName(r);
      else if(activeTab === 'paper_feedback') html += cardPaperFeedback(r, status, cls);
    });
    reqGrid.innerHTML = prefix + html;
    bindActions();
    if(activeTab === 'paper_feedback') loadPaperStats();
  }
  function cardRequest(r, status, cls){
    return '<div class="req-card ' + cls + '">' +
      '<div class="req-top"><span class="req-id">REQ #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'new' ? 'New' : 'Contacted') + '</span></div>' +
      '<div class="req-name">' + esc(r.name) + '</div>' +
      '<a class="req-phone" href="tel:' + esc(r.phone) + '">' + esc(r.phone) + '</a>' +
      '<div class="req-meta">' + (r.batch ? '<span class="req-chip">' + esc(r.batch) + '</span>' : '') + (r.location ? '<span class="req-chip">' + esc(r.location) + '</span>' : '') + (r.email ? '<span class="req-chip">' + esc(r.email) + '</span>' : '') + '</div>' +
      (r.message ? '<div class="req-msg">' + esc(r.message) + '</div>' : '') +
      '<div class="req-date">Received · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'new' ? '<button class="req-btn primary" data-act="toggle" data-type="requests" data-id="' + r.id + '" data-next="contacted">Mark Contacted</button>' : '<button class="req-btn" data-act="toggle" data-type="requests" data-id="' + r.id + '" data-next="new">Mark New</button>') +
        '<a class="req-btn primary" href="https://wa.me/' + esc((r.phone || '').replace(/[^0-9]/g, '')) + '" target="_blank" rel="noopener">WhatsApp</a>' +
        '<button class="req-btn danger" data-act="delete" data-type="requests" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardComment(r, status, cls){
    var stars = ''; var rating = parseInt(r.rating || 5, 10);
    for(var i = 0; i < 5; i++) stars += i < rating ? '★' : '☆';
    return '<div class="req-card ' + cls + '">' +
      '<div class="req-top"><span class="req-id">CMT #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'new' ? 'New' : 'Read') + '</span></div>' +
      '<div class="req-stars">' + stars + '</div>' +
      '<div class="req-name">' + esc(r.name) + '</div>' +
      '<div class="req-meta">' + (r.batch ? '<span class="req-chip hot">Batch ' + esc(r.batch) + '</span>' : '') + '<span class="req-chip">Rating ' + rating + '/5</span></div>' +
      (r.message ? '<div class="req-msg">' + esc(r.message) + '</div>' : '') +
      '<div class="req-date">Received · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'new' ? '<button class="req-btn primary" data-act="toggle" data-type="comments" data-id="' + r.id + '" data-next="read">Mark Read</button>' : '<button class="req-btn" data-act="toggle" data-type="comments" data-id="' + r.id + '" data-next="new">Mark Unread</button>') +
        '<button class="req-btn danger" data-act="delete" data-type="comments" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardComplaint(r, status, cls){
    return '<div class="req-card ' + cls + '">' +
      '<div class="req-top"><span class="req-id">FDB #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'new' ? 'New' : 'Resolved') + '</span></div>' +
      '<div class="req-name">' + (r.name ? esc(r.name) : '<em style="color:var(--muted-2);font-style:italic;font-weight:400">Anonymous</em>') + '</div>' +
      '<div class="req-meta">' + (r.category ? '<span class="req-chip hot">' + esc(r.category) + '</span>' : '') + (r.contact ? '<span class="req-chip">' + esc(r.contact) + '</span>' : '') + '</div>' +
      (r.message ? '<div class="req-msg">' + esc(r.message) + '</div>' : '') +
      '<div class="req-date">Received · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'new' ? '<button class="req-btn primary" data-act="toggle" data-type="complaints" data-id="' + r.id + '" data-next="resolved">Mark Resolved</button>' : '<button class="req-btn" data-act="toggle" data-type="complaints" data-id="' + r.id + '" data-next="new">Mark New</button>') +
        '<button class="req-btn danger" data-act="delete" data-type="complaints" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardDoubt(r, status, cls){
    return '<div class="req-card ' + cls + '">' +
      '<div class="req-top"><span class="req-id">DBT #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'new' ? 'New' : 'Answered') + '</span></div>' +
      '<div class="req-name">' + esc(r.name) + '</div>' +
      '<div class="req-meta">' + (r.batch ? '<span class="req-chip">Batch ' + esc(r.batch) + '</span>' : '') + (r.topic ? '<span class="req-chip hot">' + esc(r.topic) + '</span>' : '') + '</div>' +
      (r.question ? '<div class="req-msg">' + esc(r.question) + '</div>' : '') +
      '<div class="req-date">Received · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'new' ? '<button class="req-btn primary" data-act="toggle" data-type="doubts" data-id="' + r.id + '" data-next="resolved">Mark Answered</button>' : '<button class="req-btn" data-act="toggle" data-type="doubts" data-id="' + r.id + '" data-next="new">Mark New</button>') +
        '<button class="req-btn danger" data-act="delete" data-type="doubts" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardNews(r){
    return '<div class="req-card">' +
      '<div class="req-top"><span class="req-id">NEWS #' + String(r.id).padStart(4,'0') + '</span><span class="req-status published">Published</span></div>' +
      (r.image_url ? '<div class="req-thumb"><img src="' + esc(r.image_url) + '" alt="" onerror="this.style.display=\'none\'"></div>' : '') +
      '<div class="req-name">' + esc(r.title) + '</div>' +
      (r.description ? '<div class="req-msg">' + esc(r.description) + '</div>' : '') +
      '<div class="req-date">Posted · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions"><button class="req-btn danger" data-act="delete" data-type="news" data-id="' + r.id + '">Delete</button></div></div>';
  }
  function cardSession(r){
    var m = (r.youtube_url || '').match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{6,})/);
    var id = m ? m[1] : '';
    return '<div class="req-card">' +
      '<div class="req-top"><span class="req-id">YT #' + String(r.id).padStart(4,'0') + '</span><span class="req-status published">Published</span></div>' +
      (id ? '<div class="req-thumb" style="aspect-ratio:16/9;max-width:100%"><img src="https://img.youtube.com/vi/' + id + '/mqdefault.jpg" alt=""></div>' : '') +
      '<div class="req-name">' + esc(r.title) + '</div>' +
      '<div class="req-meta"><span class="req-chip">' + esc(id || 'invalid url') + '</span></div>' +
      (r.description ? '<div class="req-msg">' + esc(r.description) + '</div>' : '') +
      '<div class="req-date">Added · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (id ? '<a class="req-btn primary" href="https://youtu.be/' + id + '" target="_blank" rel="noopener">Watch</a>' : '') +
        '<button class="req-btn danger" data-act="delete" data-type="sessions" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardMotivation(r){
    var m = (r.tiktok_url || '').match(/\/video\/(\d+)/);
    var id = m ? m[1] : '';
    return '<div class="req-card">' +
      '<div class="req-top"><span class="req-id">TT #' + String(r.id).padStart(4,'0') + '</span><span class="req-status published">Published</span></div>' +
      '<div class="req-name">' + esc(r.title || 'Motivation') + '</div>' +
      '<div class="req-meta"><span class="req-chip">' + esc(id || 'invalid url') + '</span></div>' +
      '<div class="req-date">Added · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions"><a class="req-btn primary" href="' + esc(r.tiktok_url) + '" target="_blank" rel="noopener">Open</a><button class="req-btn danger" data-act="delete" data-type="motivations" data-id="' + r.id + '">Delete</button></div></div>';
  }
  function cardPaperName(r){
    var status = r.status || 'published';
    var isLatest = (STORE.papers.length && STORE.papers[0].id === r.id && status === 'published');
    var feedbackCount = STORE.paper_feedback.filter(function(f){ return f.paper_id === r.id; }).length;
    return '<div class="req-card">' +
      '<div class="req-top"><span class="req-id">PAP #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'published' ? (isLatest ? 'Live on Site' : 'Published') : 'Archived') + '</span></div>' +
      '<div class="req-name">' + esc(r.name) + '</div>' +
      (r.description ? '<div class="req-msg">' + esc(r.description) + '</div>' : '') +
      '<div class="req-meta"><span class="req-chip hot">' + feedbackCount + ' feedback' + (feedbackCount === 1 ? '' : 's') + '</span></div>' +
      '<div class="req-date">Added · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'published'
          ? '<button class="req-btn" data-act="paper-status" data-id="' + r.id + '" data-next="archived">Archive</button>'
          : '<button class="req-btn primary" data-act="paper-status" data-id="' + r.id + '" data-next="published">Publish</button>') +
        '<button class="req-btn danger" data-act="paper-delete" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function cardPaperFeedback(r, status, cls){
    var mcq = parseJSONArr(r.mcq), st = parseJSONArr(r.structured), es = parseJSONArr(r.essays);
    var chips = '';
    mcq.forEach(function(q){ chips += '<span class="req-chip hot">MCQ ' + esc(q) + '</span>'; });
    st.forEach(function(q){ chips += '<span class="req-chip hot">Struct ' + esc(q) + '</span>'; });
    es.forEach(function(q){ chips += '<span class="req-chip hot">Essay ' + esc(q) + '</span>'; });
    var paper = STORE.papers.find(function(p){ return p.id === r.paper_id; });
    var paperName = paper ? paper.name : ('#' + (r.paper_id || '—'));
    return '<div class="req-card ' + cls + '">' +
      '<div class="req-top"><span class="req-id">PFB #' + String(r.id).padStart(4,'0') + '</span><span class="req-status ' + status + '">' + (status === 'new' ? 'New' : 'Read') + '</span></div>' +
      '<div class="req-name">' + (r.name ? esc(r.name) : '<em style="color:var(--muted-2);font-style:italic;font-weight:400">Anonymous</em>') + '</div>' +
      '<div class="req-meta">' + (r.batch ? '<span class="req-chip">Batch ' + esc(r.batch) + '</span>' : '') + '<span class="req-chip">' + esc(paperName) + '</span></div>' +
      '<div class="req-meta">' + (chips || '<span class="req-chip">No questions flagged</span>') + '</div>' +
      (r.comment ? '<div class="req-msg">' + esc(r.comment) + '</div>' : '') +
      '<div class="req-date">Received · ' + esc(fmtDate(r.created_at)) + '</div>' +
      '<div class="req-actions">' +
        (status === 'new'
          ? '<button class="req-btn primary" data-act="toggle" data-type="paper_feedback" data-id="' + r.id + '" data-next="read">Mark Read</button>'
          : '<button class="req-btn" data-act="toggle" data-type="paper_feedback" data-id="' + r.id + '" data-next="new">Mark New</button>') +
        '<button class="req-btn danger" data-act="delete" data-type="paper_feedback" data-id="' + r.id + '">Delete</button>' +
      '</div></div>';
  }
  function loadPaperStats(){
    var host = document.getElementById('paperStats');
    if(!host) return;
    fetch('/api/admin/paper-feedback/stats')
      .then(function(r){ return r.json(); })
      .then(function(d){
        if(!d || !d.ok){ host.style.display = 'none'; return; }
        host.innerHTML = renderPaperStatsHTML(d);
      })
      .catch(function(){ host.style.display = 'none'; });
  }
  function renderPaperStatsHTML(d){
    if(!d.total){
      return '<div class="pb-head"><h3>Most-Flagged Questions</h3><span class="pb-total">No feedback yet</span></div><div class="pb-empty">Waiting for student submissions…</div>';
    }
    function bar(label, count, max){
      var pct = max ? Math.round((count / max) * 100) : 0;
      return '<div class="pb-row">' +
        '<span class="pb-label">' + esc(label) + '</span>' +
        '<span class="pb-track"><span class="pb-fill" style="width:' + pct + '%"></span></span>' +
        '<span class="pb-count">' + count + '</span>' +
      '</div>';
    }
    function section(title, list, pre){
      if(!list || !list.length) return '<div class="pb-section"><h4>' + title + '</h4><div class="pb-empty">—</div></div>';
      var max = list[0].count;
      return '<div class="pb-section"><h4>' + title + '</h4>' +
        list.map(function(x){ return bar(pre + x.q, x.count, max); }).join('') +
      '</div>';
    }
    var html = '<div class="pb-head"><h3>Most-Flagged Questions · All Papers</h3>' +
      '<span class="pb-total">' + d.total + ' response' + (d.total === 1 ? '' : 's') + '</span></div>';
    html += '<div class="pb-grid">';
    html += section('MCQ', d.mcq, 'Q');
    html += section('Structured Essay', d.structured, 'Q');
    html += section('Essay', d.essays, '');
    html += '</div>';
    return html;
  }
  function bindActions(){
    reqGrid.querySelectorAll('[data-act]').forEach(function(btn){
      btn.addEventListener('click', function(){
        var act = btn.dataset.act, type = btn.dataset.type, id = btn.dataset.id;
        if(act === 'delete'){
          if(!confirm('Delete ' + type + ' #' + id + '?')) return;
          fetch('/api/admin/data/' + type + '/' + id, { method: 'DELETE' })
            .then(function(r){ return r.json(); })
            .then(function(d){ if(d.ok){ showToast('Deleted #' + id); loadAll(); } })
            .catch(function(){ showToast('Delete failed', true); });
        } else if(act === 'toggle'){
          var next = btn.dataset.next;
          fetch('/api/admin/data/' + type + '/' + id, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: next })
          })
          .then(function(r){ return r.json(); })
          .then(function(d){ if(d.ok){ showToast('Updated #' + id); loadAll(); } })
          .catch(function(){ showToast('Update failed', true); });
        } else if(act === 'paper-status'){
          var nextPaperStatus = btn.dataset.next;
          fetch('/api/admin/papers/' + id, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: nextPaperStatus })
          })
          .then(function(r){ return r.json(); })
          .then(function(d){ if(d.ok){ showToast('Paper #' + id + ' · ' + nextPaperStatus); loadAll(); } })
          .catch(function(){ showToast('Update failed', true); });
        } else if(act === 'paper-delete'){
          if(!confirm('Delete paper #' + id + ' AND all its feedback?')) return;
          fetch('/api/admin/papers/' + id, { method: 'DELETE' })
            .then(function(r){ return r.json(); })
            .then(function(d){ if(d.ok){ showToast('Paper #' + id + ' deleted'); loadAll(); } })
            .catch(function(){ showToast('Delete failed', true); });
        }
      });
    });
  }
  document.querySelectorAll('.tab').forEach(function(t){
    t.addEventListener('click', function(){
      document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('on'); });
      t.classList.add('on');
      activeTab = t.dataset.tab;
      renderList();
      if(['news','sessions','motivations','papers'].indexOf(activeTab) === -1){ closeCreate(); }
      setTimeout(updateCreateVisibility, 10);
    });
  });
  var searchInput = document.getElementById('searchInput');
  var searchTimer = null;
  searchInput.addEventListener('input', function(){
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function(){ search = searchInput.value.trim(); renderList(); }, 160);
  });
  document.getElementById('exportBtn').addEventListener('click', function(){
    var items = STORE[activeTab] || [];
    if(!items.length){ showToast('Nothing to export', true); return; }
    var keys = {};
    items.forEach(function(r){ Object.keys(r).forEach(function(k){ keys[k] = true; }); });
    var headers = Object.keys(keys);
    var rows = [headers.join(',')];
    items.forEach(function(r){
      rows.push(headers.map(function(h){
        var v = r[h] == null ? '' : String(r[h]).replace(/"/g,'""').replace(/\n/g,' ');
        return '"' + v + '"';
      }).join(','));
    });
    var csv = rows.join('\n');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'sr-physics-' + activeTab + '-' + new Date().toISOString().slice(0,10) + '.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported ' + items.length + ' items');
  });
  document.getElementById('refreshBtn').addEventListener('click', function(){ showToast('Refreshing...'); loadAll(); });
  document.getElementById('logoutBtn').addEventListener('click', function(){
    fetch('/api/admin/logout', { method: 'POST' }).then(function(){
      dash.classList.remove('on');
      loginWrap.style.display = 'flex';
      pwInput.value = '';
      pwInput.focus();
      loginBtn.disabled = false;
      loginBtn.textContent = 'Unlock Console';
    });
  });
  function updateCreateVisibility(){
    var creatable = ['news','sessions','motivations','papers'];
    var shouldShow = creatable.indexOf(activeTab) >= 0;
    var openBtn = document.getElementById('openCreateBtn');
    if(!shouldShow){ closeCreate(); if(openBtn) openBtn.style.display = 'none'; return; }
    if(openBtn) openBtn.style.display = 'inline-block';
    document.querySelectorAll('.cf').forEach(function(cf){
      cf.style.display = (cf.dataset.cf === activeTab) ? '' : 'none';
    });
    createTitle.textContent = 'Add ' + activeTab.charAt(0).toUpperCase() + activeTab.slice(1, -1);
    if(createOpen) createWrap.classList.add('on');
  }
  (function(){
    var ctrls = document.querySelector('.dash-controls');
    var btn = document.createElement('button');
    btn.className = 'dash-export';
    btn.id = 'openCreateBtn';
    btn.textContent = '+ Add';
    btn.style.display = 'none';
    btn.addEventListener('click', function(){
      createOpen = !createOpen;
      createWrap.classList.toggle('on', createOpen);
      if(createOpen) updateCreateVisibility();
    });
    ctrls.appendChild(btn);
  })();
  function closeCreate(){ createOpen = false; createWrap.classList.remove('on'); }
  document.getElementById('createClose').addEventListener('click', closeCreate);
  document.getElementById('createCancel').addEventListener('click', closeCreate);
  document.getElementById('createSubmit').addEventListener('click', function(){
    var btn = this;
    btn.disabled = true;
    var payload = {}, endpoint = '';
    if(activeTab === 'news'){
      payload = { title: document.getElementById('nwTitle').value.trim(), image_url: document.getElementById('nwImage').value.trim(), description: document.getElementById('nwDesc').value.trim() };
      if(!payload.title){ showToast('Title required', true); btn.disabled = false; return; }
      endpoint = '/api/admin/news';
    } else if(activeTab === 'sessions'){
      payload = { title: document.getElementById('ssTitle').value.trim(), youtube_url: document.getElementById('ssUrl').value.trim(), description: document.getElementById('ssDesc').value.trim() };
      if(!payload.title || !payload.youtube_url){ showToast('Title and YouTube URL required', true); btn.disabled = false; return; }
      endpoint = '/api/admin/sessions';
    } else if(activeTab === 'motivations'){
      payload = { title: document.getElementById('mtTitle').value.trim(), tiktok_url: document.getElementById('mtUrl').value.trim() };
      if(!payload.tiktok_url){ showToast('TikTok URL required', true); btn.disabled = false; return; }
      endpoint = '/api/admin/motivations';
    } else if(activeTab === 'papers'){
      payload = { name: document.getElementById('paName').value.trim(), description: document.getElementById('paDesc').value.trim() };
      if(!payload.name){ showToast('Paper name required', true); btn.disabled = false; return; }
      endpoint = '/api/admin/papers';
    }
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(function(r){ return r.json().then(function(d){ return { ok: r.ok, data: d }; }); })
    .then(function(res){
      if(res.ok && res.data.ok){
        showToast('Added #' + res.data.id);
        document.querySelectorAll('.cf input, .cf textarea').forEach(function(el){ el.value = ''; });
        closeCreate();
        loadAll();
      } else {
        showToast((res.data && res.data.error) || 'Failed', true);
      }
    })
    .catch(function(){ showToast('Network error', true); })
    .finally(function(){ btn.disabled = false; });
  });
  updateCreateVisibility();
  fetch('/api/admin/whoami')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d && d.admin){ enterDashboard(); }
      else setTimeout(function(){ pwInput.focus(); }, 200);
    })
    .catch(function(){ setTimeout(function(){ pwInput.focus(); }, 200); });
})();
</script>
</body>
</html>
"""


# ============================================================
# ROUTES
# ============================================================
@app.route("/")
def page_portfolio():
    full = page_shell(
        "Shamil Rathnayake — A/L Physics | The Leader in Delivering Results",
        PORTFOLIO_BODY, PORTFOLIO_CSS, PORTFOLIO_JS, active="home"
    )
    extra = (
        '<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js"}}</script>'
        '<script type="module">' + HERO_MODULE + '</script>'
    )
    full = full.replace("</body>", extra + "</body>")
    return Response(full, mimetype="text/html")


@app.route("/magic")
def page_magic():
    return Response(magic_shell(
        "Magic — Learn, Watch, Explore | SR Physics",
        MAGIC_HUB_BODY, active="magic", page_css=MAGIC_HUB_CSS
    ), mimetype="text/html")


@app.route("/magic/sessions")
def page_magic_sessions():
    return Response(magic_shell(
        "Sessions from Sir — Class Recordings | SR Physics",
        SESSIONS_BODY, active="sessions", page_css=SESSIONS_CSS, page_js=SESSIONS_JS
    ), mimetype="text/html")


@app.route("/magic/from-sir")
def page_magic_from_sir():
    return Response(magic_shell(
        "From Sir — Motivations | SR Physics",
        FROMSIR_BODY, active="from-sir", page_css=FROMSIR_CSS, page_js=FROMSIR_JS
    ), mimetype="text/html")


@app.route("/magic/simulations")
def page_magic_simulations():
    return Response(magic_shell(
        "Simulations — Physics in Real Time | SR Physics",
        SIMS_BODY, active="simulations", page_css=SIMS_CSS, page_js=SIMS_JS
    ), mimetype="text/html")


@app.route("/magic/visualizations")
def page_magic_visualizations():
    full = magic_shell(
        "Visualizations — See the Field Live | SR Physics",
        VIZ_BODY, active="visualizations", page_css=VIZ_CSS, page_js=VIZ_JS
    )
    extra = (
        '<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js"}}</script>'
        '<script type="module">' + VIZ_MODULE + '</script>'
    )
    full = full.replace("</body>", extra + "</body>")
    return Response(full, mimetype="text/html")


@app.route("/learn")
def redirect_learn():
    return Response('<meta http-equiv="refresh" content="0;url=/magic/simulations">', mimetype="text/html")


@app.route("/sessions")
def redirect_sessions():
    return Response('<meta http-equiv="refresh" content="0;url=/magic/sessions">', mimetype="text/html")


@app.route("/motivations")
def redirect_motivations():
    return Response('<meta http-equiv="refresh" content="0;url=/magic/from-sir">', mimetype="text/html")


@app.route("/admin")
def page_admin():
    return Response(ADMIN_HTML, mimetype="text/html")


# ---------- public submissions ----------
@app.route("/api/join-request", methods=["POST"])
def api_join():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    phone = (d.get("phone") or "").strip()
    if not name or not phone:
        return jsonify(ok=False, error="Name and phone are required"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO join_requests(name, phone, email, batch, location, message) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, phone, (d.get("email") or "").strip(), (d.get("batch") or "").strip(),
             (d.get("location") or "").strip(), (d.get("message") or "").strip()),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/comment", methods=["POST"])
def api_comment():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    message = (d.get("message") or "").strip()
    if not name or not message:
        return jsonify(ok=False, error="Name and comment are required"), 400
    try:
        rating = max(1, min(5, int(d.get("rating") or 5)))
    except Exception:
        rating = 5
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO comments(name, batch, rating, message) VALUES (%s,%s,%s,%s)",
            (name, (d.get("batch") or "").strip(), rating, message),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/complaint", methods=["POST"])
def api_complaint():
    d = request.get_json(silent=True) or {}
    message = (d.get("message") or "").strip()
    if not message:
        return jsonify(ok=False, error="Message required"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO complaints(name, contact, category, message) VALUES (%s,%s,%s,%s)",
            ((d.get("name") or "").strip(), (d.get("contact") or "").strip(),
             (d.get("category") or "").strip(), message),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/doubt", methods=["POST"])
def api_doubt():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    topic = (d.get("topic") or "").strip()
    question = (d.get("question") or "").strip()
    if not name or not topic or not question:
        return jsonify(ok=False, error="Name, topic and question are required"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO doubts(name, batch, topic, question) VALUES (%s,%s,%s,%s)",
            (name, (d.get("batch") or "").strip(), topic, question),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/paper-feedback", methods=["POST"])
def api_paper_feedback():
    d = request.get_json(silent=True) or {}

    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        paper = conn.execute(
            "SELECT * FROM papers WHERE status='published' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    if not paper:
        return jsonify(ok=False, error="No active paper"), 400

    raw_mcq = d.get("mcq") or []
    raw_struct = d.get("structured") or []
    raw_essays = d.get("essays") or []

    try:
        mcq = sorted({int(x) for x in raw_mcq if str(x).isdigit() and 1 <= int(x) <= 50})
    except Exception:
        mcq = []
    try:
        structured = sorted({int(x) for x in raw_struct if str(x).isdigit() and 1 <= int(x) <= 4})
    except Exception:
        structured = []
    valid_essays = {"6", "7", "8", "9A", "9B", "10A", "10B"}
    essays = sorted({str(x).strip() for x in raw_essays if str(x).strip() in valid_essays})

    if not (mcq or structured or essays):
        return jsonify(ok=False, error="Select at least one question"), 400

    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO paper_feedback(paper_id, name, batch, mcq, structured, essays, comment) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                paper["id"],
                (d.get("name") or "").strip(),
                (d.get("batch") or "").strip(),
                json.dumps(mcq), json.dumps(structured), json.dumps(essays),
                (d.get("comment") or "").strip(),
            ),
        )
        return jsonify(ok=True, id=cur.lastrowid)


# ---------- public reads ----------
@app.route("/api/news")
def api_news():
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        rows = conn.execute("SELECT * FROM news ORDER BY id DESC LIMIT 15").fetchall()
    return jsonify(ok=True, items=[dict(r) for r in rows])


@app.route("/api/sessions")
def api_sessions():
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        rows = conn.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
    return jsonify(ok=True, items=[dict(r) for r in rows])


@app.route("/api/motivations")
def api_motivations():
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        rows = conn.execute("SELECT * FROM motivations ORDER BY id DESC").fetchall()
    return jsonify(ok=True, items=[dict(r) for r in rows])


@app.route("/api/paper/current")
def api_paper_current():
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        row = conn.execute(
            "SELECT * FROM papers WHERE status='published' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return jsonify(ok=True, paper=None)
    return jsonify(ok=True, paper=dict(row))


# ---------- admin auth ----------
@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    d = request.get_json(silent=True) or {}
    pw = (d.get("password") or "")
    if pw == ADMIN_PASSWORD:
        session["admin"] = True
        session.permanent = True
        return jsonify(ok=True)
    return jsonify(ok=False, error="Invalid password"), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    session.pop("admin", None)
    return jsonify(ok=True)


@app.route("/api/admin/whoami")
def api_admin_whoami():
    return jsonify(admin=(session.get("admin") is True))


# ---------- admin generic ----------
def _is_admin():
    return session.get("admin") is True


@app.route("/api/admin/data/<type_>")
def api_admin_data(type_):
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    table = TYPE_TABLE.get(type_)
    if not table:
        return jsonify(ok=False, error="unknown type"), 404
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        rows = conn.execute("SELECT * FROM " + table + " ORDER BY id DESC").fetchall()
    return jsonify(ok=True, items=[dict(r) for r in rows])


@app.route("/api/admin/data/<type_>/<int:rid>", methods=["PATCH"])
def api_admin_update(type_, rid):
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    table = TYPE_TABLE.get(type_)
    if not table:
        return jsonify(ok=False, error="unknown type"), 404
    d = request.get_json(silent=True) or {}
    status = d.get("status")
    if status not in ("new", "contacted", "read", "resolved", "published", "archived"):
        return jsonify(ok=False, error="invalid status"), 400
    with db.connect() as conn:
        conn.execute("UPDATE " + table + " SET status=%s WHERE id=%s", (status, rid))
    return jsonify(ok=True)


@app.route("/api/admin/data/<type_>/<int:rid>", methods=["DELETE"])
def api_admin_delete(type_, rid):
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    table = TYPE_TABLE.get(type_)
    if not table:
        return jsonify(ok=False, error="unknown type"), 404
    with db.connect() as conn:
        conn.execute("DELETE FROM " + table + " WHERE id=%s", (rid,))
    return jsonify(ok=True)


@app.route("/api/admin/news", methods=["POST"])
def api_admin_news_create():
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    if not title:
        return jsonify(ok=False, error="Title required"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO news(title, description, image_url) VALUES (%s,%s,%s)",
            (title, (d.get("description") or "").strip(), (d.get("image_url") or "").strip()),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/admin/sessions", methods=["POST"])
def api_admin_sessions_create():
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    url = (d.get("youtube_url") or "").strip()
    if not title or not url:
        return jsonify(ok=False, error="Title and YouTube URL required"), 400
    if not extract_youtube_id(url):
        return jsonify(ok=False, error="Invalid YouTube URL"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO sessions(title, description, youtube_url) VALUES (%s,%s,%s)",
            (title, (d.get("description") or "").strip(), url),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/admin/motivations", methods=["POST"])
def api_admin_motivations_create():
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    d = request.get_json(silent=True) or {}
    url = (d.get("tiktok_url") or "").strip()
    if not url:
        return jsonify(ok=False, error="TikTok URL required"), 400
    if not extract_tiktok_id(url):
        return jsonify(ok=False, error="Invalid TikTok URL"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO motivations(title, tiktok_url) VALUES (%s,%s)",
            ((d.get("title") or "").strip(), url),
        )
        return jsonify(ok=True, id=cur.lastrowid)


# ---------- admin papers ----------
@app.route("/api/admin/papers", methods=["POST"])
def api_admin_papers_create():
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="Paper name required"), 400
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO papers(name, description) VALUES (%s,%s)",
            (name, (d.get("description") or "").strip()),
        )
        return jsonify(ok=True, id=cur.lastrowid)


@app.route("/api/admin/papers/<int:pid>", methods=["PATCH"])
def api_admin_papers_update(pid):
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    d = request.get_json(silent=True) or {}
    fields = []
    params = []
    if "status" in d and d["status"] in ("published", "archived"):
        fields.append("status=%s")
        params.append(d["status"])
    if "name" in d:
        nm = str(d["name"]).strip()
        if nm:
            fields.append("name=%s")
            params.append(nm)
    if "description" in d:
        fields.append("description=%s")
        params.append(str(d["description"]).strip())
    if not fields:
        return jsonify(ok=False, error="No fields to update"), 400
    params.append(pid)
    with db.connect() as conn:
        conn.execute("UPDATE papers SET " + ", ".join(fields) + " WHERE id=%s", params)
    return jsonify(ok=True)


@app.route("/api/admin/papers/<int:pid>", methods=["DELETE"])
def api_admin_papers_delete(pid):
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    with db.connect() as conn:
        conn.execute("DELETE FROM papers WHERE id=%s", (pid,))
        conn.execute("DELETE FROM paper_feedback WHERE paper_id=%s", (pid,))
    return jsonify(ok=True)


@app.route("/api/admin/paper-feedback/stats")
def api_admin_paper_stats():
    if not _is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    mcq_c, struct_c, essay_c = Counter(), Counter(), Counter()
    with db.connect() as conn:
        pass  # database rows support names and numeric indexes
        rows = conn.execute("SELECT * FROM paper_feedback").fetchall()
    total = 0
    for r in rows:
        total += 1
        try:
            for q in json.loads(r["mcq"] or "[]"): mcq_c[int(q)] += 1
        except Exception:
            pass
        try:
            for q in json.loads(r["structured"] or "[]"): struct_c[int(q)] += 1
        except Exception:
            pass
        try:
            for q in json.loads(r["essays"] or "[]"): essay_c[str(q)] += 1
        except Exception:
            pass
    def top(counter, limit=None):
        items = [{"q": k, "count": v} for k, v in counter.items()]
        items.sort(key=lambda x: (-x["count"], str(x["q"])))
        return items[:limit] if limit else items
    return jsonify(
        ok=True, total=total,
        mcq=top(mcq_c, limit=10),
        structured=top(struct_c),
        essays=top(essay_c),
    )


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 66)
    print("  SR PHYSICS — Full Suite v4 (Final + Paper Feedback)")
    print("=" * 66)
    print("  Portfolio         :  http://127.0.0.1:5000/")
    print("  ✦ Magic Hub       :  http://127.0.0.1:5000/magic")
    print("  ✦ Sessions        :  http://127.0.0.1:5000/magic/sessions")
    print("  ✦ From Sir        :  http://127.0.0.1:5000/magic/from-sir")
    print("  ✦ Simulations     :  http://127.0.0.1:5000/magic/simulations")
    print("  ✦ Visualizations  :  http://127.0.0.1:5000/magic/visualizations")
    print("  P6 Console        :  http://127.0.0.1:5000/admin")
    print("  Password          :  Set in ADMIN_PASSWORD environment variable")
    print("  Database          :  " + DB_PATH)
    print("=" * 66 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)