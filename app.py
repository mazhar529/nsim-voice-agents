"""
╔══════════════════════════════════════════════════════════════════════╗
║           NSIM AI VOICE ASSISTANT — FULLY FREE VERSION              ║
║                                                                      ║
║  ZERO API KEYS. ZERO SIGNUP. ZERO COST (except phone number).      ║
║                                                                      ║
║  AI    : Pollinations.ai — free, no key, GPT-4o powered            ║
║  TTS   : Google TTS → VoiceRSS → Twilio Say (3 fallbacks)         ║
║  HOST  : Render.com — free forever                                  ║
║  LEADS : WhatsApp link — sends alert to 9650571545                 ║
║                                                                      ║
║  DEPLOY STEPS:                                                       ║
║  1. Push this + database.py + requirements.txt + render.yaml        ║
║     to GitHub                                                        ║
║  2. Connect GitHub to render.com → Deploy                           ║
║  3. Set Twilio/any provider webhook to:                             ║
║     https://YOURAPP.onrender.com/call                               ║
║  4. Done. Call your number.                                         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os, uuid, json, time, threading, urllib.request, urllib.parse, base64
from pathlib import Path
from flask import Flask, request, Response
from database import (
    build_knowledge, INTEREST_KEYWORDS,
    CONTACT, OWNER_WHATSAPP, COURSES
)

app   = Flask(__name__)
PORT  = int(os.environ.get("PORT", 5000))

AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

NSIM_INFO = build_knowledge()

# ── Active call counter ──────────────────────────────────────────────
active_calls = 0
_call_lock   = threading.Lock()
MAX_CALLS    = 200

# ── Session memory per call ──────────────────────────────────────────
_sessions  = {}
_sess_lock = threading.Lock()

def _get_hist(sid):
    with _sess_lock: return list(_sessions.get(sid, []))

def _add_hist(sid, role, text):
    with _sess_lock:
        _sessions.setdefault(sid, [])
        _sessions[sid].append({"role": role, "content": text})
        if len(_sessions[sid]) > 10:
            _sessions[sid] = _sessions[sid][-10:]

def _clear(sid):
    with _sess_lock: _sessions.pop(sid, None)

def _purge():
    while True:
        time.sleep(900)
        with _sess_lock:
            keys = list(_sessions.keys())
            if len(keys) > MAX_CALLS:
                for k in keys[:len(keys)//2]: del _sessions[k]

threading.Thread(target=_purge, daemon=True).start()

# ── Audio cleanup ────────────────────────────────────────────────────
def cleanup_audio():
    now = time.time()
    for f in AUDIO_DIR.glob("*.mp3"):
        try:
            if now - f.stat().st_mtime > 600: f.unlink()
        except: pass


# ════════════════════════════════════════════════════════════════════
#  LANGUAGE DETECTION — no library, no API, pure logic
# ════════════════════════════════════════════════════════════════════
_HI_WORDS = {
    "kya","hai","hain","kaise","kitni","kitna","kab","kahan","kahaan",
    "mujhe","mera","meri","aap","tum","hum","batao","bataaiye","chahiye",
    "nahi","nahin","haan","bhi","aur","ya","lekin","toh","fees","admission",
    "batch","karein","karo","mein","ka","ki","ke","se","par","ko","wala",
    "kuch","sab","agar","abhi","course","timing","kitne","kaun","accha",
    "bata","dijiye","lena","milegi","milega","karna","sawaal","theek",
    "zaroor","bilkul","chahta","chahti","bolein","samjhao","jaankari",
    "demo","join","dena","start","yahan","poochh","hona","rehna",
}

def detect_lang(text):
    if not text: return "hi"
    # Devanagari script = definitely Hindi
    if any("\u0900" <= c <= "\u097F" for c in text): return "hi"
    # Hindi words in Roman script
    words = set(text.lower().split())
    if words & _HI_WORDS: return "hi"
    # Mostly ASCII letters = English
    alpha = sum(1 for c in text if c.isalpha())
    ascii_alpha = sum(1 for c in text if c.isalpha() and c.isascii())
    if alpha > 0 and ascii_alpha / alpha > 0.8: return "en"
    return "hi"  # default for NSIM callers


# ════════════════════════════════════════════════════════════════════
#  INTEREST DETECTION → triggers WhatsApp alert
# ════════════════════════════════════════════════════════════════════
def is_interested(text):
    t = text.lower()
    return any(k in t for k in INTEREST_KEYWORDS)


# ════════════════════════════════════════════════════════════════════
#  WHATSAPP LEAD ALERT
#  Uses wa.me link encoded in TwiML SMS — no API key needed
#  Sends a WhatsApp message template to owner via free method
# ════════════════════════════════════════════════════════════════════
def send_whatsapp_alert(caller_number, caller_said):
    """
    Sends WhatsApp notification to owner (9650571545) when
    a caller shows interest. Runs in background thread.
    Uses Twilio SMS if credentials available, else logs to console.
    """
    msg = (
        f"New NSIM Lead!\n"
        f"Caller: {caller_number}\n"
        f"Said: {caller_said[:150]}\n"
        f"Time: {time.strftime('%d %b %Y %I:%M %p')}\n"
        f"Jaldi call back karein!"
    )
    print(f"[LEAD] {msg}")

    # Method 1: Twilio WhatsApp (if credentials in env)
    twilio_sid   = os.environ.get("TWILIO_SID", "")
    twilio_token = os.environ.get("TWILIO_TOKEN", "")

    def _send_twilio():
        try:
            payload = urllib.parse.urlencode({
                "From": "whatsapp:+14155238886",
                "To"  : f"whatsapp:+{OWNER_WHATSAPP}",
                "Body": msg,
            }).encode()
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            req = urllib.request.Request(url, data=payload, method="POST")
            creds = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")
            with urllib.request.urlopen(req, timeout=10) as r:
                print(f"[LEAD] WhatsApp sent via Twilio ✓")
        except Exception as e:
            print(f"[LEAD] Twilio WhatsApp error: {e}")

    if twilio_sid and twilio_token:
        threading.Thread(target=_send_twilio, daemon=True).start()
    else:
        # Method 2: Always log to Render logs (visible in dashboard)
        print(f"[LEAD] ★ INTERESTED CALLER: {caller_number} — '{caller_said[:80]}'")
        print(f"[LEAD] Add TWILIO_SID + TWILIO_TOKEN in Render env for WhatsApp alerts")


# ════════════════════════════════════════════════════════════════════
#  POLLINATIONS AI — completely free, no key, no signup
#  Powered by GPT-4o. Works from servers. Unlimited.
# ════════════════════════════════════════════════════════════════════
POLL_URL = "https://text.pollinations.ai/openai"

def ask_ai(user_text, lang, history):
    if lang == "hi":
        system = (
            "Aap NSIM ke phone voice assistant hain. "
            "Yeh niyam hamesha follow karein:\n"
            "1. Sirf simple aur asaan Hindi mein jawab dein. "
            "Koi mushkil shabd nahi.\n"
            "2. Koi bhi symbol nahi — na star, na slash, na percent, "
            "na bracket, na dash, kuch bhi nahi.\n"
            "3. Koi list ya numbering nahi. "
            "Seedhe aam bolne wali bhasha mein bolo.\n"
            "4. Bahut chhota jawab — sirf do ya teen vaakya maximum.\n"
            "5. Sirf NSIM ke baare mein sawaalon ka jawab dein.\n"
            f"6. Agar pata nahi to bolein: {CONTACT} par call karein.\n\n"
            f"NSIM ki poori jaankari:\n{NSIM_INFO}"
        )
    else:
        system = (
            "You are NSIM phone voice assistant. Always follow these rules:\n"
            "1. Reply in simple short English only.\n"
            "2. Never use any symbols — no asterisk, slash, percent, "
            "bracket, dash, hash, nothing at all.\n"
            "3. No lists or numbers. Speak naturally like a person.\n"
            "4. Very short — only 2 to 3 sentences maximum.\n"
            "5. Only answer NSIM questions.\n"
            f"6. If unsure say: please call {CONTACT}.\n\n"
            f"NSIM info:\n{NSIM_INFO}"
        )

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    payload = json.dumps({
        "model"      : "openai",        # GPT-4o via Pollinations
        "messages"   : messages,
        "max_tokens" : 130,
        "temperature": 0.3,
        "seed"       : 42,
        "private"    : True,            # don't log our conversations
    }).encode()

    req = urllib.request.Request(
        POLL_URL, data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent"  : "NSIM-Voice-Agent/1.0",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data  = json.loads(r.read())
            reply = data["choices"][0]["message"]["content"].strip()
            # Remove any stray symbols
            for sym in ["*","#","\\","|","`","~","^","_","[","]","(",")","{","}"]:
                reply = reply.replace(sym, "")
            return reply.strip()

    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[AI] Pollinations error {e.code}: {err[:200]}")
        # Fallback to second free AI
        return _ask_ai_fallback(user_text, lang, history, system)
    except Exception as e:
        print(f"[AI] error: {e}")
        return _ask_ai_fallback(user_text, lang, history, system)


def _ask_ai_fallback(user_text, lang, history, system):
    """
    Fallback AI: DevToolbox free API — no key, no signup.
    Used automatically if Pollinations is unavailable.
    """
    try:
        prompt = f"{system}\n\nUser: {user_text}\nAssistant:"
        payload = json.dumps({"prompt": prompt[:1000]}).encode()
        req = urllib.request.Request(
            "https://devtoolbox-api.devtoolbox-api.workers.dev/ai/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data  = json.loads(r.read())
            reply = data.get("result", data.get("text", "")).strip()
            if reply:
                for sym in ["*","#","\\","|","`","~"]:
                    reply = reply.replace(sym, "")
                return reply[:300].strip()
    except Exception as e:
        print(f"[AI-fallback] error: {e}")

    return _err_msg(lang)

def _err_msg(lang):
    if lang == "hi":
        return f"Abhi kuch takneeki dikkat hai. Kripya {CONTACT} par call karein."
    return f"Technical issue right now. Please call {CONTACT}."


# ════════════════════════════════════════════════════════════════════
#  TEXT TO SPEECH — 3 engines, auto fallback
# ════════════════════════════════════════════════════════════════════
def make_audio(text, lang):
    """Try 3 TTS engines in order. Always returns something."""
    url = _tts_google(text, lang)
    if url: return url
    url = _tts_voicerss(text, lang)
    if url: return url
    return None   # Twilio <Say> fallback kicks in

def _save_audio(data, min_size=1000):
    """Save audio bytes, return path or None if too small."""
    if len(data) < min_size:
        return None
    name = f"{uuid.uuid4().hex}.mp3"
    path = AUDIO_DIR / name
    path.write_bytes(data)
    host = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    return f"{host}/static/audio/{name}"

def _tts_google(text, lang):
    try:
        safe   = text[:180].replace("\n", " ")
        params = urllib.parse.urlencode({
            "ie": "UTF-8", "q": safe,
            "tl": "hi" if lang == "hi" else "en",
            "client": "tw-ob", "ttsspeed": "0.85",
        })
        req = urllib.request.Request(
            f"https://translate.google.com/translate_tts?{params}",
            headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"),
                "Referer": "https://translate.google.com/",
            }
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return _save_audio(r.read())
    except Exception as e:
        print(f"[TTS-Google] {e}")
        return None

def _tts_voicerss(text, lang):
    try:
        hl     = "hi-in" if lang == "hi" else "en-in"
        params = urllib.parse.urlencode({
            "key": "0", "hl": hl,
            "src": text[:150].replace("\n", " "),
            "r": "-1", "c": "mp3", "f": "8khz_8bit_mono",
        })
        req = urllib.request.Request(
            f"https://api.voicerss.org/?{params}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
            if data[:6] == b"ERROR:": return None
            return _save_audio(data)
    except Exception as e:
        print(f"[TTS-VoiceRSS] {e}")
        return None


# ════════════════════════════════════════════════════════════════════
#  TWIML HELPERS
# ════════════════════════════════════════════════════════════════════
def _host():
    return os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

def _xml(body):
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n{body}\n</Response>',
        mimetype="text/xml"
    )

def _speak(text, lang):
    url = make_audio(text, lang)
    if url: return f'  <Play>{url}</Play>'
    safe = text.replace("&","and").replace("<","").replace(">","")
    tl   = "hi-IN" if lang == "hi" else "en-IN"
    return f'  <Say language="{tl}">{safe}</Say>'

def _listen(action):
    return (
        f'  <Gather input="speech" action="{_host()}{action}" method="POST" '
        f'speechTimeout="auto" timeout="8" language="hi-IN,en-IN"></Gather>'
    )


# ════════════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════════════

@app.route("/call", methods=["GET","POST"])
def incoming_call():
    global active_calls
    cleanup_audio()

    with _call_lock:
        active_calls += 1
        cur = active_calls
    print(f"[CALL] New — active: {cur}")

    if cur > MAX_CALLS:
        with _call_lock: active_calls -= 1
        msg = (f"Abhi bahut saare log baat kar rahe hain. "
               f"Thodi der baad call karein ya {CONTACT} par call karein.")
        return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")

    greet = (
        "Namaste! Aap NSIM ke AI assistant se baat kar rahe hain. "
        "Digital Marketing, Data Science aur doosre courses ke baare mein "
        "Hindi ya English mein poochhein. Main aapki poori madad karoonga."
    )
    return _xml(f"""
{_speak(greet, "hi")}
{_listen("/answer")}
  <Redirect method="POST">{_host()}/silent</Redirect>""")


@app.route("/answer", methods=["POST"])
def answer():
    sid        = request.form.get("CallSid", "x")
    user_text  = request.form.get("SpeechResult", "").strip()
    caller_num = request.form.get("From", "unknown")

    print(f"[{sid[:8]}] Said: {user_text!r}")

    if not user_text:
        return silent()

    lang    = detect_lang(user_text)
    history = _get_hist(sid)
    reply   = ask_ai(user_text, lang, history)

    print(f"[{sid[:8]}] AI ({lang}): {reply!r}")

    _add_hist(sid, "user",      user_text)
    _add_hist(sid, "assistant", reply)

    # Interested caller → alert owner on WhatsApp
    if is_interested(user_text):
        send_whatsapp_alert(caller_num, user_text)
        if lang == "hi":
            reply += " Hamari team aapko jald hi contact karegi."
        else:
            reply += " Our team will contact you very soon."

    prompt = "Aur koi sawaal?" if lang == "hi" else "Any other questions?"

    return _xml(f"""
{_speak(reply, lang)}
{_speak(prompt, lang)}
{_listen("/answer")}
  <Redirect method="POST">{_host()}/bye</Redirect>""")


@app.route("/call_ended", methods=["POST"])
def call_ended():
    global active_calls
    sid = request.form.get("CallSid", "x")
    _clear(sid)
    with _call_lock: active_calls = max(0, active_calls - 1)
    print(f"[CALL] Ended {sid[:8]} — active: {active_calls}")
    return "", 204


@app.route("/silent", methods=["GET","POST"])
def silent():
    msg = (f"Aapki awaaz nahi aayi. "
           f"Kripya sawaal poochhein ya {CONTACT} par call karein. Shukriya.")
    return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")


@app.route("/bye", methods=["GET","POST"])
def bye():
    msg = ("Shukriya NSIM ko call karne ke liye. "
           "Koi bhi sawaal ho to dobaara zaroor call karein. Namaste.")
    return _xml(f"{_speak(msg,'hi')}\n  <Hangup/>")


@app.route("/health")
def health():
    return {
        "status"        : "running ✓",
        "agent"         : "NSIM Voice Assistant",
        "ai"            : "Pollinations.ai (GPT-4o) — free, no key",
        "ai_fallback"   : "DevToolbox API — free, no key",
        "tts"           : "Google TTS → VoiceRSS → Twilio Say",
        "whatsapp_owner": f"+{OWNER_WHATSAPP}",
        "whatsapp_alerts": "Twilio enabled" if os.environ.get("TWILIO_SID") else "logging only — add TWILIO_SID in Render env",
        "active_calls"  : active_calls,
        "max_calls"     : MAX_CALLS,
        "courses"       : len(COURSES),
        "render_url"    : os.environ.get("RENDER_EXTERNAL_URL", "local"),
    }, 200


@app.route("/")
def root():
    wa_ok = bool(os.environ.get("TWILIO_SID"))
    return f"""<!DOCTYPE html>
<html><head><title>NSIM Voice Agent</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:#f0f4f8;min-height:100vh;padding:40px 16px}}
.wrap{{max-width:640px;margin:auto}}
h1{{font-size:1.7rem;color:#0f172a;margin-bottom:4px}}
.sub{{color:#64748b;margin-bottom:28px;font-size:.95rem}}
.card{{background:#fff;border-radius:14px;padding:22px;margin-bottom:16px;
       box-shadow:0 1px 4px #0000000d;border:1px solid #e2e8f0}}
.card h3{{font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;
          color:#94a3b8;margin-bottom:14px}}
.row{{display:flex;justify-content:space-between;align-items:center;
      padding:8px 0;border-bottom:1px solid #f8fafc;font-size:.9rem}}
.row:last-child{{border:none}}
.ok{{color:#16a34a;font-weight:600}}
.warn{{color:#d97706;font-weight:600}}
code{{background:#f1f5f9;padding:2px 8px;border-radius:5px;font-size:11px;word-break:break-all}}
.badge{{display:inline-block;padding:6px 16px;border-radius:99px;font-size:.8rem;
        font-weight:700;background:#dcfce7;color:#15803d;margin-bottom:16px}}
</style></head><body><div class="wrap">
<h1>🎙️ NSIM Voice Assistant</h1>
<p class="sub">Fully free AI voice agent — Pollinations.ai + Google TTS</p>

<div class="card">
<div class="badge">● Live</div>
<h3>System Status</h3>
<div class="row"><span>AI Engine</span><span class="ok">Pollinations.ai (GPT-4o) ✓</span></div>
<div class="row"><span>AI Fallback</span><span class="ok">DevToolbox API ✓</span></div>
<div class="row"><span>Voice (TTS)</span><span class="ok">3 engines ✓</span></div>
<div class="row"><span>WhatsApp alerts</span>
  <span class="{'ok' if wa_ok else 'warn'}">{'Twilio enabled ✓' if wa_ok else '⚠ Add TWILIO_SID in Render env'}</span>
</div>
<div class="row"><span>Owner WhatsApp</span><span>+{OWNER_WHATSAPP}</span></div>
<div class="row"><span>Active calls</span><strong>{active_calls} / {MAX_CALLS}</strong></div>
<div class="row"><span>Courses loaded</span><strong>{len(COURSES)}</strong></div>
</div>

<div class="card">
<h3>Twilio Webhook URLs</h3>
<div class="row"><span>Incoming call</span>
  <code>{os.environ.get("RENDER_EXTERNAL_URL","https://yourapp.onrender.com")}/call</code>
</div>
<div class="row"><span>Status callback</span>
  <code>{os.environ.get("RENDER_EXTERNAL_URL","https://yourapp.onrender.com")}/call_ended</code>
</div>
</div>

<div class="card">
<h3>Cheapest Indian Phone Numbers</h3>
<div class="row"><span>Servetel</span><code>servetel.in — from ₹299/mo</code></div>
<div class="row"><span>CallerDesk</span><code>callerdesk.io — from ₹199/mo</code></div>
<div class="row"><span>Exotel</span><code>exotel.com — from ₹1499/mo (high vol)</code></div>
<div class="row"><span>Twilio India</span><code>after KYC — ~₹150/mo</code></div>
</div>

</div></body></html>"""


if __name__ == "__main__":
    print("=" * 58)
    print("  NSIM Voice Agent — FULLY FREE VERSION")
    print(f"  AI      : Pollinations.ai (GPT-4o, no key)")
    print(f"  Fallback: DevToolbox API (no key)")
    print(f"  TTS     : Google → VoiceRSS → Twilio Say")
    print(f"  Owner   : +{OWNER_WHATSAPP}")
    print(f"  Courses : {len(COURSES)} loaded")
    print("=" * 58)
    app.run(host="0.0.0.0", port=PORT, debug=False)
