"""Local frontend integration using Aiven PostgreSQL."""
import json
import os
import threading
import hmac
from urllib.parse import urlparse
import database as db
from pathlib import Path
from flask import abort, jsonify, redirect, request, send_from_directory
import p6

app = p6.app
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
_ready = False
_ready_lock = threading.Lock()

def ensure_ready():
    global _ready
    if not _ready:
        with _ready_lock:
            if not _ready:
                p6.init_db()
                _ready = True

@app.before_request
def validate_request():
    if request.path.startswith('/api/') and request.method in ('POST', 'PATCH', 'DELETE'):
        origin = request.headers.get('Origin')
        if origin and urlparse(origin).netloc != request.host:
            return jsonify(ok=False, error='Request origin is not allowed.'), 403
        empty_allowed = request.method == 'DELETE' or request.path == '/api/admin/logout'
        if empty_allowed and not request.content_length:
            return None
        if not request.is_json or not isinstance(request.get_json(silent=True), dict):
            return jsonify(ok=False, error='Send a JSON object.'), 400

@app.errorhandler(db.Error)
def database_unavailable(exc):
    # Never put credentials, SQL or student data into client-visible errors.
    app.logger.warning('Database request failed: %s', type(exc).__name__)
    return jsonify(ok=False, error='Database temporarily unavailable. Please try again shortly.'), 503, {'Retry-After': '5'}

@app.errorhandler(413)
def oversized_request(exc):
    return jsonify(ok=False, error='Request is too large.'), 413

@app.get('/healthz')
def health():
    return jsonify(ok=True)

@app.get('/api/internal/cleanup')
def scheduled_cleanup():
    secret = os.environ.get('CRON_SECRET', '')
    if not secret or not hmac.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + secret):
        return jsonify(ok=False, error='unauthorized'), 401
    ensure_ready()
    cleanup_papers()
    return jsonify(ok=True)

ASSETS = Path(__file__).resolve().parent / "assets"

def page(filename):
    return send_from_directory(ASSETS, filename)

# Replace only the HTML delivery layer, retaining p6's APIs and database schema.
for endpoint, filename in {
    "page_portfolio": "index.html",
    "page_magic": "magic.html",
    "page_magic_sessions": "sessions.html",
    "page_magic_simulations": "simulations.html",
    "page_admin": "admin.html",
}.items():
    app.view_functions[endpoint] = lambda filename=filename: page(filename)

for endpoint in ("page_magic_from_sir", "page_magic_visualizations", "redirect_motivations"):
    app.view_functions[endpoint] = lambda: redirect("/magic", code=302)

@app.get("/assets/<path:filename>")
def frontend_asset(filename):
    return page(filename)

@app.get("/papers")
def papers_page():
    return page("papers.html")

@app.get("/community")
def community_page():
    return page("community.html")

@app.get("/<filename>")
def frontend_file(filename):
    # Assets only; never expose Python, the database, or project configuration.
    if filename.endswith((".html", ".webp", ".png", ".svg", ".jpg", ".css", ".js", ".txt", ".xml")):
        return page(filename)
    abort(404)

@app.get('/api/admin/snapshot')
def admin_snapshot():
    """Refresh all dashboard sections using a single database connection."""
    if not p6._is_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    sections = ('requests', 'comments', 'complaints', 'doubts',
                'news', 'sessions', 'papers', 'paper_feedback')
    items = {}
    with db.connect() as conn:
        for section in sections:
            # Table identifiers come only from the server's fixed allowlist.
            table = p6.TYPE_TABLE[section]
            rows = conn.execute('SELECT * FROM ' + table + ' ORDER BY id DESC').fetchall()
            items[section] = [dict(row) for row in rows]
    return jsonify(ok=True, items=items)

@app.get("/api/papers")
def published_papers():
    with db.connect() as conn:
        pass
        rows = conn.execute("SELECT id,name,description,created_at FROM papers WHERE status='published' ORDER BY id DESC").fetchall()
    return jsonify(ok=True, items=[dict(row) for row in rows])

@app.post("/api/papers/<int:paper_id>/feedback")
def paper_specific_feedback(paper_id):
    """Additive endpoint: original /api/paper-feedback still retains its behavior."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="Send a JSON object."), 400
    limits = {"mcq": {str(n) for n in range(1, 51)},
              "structured": {str(n) for n in range(1, 5)},
              "essays": {"6", "7", "8", "9A", "9B", "10A", "10B"}}
    selected = {}
    for field, valid in limits.items():
        values = data.get(field, [])
        if not isinstance(values, list) or any(str(v) not in valid for v in values):
            return jsonify(ok=False, error="Invalid question selection."), 400
        selected[field] = sorted({str(v) for v in values})
        if field != "essays":
            selected[field] = sorted(int(v) for v in selected[field])
    if not any(selected.values()):
        return jsonify(ok=False, error="Select at least one question."), 400
    for field, limit in (("name", 160), ("batch", 100), ("comment", 5000)):
        value = data.get(field, "")
        if not isinstance(value, str) or len(value) > limit:
            return jsonify(ok=False, error="Invalid or overly long " + field + "."), 400
    with db.connect() as conn:
        # Lock before checking status so an archive/delete cannot race this insert.
        conn.execute("LOCK TABLE papers, paper_feedback IN EXCLUSIVE MODE")
        paper = conn.execute("SELECT id FROM papers WHERE id=%s AND status='published'", (paper_id,)).fetchone()
        if paper is None:
            return jsonify(ok=False, error="This paper is no longer open for feedback. Choose another paper."), 409
        cur = conn.execute(
            "INSERT INTO paper_feedback(paper_id,name,batch,mcq,structured,essays,comment) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (paper_id, data.get("name", "").strip(), data.get("batch", "").strip(),
             json.dumps(selected["mcq"]), json.dumps(selected["structured"]),
             json.dumps(selected["essays"]), data.get("comment", "").strip()))
        feedback_id = cur.lastrowid
    return jsonify(ok=True, id=feedback_id, paper_id=paper_id), 201

# Single current paper lifecycle, serialized in PostgreSQL.
def cleanup_papers():
    with db.connect() as conn:
        conn.execute("LOCK TABLE papers, paper_feedback IN EXCLUSIVE MODE")
        conn.execute("DELETE FROM paper_feedback WHERE paper_id NOT IN (SELECT max(id) FROM papers) OR created_at <= to_char((CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - INTERVAL '7 days', 'YYYY-MM-DD HH24:MI:SS')")
        conn.execute("DELETE FROM papers WHERE id NOT IN (SELECT max(id) FROM papers)")
        conn.execute("DELETE FROM paper_feedback WHERE paper_id IN (SELECT id FROM papers WHERE created_at <= to_char((CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - INTERVAL '7 days', 'YYYY-MM-DD HH24:MI:SS'))")
        conn.execute("DELETE FROM papers WHERE created_at <= to_char((CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - INTERVAL '7 days', 'YYYY-MM-DD HH24:MI:SS')")
        conn.execute("DELETE FROM paper_feedback WHERE paper_id IS NULL OR paper_id NOT IN (SELECT id FROM papers)")

@app.before_request
def maintain_current_paper():
    if request.path.startswith('/api/') and request.path != '/api/internal/cleanup':
        ensure_ready()
        cleanup_papers()

@app.after_request
def fresh_api(response):
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

def visible_news():
    with db.connect() as conn:
        pass
        rows = conn.execute("SELECT * FROM news WHERE status='published' ORDER BY id DESC LIMIT 15").fetchall()
    return jsonify(ok=True, items=[dict(r) for r in rows])

app.view_functions['api_news'] = visible_news

def create_single_paper():
    if not p6._is_admin():
        return jsonify(ok=False, error="unauthorized"), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('name'), str) or not data['name'].strip():
        return jsonify(ok=False, error="Paper name required"), 400
    if not isinstance(data.get('description', ''), str):
        return jsonify(ok=False, error="Invalid description"), 400
    with db.connect() as conn:
        conn.execute('LOCK TABLE papers, paper_feedback IN EXCLUSIVE MODE')
        current = conn.execute('SELECT id FROM papers ORDER BY id DESC LIMIT 1').fetchone()
        if current and data.get('replace_id') != current[0]:
            return jsonify(ok=False, error="Only one paper is allowed. Refresh and confirm replacement of the current paper and its feedback."), 409
        if not current and data.get('replace_id') is not None:
            return jsonify(ok=False, error="The paper has changed or expired. Refresh before adding your new paper."), 409
        conn.execute('DELETE FROM paper_feedback')
        conn.execute('DELETE FROM papers')
        cur = conn.execute('INSERT INTO papers(name,description) VALUES(%s,%s)', (data['name'].strip(), data.get('description','').strip()))
        paper_id = cur.lastrowid
    return jsonify(ok=True, id=paper_id)

app.view_functions['api_admin_papers_create'] = create_single_paper

def expiry_worker():
    import time
    while True:
        try:
            cleanup_papers()
        except db.Error:
            app.logger.exception('Paper cleanup will retry')
        time.sleep(60)

if __name__ == "__main__":
    ensure_ready()
    cleanup_papers()
    threading.Thread(target=expiry_worker, daemon=True).start()
    print("SR Physics: http://127.0.0.1:5000 · Admin: http://127.0.0.1:5000/admin")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
