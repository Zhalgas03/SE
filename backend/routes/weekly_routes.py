# weekly_routes.py
import json
from flask import Blueprint, request, jsonify, render_template_string, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.weekly_token import decode_weekly_payload, encode_weekly_payload
from db import get_db_connection
import os
from api.weekly_generate import generate_weekly_trip
from psycopg2.extras import RealDictCursor
import requests
import io, base64, textwrap, datetime as dt, requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

weekly_bp = Blueprint("weekly", __name__, url_prefix="/weekly")

PREVIEW_TMPL = """
<!doctype html>
<meta charset="utf-8" />
<title>Trip of the Week</title>

<div id="offer" style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; max-width: 940px; margin: 24px auto;">
  <h1 style="margin:0 0 8px 0;">{{ offer.meta.title }}</h1>
  <h2 style="margin:0 0 12px 0;">{{ offer.summary.destination }} — {{ offer.meta.duration_days }} days</h2>
  <p style="color:#555; margin:0 0 18px 0;">{{ offer.summary.teaser }}</p>

  <h3 style="margin:20px 0 10px 0;">Itinerary</h3>
  <ol style="padding-left:20px;">
  {% for day in offer.itinerary %}
    <li style="margin-bottom:8px;">
      <b>Day {{ day.day }} — {{ day.title }}</b>
      <ul style="margin:6px 0 0 16px;">
        {% for it in day["items"] %}
          <li>{{ it.time }} · {{ it.place_name }}{% if it.notes %} — {{ it.notes }}{% endif %}</li>
        {% endfor %}
      </ul>
    </li>
  {% endfor %}
  </ol>

  {% if offer.flights %}
    <h3 style="margin:18px 0 8px 0;">Flights</h3>
    <ul>
      {% for f in offer.flights %}
        <li>{{ f.origin }} → {{ f.destination }} {{ f.depart_datetime }} ({{ f.airline }}) {{ f.price }}</li>
      {% endfor %}
    </ul>
  {% endif %}

  {% if offer.hotels %}
    <h3 style="margin:18px 0 8px 0;">Hotels</h3>
    <ul>
      {% for h in offer.hotels %}
        <li>{{ h.name }}{% if h.price %} — {{ h.price }}{% endif %}</li>
      {% endfor %}
    </ul>
  {% endif %}
</div>

<div style="max-width: 940px; margin: 0 auto 24px;">
  <button id="btnSave" onclick="saveFav()" style="padding:6px 10px;">Save to favorites</button>
</div>

<script>
const FE_ORIGIN = 'http://localhost:3000';      // фронт
const INTENT_KEY = 'weekly_save_intent_v2';     // флаг намерения сохранить (sessionStorage)

// --- 1) кладём JWT из #rt=... в localStorage (домена :5001) и очищаем hash
(function bootstrap() {
  try {
    const hash = new URLSearchParams(location.hash.slice(1));
    const rt = hash.get('rt');
    if (rt) {
      localStorage.setItem('token', rt);
      history.replaceState(null, '', location.pathname + location.search);
    }
  } catch {}

  // --- 2) авто-сохранение допускаем ТОЛЬКО если вернулись ПОСЛЕ клика Save:
  //     условия: intent=save в URL + есть флаг в sessionStorage
  const params = new URLSearchParams(location.search);
  const intent = params.get('intent');
  const intentData = sessionStorage.getItem(INTENT_KEY);
  if (intent === 'save' && intentData) {
    // один тихий вызов, затем убираем флаг
    try { sessionStorage.removeItem(INTENT_KEY); } catch {}
    setTimeout(() => saveFav(true), 80); // silent=true
  }
})();

function redirectToLoginWithIntent() {
  // добавим intent=save к текущему URL, чтобы после логина вернуться и авто-сохранить
  const u = new URL(location.href);
  u.searchParams.set('intent', 'save');
  const next = encodeURIComponent(u.toString());
  window.location.href = `${FE_ORIGIN}/login?next=${next}`;
}

async function saveFav(silent = false) {
  const btn = document.getElementById('btnSave');
  let token = localStorage.getItem('token');

  if (!token) {
    // пользователь ЯВНО нажал Save → фиксируем намерение и ведём на логин
    try { sessionStorage.setItem(INTENT_KEY, JSON.stringify({ t: "{{ token }}", ts: Date.now() })); } catch {}
    redirectToLoginWithIntent();
    return;
  }

  try {
    if (!silent && btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

    const res = await fetch('/weekly/save-favorite', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ t: "{{ token }}" })
    });

    if (res.status === 401) {
      // истёк JWT → чистим и просим логин (только если это НЕ silent)
      localStorage.removeItem('token');
      if (!silent) {
        try { sessionStorage.setItem(INTENT_KEY, JSON.stringify({ t: "{{ token }}", ts: Date.now() })); } catch {}
        redirectToLoginWithIntent();
      }
      return;
    }

    const j = await res.json().catch(() => ({}));
    if (j && j.success) {
      window.location.href = `${FE_ORIGIN}/favorites?just_saved=1`;
    } else {
      if (!silent) alert((j && j.message) || 'Failed to save');
      if (!silent && btn) { btn.disabled = false; btn.textContent = 'Save to favorites'; }
    }
  } catch (e) {
    if (!silent) alert('Server error');
    if (!silent && btn) { btn.disabled = false; btn.textContent = 'Save to favorites'; }
  }
}
</script>
"""



@weekly_bp.route("/test-generate", methods=["GET"])
def test_generate():
    offer = generate_weekly_trip()
    secret = current_app.config["JWT_SECRET_KEY"]
    token = encode_weekly_payload(offer, secret, exp_days=14)

    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    preview_url = f"{base_url}/weekly/preview?t={token}"
    return jsonify(
        success=True,
        token=token,
        preview_url=preview_url,
        summary=offer["summary"]
    )

@weekly_bp.route("/preview")
def preview():
    t = request.args.get("t")
    if not t:
        return jsonify(success=False, message="Missing token"), 400
    try:
        offer = decode_weekly_payload(t, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    front_origin = current_app.config.get("FRONT_ORIGIN", "http://localhost:3000")
    return render_template_string(PREVIEW_TMPL, offer=offer, token=t, front_origin=front_origin)


@weekly_bp.route("/create-trip", methods=["POST"])
@jwt_required()
def create_trip_from_token():
    data = request.get_json(silent=True) or {}
    t = data.get("t") or request.args.get("t")
    if not t:
        return jsonify(success=False, message="Missing token"), 400

    try:
        offer = decode_weekly_payload(t, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    username = get_jwt_identity()  # из JWT -> users.username
    conn = get_db_connection()
    with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 1) найдём автора (uuid)
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        u = cur.fetchone()
        if not u:
            return jsonify(success=False, message="User not found"), 404
        user_id = u["id"]

        # 2) подготовим значения под твою схему trips
        duration_days = int(offer["meta"].get("duration_days", 3))
        trip_name = offer["summary"].get("destination", offer["meta"].get("title", "Trip"))
        teaser = offer["summary"].get("teaser", "")
        desc = f"{trip_name} — {duration_days} days. {teaser}".strip()

        # 3) вставка в trips (creator_id, name, date_start/end, description)
        cur.execute(
            """
            INSERT INTO trips (creator_id, name, date_start, date_end, description)
            VALUES (%s, %s, NOW(), NOW() + (%s || ' day')::interval, %s)
            RETURNING id
            """,
            (user_id, trip_name, duration_days, desc)
        )
        trip_id = cur.fetchone()["id"]

    return jsonify(success=True, trip_id=str(trip_id))


# --- Save to favorites (создаём запись в trips С PDF) ---
@weekly_bp.route("/save-favorite", methods=["POST"])
@jwt_required()
def save_favorite_from_token():
    data = request.get_json(silent=True) or {}
    tok = data.get("t")
    if not tok:
        return jsonify(success=False, message="Missing token"), 400

    # 1) Декодируем оффер из weekly-токена
    try:
        offer = decode_weekly_payload(tok, current_app.config["JWT_SECRET_KEY"])
    except Exception as e:
        return jsonify(success=False, message=f"Invalid token: {e}"), 400

    # 2) Рендерим PDF сервер-сайд (ReportLab)
    try:
        pdf_bytes = _render_offer_pdf(offer)
    except Exception as e:
        current_app.logger.exception("PDF render failed")
        return jsonify(success=False, message="Failed to render PDF"), 500

    # 3) Готовим метаданные для trips
    try:
        duration = int(offer.get("meta", {}).get("duration_days") or 5)
    except Exception:
        duration = 5
    name = (
        offer.get("meta", {}).get("title")
        or offer.get("summary", {}).get("destination")
        or "Trip of the Week"
    )
    today = dt.date.today()
    # date_end включительно на duration дней
    date_start = today.isoformat()
    date_end = (today + dt.timedelta(days=max(0, duration - 1))).isoformat()

    # 4) Вызываем уже существующий API, который пишет в БД и сохраняет PDF на диск
    #    ВАЖНО: прокидываем Authorization из исходного запроса, чтобы 401 не случился.
    try:
        result = _call_save_with_pdf(name=name, date_start=date_start, date_end=date_end, pdf_bytes=pdf_bytes)
    except requests.HTTPError as err:
        status = getattr(err.response, "status_code", 500)
        # если токен протух — дадим фронту понять, что надо перелогиниться
        return jsonify(success=False, message=f"Save failed", status=status), status
    except Exception as e:
        current_app.logger.exception("Save favorite (save-with-pdf) failed")
        return jsonify(success=False, message="Server error"), 500

    # 5) Возвращаем то, что отдал save-with-pdf
    if not result.get("success"):
        return jsonify(success=False, message=result.get("message") or "Failed to create trip"), 502

    return jsonify(
        success=True,
        trip_id=result.get("trip_id"),
        pdf_path=result.get("pdf_path"),
    ), 201


@weekly_bp.route("/ping", methods=["GET"])
def weekly_ping():
    return jsonify(ok=True)

@weekly_bp.route("/test-generate", methods=["GET"])
def weekly_test_generate():
    # защитим дев-ручку флагом окружения
    if os.getenv("ALLOW_WEEKLY_DEV", "1") != "1":
        return jsonify(success=False, message="Forbidden"), 403

    offer = generate_weekly_trip()
    token = encode_weekly_payload(offer, current_app.config["JWT_SECRET_KEY"], exp_days=14)
    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    preview_url = f"{base_url}/weekly/preview?t={token}"
    return jsonify(success=True, token=token, preview_url=preview_url, summary=offer.get("summary", {}))

@weekly_bp.route("/decode", methods=["GET"])
def weekly_decode():
    if os.getenv("ALLOW_WEEKLY_DEV", "1") != "1":
        return jsonify(success=False, message="Forbidden"), 403

    t = request.args.get("t")
    if not t:
        return jsonify(success=False, message="Missing token"), 400
    try:
        offer = decode_weekly_payload(t, current_app.config["JWT_SECRET_KEY"])
        return jsonify(success=True, offer=offer)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 400


def _call_save_with_pdf(name: str, date_start: str, date_end: str, pdf_bytes: bytes) -> dict:
    base_url = current_app.config.get("BASE_URL", "http://localhost:5001")
    url = f"{base_url}/api/trips/save-with-pdf"
    headers = {
        "Authorization": request.headers.get("Authorization", ""),
        "Content-Type": "application/json"
    }
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    data_url = f"data:application/pdf;base64,{pdf_b64}"
    payload = {
        "name": name,
        "date_start": date_start,
        "date_end": date_end,
        "pdf_base64": data_url
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()



def _wrap_lines(text, width=95):
    return textwrap.wrap(text, width=width) if text else [""]

def _render_offer_pdf(offer: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    margin = 56  # ~0.78"
    y = h - margin

    # Header
    title = f"Trip of the Week — {offer['summary'].get('destination','')}"
    subtitle = f"{offer['meta'].get('duration_days','?')} days — {offer['summary'].get('teaser','')}"
    c.setFont("Helvetica-Bold", 16); c.drawString(margin, y, title); y -= 20
    c.setFont("Helvetica", 11); c.drawString(margin, y, subtitle); y -= 24

    # Optional samples
    if offer.get("flights"):
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Flights sample:"); y -= 14
        c.setFont("Helvetica", 10)
        fs = offer["flights"][0]
        for line in _wrap_lines(f"{fs.get('origin','')} → {fs.get('destination','')} · {fs.get('price','')}"):
            if y < margin: c.showPage(); y = h - margin
            c.drawString(margin, y, line); y -= 12
        y -= 6
    if offer.get("hotels"):
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Hotel sample:"); y -= 14
        c.setFont("Helvetica", 10)
        hs = offer["hotels"][0]
        for line in _wrap_lines(f"{hs.get('name','')} · {hs.get('price','')}"):
            if y < margin: c.showPage(); y = h - margin
            c.drawString(margin, y, line); y -= 12
        y -= 6

    # Itinerary
    c.setFont("Helvetica-Bold", 12); c.drawString(margin, y, "Itinerary"); y -= 16
    for day in offer.get("itinerary", []):
        if y < margin + 40: c.showPage(); y = h - margin
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, f"Day {day.get('day','?')} — {day.get('title','')}"); y -= 14
        c.setFont("Helvetica", 10)
        for item in day.get("items", []):
            line = f"{item.get('time','')}  {item.get('place_name','')}"
            notes = item.get("notes","")
            for chunk in _wrap_lines(line, 95):
                if y < margin: c.showPage(); y = h - margin
                c.drawString(margin, y, f"• {chunk}"); y -= 12
            if notes:
                for chunk in _wrap_lines(f"   {notes}", 95):
                    if y < margin: c.showPage(); y = h - margin
                    c.drawString(margin, y, chunk); y -= 12
        y -= 6

    # Tips
    if offer.get("tips"):
        if y < margin + 40: c.showPage(); y = h - margin
        c.setFont("Helvetica-Bold", 11); c.drawString(margin, y, "Tips"); y -= 14
        c.setFont("Helvetica", 10)
        for tip in offer["tips"]:
            for chunk in _wrap_lines(f"• {tip}", 95):
                if y < margin: c.showPage(); y = h - margin
                c.drawString(margin, y, chunk); y -= 12

    c.showPage(); c.save()
    pdf_bytes = buf.getvalue(); buf.close()
    return pdf_bytes


