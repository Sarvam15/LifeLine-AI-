import streamlit as st
import time
import random
import base64
import requests as req
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(
    page_title="LifeLine AI",
    page_icon="🚑",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Logo — load from local app dir (CWD = artifacts/lifeline-ai when running) ─
@st.cache_data
def get_logo_b64():
    import os
    # Try local copy first (most reliable), then fallback paths
    for path in ["lifeline_logo.png",
                 "attached_assets/lifeline_1778581593885.png",
                 "../../attached_assets/lifeline_1778581593885.png"]:
        try:
            full = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
            with open(full, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            pass
    return ""

LOGO_B64 = get_logo_b64()

# ─── Road routing via OSRM ─────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_road_route(lat1, lon1, lat2, lon2):
    try:
        url = (f"http://router.project-osrm.org/route/v1/driving/"
               f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson")
        resp = req.get(url, timeout=5)
        coords = resp.json()["routes"][0]["geometry"]["coordinates"]
        return [[c[1], c[0]] for c in coords]
    except Exception:
        return [[lat1, lon1], [lat2, lon2]]

# ─── Session State ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "phase":             "splash",
        "splash_start":      time.time(),
        "dark":              False,
        "service":           None,
        "symptom":           "",
        "stage":             0,
        "claimed":           False,
        "start_ts":          None,
        "driver":            None,
        "hospital":          None,
        "eta_pickup":        None,
        "eta_hosp_min":      None,
        "route_coords":      None,
        "amb_start_lat":     None,
        "amb_start_lon":     None,
        "hospital_reply":    None,
        "condition_sent_ts": None,
        "reply_shown":       False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
dark = st.session_state.dark

# ─── Color Tokens ─────────────────────────────────────────────────────────────
if dark:
    BG="#0D0D0F"; BG2="#1C1C1E"; BG3="#2C2C2E"
    TEXT="#F5F5F7"; TEXT2="#EBEBF5"; MUTED="#636366"
    BORDER="#38383A"; RED="#FF453A"; BLUE="#0A84FF"
    GREEN="#32D74B"; ORANGE="#FF9F0A"; SURFACE="#1C1C1E"
    CARD_SH="0 2px 20px rgba(0,0,0,0.55)"
    MAP_TILE="CartoDB dark_matter"
else:
    BG="#FFFFFF"; BG2="#F5F5F7"; BG3="#E5E5EA"
    TEXT="#1D1D1F"; TEXT2="#3A3A3C"; MUTED="#86868B"
    BORDER="#D1D1D6"; RED="#FF3B30"; BLUE="#007AFF"
    GREEN="#34C759"; ORANGE="#FF9500"; SURFACE="#FFFFFF"
    CARD_SH="0 2px 16px rgba(0,0,0,0.08),0 0 0 1px rgba(0,0,0,0.04)"
    MAP_TILE="CartoDB positron"

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif!important;background:{BG}!important;color:{TEXT}!important;}}
[data-testid="stApp"]{{background:{BG}!important;}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding-top:2rem;padding-bottom:4rem;max-width:680px;}}
section[data-testid="stSidebar"]{{display:none;}}

/* ── Card ── */
.ll-card{{background:{SURFACE};border-radius:20px;box-shadow:{CARD_SH};padding:22px 26px;margin-bottom:16px;border:1px solid {BORDER};}}

/* ── Typography ── */
.ll-wordmark{{font-size:11px;font-weight:800;letter-spacing:.18em;color:{RED};text-transform:uppercase;margin-bottom:2px;}}
.ll-title{{font-size:30px;font-weight:800;color:{TEXT};letter-spacing:-.6px;line-height:1.1;margin:0 0 4px 0;}}
.ll-sub{{font-size:14px;color:{MUTED};margin:0 0 16px 0;}}
.ll-label{{font-size:11px;font-weight:700;letter-spacing:.10em;color:{MUTED};text-transform:uppercase;margin-bottom:10px;}}
.ll-muted{{font-size:13px;color:{MUTED};}}

/* ── Live pill ── */
.ll-live{{display:inline-flex;align-items:center;gap:6px;background:{'rgba(50,215,75,.12)' if dark else 'rgba(52,199,89,.10)'};border:1px solid {'rgba(50,215,75,.25)' if dark else 'rgba(52,199,89,.2)'};color:{GREEN};font-size:12px;font-weight:600;padding:4px 12px;border-radius:100px;}}
.ll-live-dot{{width:6px;height:6px;border-radius:50%;background:{GREEN};animation:blink 1.4s ease infinite;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}

/* ── Page fade-in — JS triggers this by toggling a class ── */
@keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.page-content{{opacity:0;}}
.page-content.visible{{animation:fadeUp .4s ease forwards;}}

/* ── Splash — uses native Streamlit layout, not fixed overlay ── */
.splash-page{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-height:85vh;background:#000;border-radius:0;
  padding:40px;
}}
.splash-logo-img{{
  width:min(260px,55vw);
  animation:logoIn .7s cubic-bezier(.34,1.56,.64,1) forwards;
}}
.splash-tagline{{
  color:rgba(255,255,255,.5);font-size:13px;font-weight:500;
  letter-spacing:.18em;text-transform:uppercase;margin-top:22px;
  animation:logoIn .7s ease .3s both;
}}
.splash-dots{{display:flex;gap:8px;margin-top:26px;animation:logoIn .5s ease .5s both;}}
.splash-dot{{
  width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.7);
}}
@keyframes logoIn{{from{{opacity:0;transform:scale(.82)}}to{{opacity:1;transform:scale(1)}}}}

/* ── Service tile buttons ── */
.svc-wrap{{margin-bottom:2px;}}
.svc-wrap > div[data-testid="stButton"] > button {{
  background:{BG2} !important;
  border:1.5px solid {BORDER} !important;
  border-radius:18px !important;
  padding:20px 22px !important;
  width:100% !important;
  min-height:96px !important;
  height:auto !important;
  text-align:left !important;
  white-space:pre-wrap !important;
  font-size:14px !important;
  font-weight:500 !important;
  color:{TEXT} !important;
  line-height:1.65 !important;
  box-shadow:{CARD_SH} !important;
  margin-bottom:12px !important;
  transition:transform .18s ease, border-color .18s ease, background .18s ease, box-shadow .18s ease !important;
  cursor:pointer !important;
}}
.svc-wrap > div[data-testid="stButton"] > button:hover {{
  border-color:{RED} !important;
  background:{'rgba(255,69,58,.07)' if dark else 'rgba(255,59,48,.05)'} !important;
  transform:translateX(5px) !important;
  box-shadow:0 6px 28px rgba(255,59,48,.20) !important;
}}
.svc-wrap > div[data-testid="stButton"] > button:active {{
  transform:translateX(2px) scale(.985) !important;
  box-shadow:0 2px 10px rgba(255,59,48,.15) !important;
}}

/* ── Primary button ── */
div[data-testid="stButton"] > button[kind="primary"]{{
  background:linear-gradient(145deg,{RED},{'#CC3A30' if dark else '#D93025'})!important;
  color:#fff!important;border:none!important;border-radius:16px!important;
  font-size:17px!important;font-weight:700!important;padding:16px!important;
  width:100%!important;box-shadow:0 4px 20px rgba(255,59,48,.35)!important;
  transition:all .18s ease!important;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(255,59,48,.45)!important;}}
div[data-testid="stButton"] > button[kind="primary"]:active{{transform:translateY(0) scale(.97)!important;}}

/* ── Secondary button ── */
div[data-testid="stButton"] > button[kind="secondary"]{{
  background:{BG2}!important;color:{TEXT}!important;
  border:1.5px solid {BORDER}!important;border-radius:14px!important;
  font-size:15px!important;font-weight:500!important;padding:14px!important;
  width:100%!important;transition:all .18s ease!important;
}}
div[data-testid="stButton"] > button[kind="secondary"]:hover{{border-color:{BLUE}!important;transform:translateY(-1px)!important;}}

/* ── SOS ring ── */
.sos-wrap{{display:flex;flex-direction:column;align-items:center;padding:24px 0 8px 0;}}
.sos-outer{{width:190px;height:190px;border-radius:50%;background:{'rgba(255,69,58,.07)' if dark else 'rgba(255,59,48,.06)'};display:flex;align-items:center;justify-content:center;animation:pulse-ring 2.2s ease-in-out infinite;}}
.sos-mid{{width:150px;height:150px;border-radius:50%;background:{'rgba(255,69,58,.12)' if dark else 'rgba(255,59,48,.11)'};display:flex;align-items:center;justify-content:center;}}
.sos-circle{{width:114px;height:114px;border-radius:50%;background:linear-gradient(145deg,{RED},{'#CC3A30' if dark else '#D93025'});display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 10px 36px rgba(255,59,48,.50);}}
.sos-txt{{font-size:28px;font-weight:900;color:#fff;letter-spacing:3px;line-height:1;}}
.sos-hint{{font-size:9px;font-weight:600;color:rgba(255,255,255,.7);letter-spacing:1.8px;text-transform:uppercase;margin-top:4px;}}
@keyframes pulse-ring{{0%,100%{{transform:scale(1);opacity:1}}50%{{transform:scale(1.06);opacity:.8}}}}

/* ── Steps ── */
.step-row{{display:flex;align-items:flex-start;gap:14px;margin-bottom:14px;}}
.dot-done{{width:28px;height:28px;border-radius:50%;background:{GREEN};display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 0 5px {'rgba(50,215,75,.15)' if dark else 'rgba(52,199,89,.12)'};}}
.dot-active{{width:28px;height:28px;border-radius:50%;background:{ORANGE};display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 0 5px {'rgba(255,159,10,.2)' if dark else 'rgba(255,149,0,.15)'};animation:pdot 1.4s ease infinite;}}
.dot-wait{{width:28px;height:28px;border-radius:50%;background:{BG3};display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.dot-alert{{width:28px;height:28px;border-radius:50%;background:{RED};display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 0 5px rgba(255,59,48,.22);animation:pdot .9s ease infinite;}}
@keyframes pdot{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.15)}}}}
.di{{font-size:12px;line-height:1;color:#fff;font-weight:700;}}
.tt-done{{font-size:14px;font-weight:500;color:{GREEN};padding-top:5px;line-height:1.4;}}
.tt-active{{font-size:14px;font-weight:600;color:{ORANGE};padding-top:5px;line-height:1.4;}}
.tt-wait{{font-size:14px;font-weight:400;color:{BG3};padding-top:5px;line-height:1.4;}}
.tt-alert{{font-size:14px;font-weight:700;color:{RED};padding-top:5px;line-height:1.4;}}

/* ── Banners ── */
.alert-red{{background:linear-gradient(135deg,{RED} 0%,{'#A63228' if dark else '#C41E17'} 100%);border-radius:16px;padding:15px 20px;display:flex;align-items:center;gap:12px;margin-bottom:16px;box-shadow:0 4px 20px rgba(255,59,48,.30);}}
.alert-green{{background:linear-gradient(135deg,{GREEN} 0%,{'#248A3D' if dark else '#1F7A36'} 100%);border-radius:16px;padding:15px 20px;display:flex;align-items:center;gap:12px;margin-bottom:16px;box-shadow:0 4px 20px rgba(52,199,89,.30);}}
.alert-txt{{font-size:15px;font-weight:700;color:#fff;line-height:1.45;}}
.alert-sub{{font-weight:400;font-size:13px;opacity:.85;}}

/* ── Broadcasting badge ── */
.bcast-badge{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,59,48,.12);border:1px solid rgba(255,59,48,.25);border-radius:100px;padding:6px 14px;font-size:13px;font-weight:600;color:{RED};animation:bcast .9s ease infinite;}}
.bcast-dot{{width:8px;height:8px;border-radius:50%;background:{RED};}}
@keyframes bcast{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

/* ── ETA ── */
.eta-row{{display:flex;gap:12px;margin-bottom:0;}}
.eta-box{{flex:1;border-radius:16px;padding:16px 14px;text-align:center;border:1px solid {BORDER};background:{BG2};}}
.eta-label{{font-size:10px;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:{MUTED};margin-bottom:5px;}}
.eta-val-r{{font-size:28px;font-weight:800;color:{RED};line-height:1;}}
.eta-val-b{{font-size:28px;font-weight:800;color:{BLUE};line-height:1;}}
.eta-sub{{font-size:11px;color:{MUTED};margin-top:3px;}}

/* ── Contact ── */
.contact-row{{display:flex;align-items:center;gap:14px;margin-bottom:12px;}}
.c-icon{{width:44px;height:44px;border-radius:50%;background:{BG2};display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;border:1px solid {BORDER};}}
.c-name{{font-size:15px;font-weight:600;color:{TEXT};}}
.c-phone{{font-size:14px;color:{GREEN};font-weight:500;}}
.c-role{{font-size:12px;color:{MUTED};}}

/* ── Hospital reply bubble ── */
.hosp-reply{{
  background:{'rgba(10,132,255,.12)' if dark else 'rgba(0,122,255,.07)'};
  border:1px solid {'rgba(10,132,255,.25)' if dark else 'rgba(0,122,255,.18)'};
  border-radius:0 16px 16px 16px;padding:14px 16px;margin-top:10px;
}}
.hosp-reply-from{{font-size:11px;font-weight:700;color:{BLUE};letter-spacing:.06em;margin-bottom:6px;}}
.hosp-reply-txt{{font-size:14px;color:{TEXT2};line-height:1.65;}}

/* ── Condition card ── */
.condition-card{{background:{BG2};border-radius:16px;padding:16px 18px;margin-bottom:16px;border:1.5px solid {'rgba(10,132,255,.3)' if dark else 'rgba(0,122,255,.2)'};}}
.condition-title{{font-size:11px;font-weight:700;letter-spacing:.10em;color:{BLUE};text-transform:uppercase;margin-bottom:10px;}}

/* ── Bar ── */
.bar-bg{{background:{BG3};border-radius:100px;height:5px;width:100%;overflow:hidden;margin-top:8px;}}
.bar-fill{{height:5px;border-radius:100px;transition:width .5s ease;}}

/* ── Pill ── */
.step-pill{{display:inline-flex;align-items:center;gap:7px;background:{BG2};border:1px solid {BORDER};border-radius:100px;padding:5px 14px;font-size:12px;font-weight:600;color:{TEXT2};margin-bottom:18px;}}
.sp-dot{{width:7px;height:7px;border-radius:50%;background:{RED};}}

/* ── Confirm box ── */
.confirm-box{{background:{BG2};border-radius:14px;padding:16px 18px;margin:14px 0;border:1px solid {BORDER};font-size:14px;color:{TEXT2};line-height:1.8;}}

/* Map iframe */
iframe{{border-radius:18px!important;}}
textarea,input{{background:{BG2}!important;color:{TEXT}!important;border-color:{BORDER}!important;border-radius:12px!important;}}
</style>
""", unsafe_allow_html=True)

# ─── JS: page fade on every rerender + service button hover ───────────────────
st.markdown("""
<script>
(function() {
  // ── Page fade-in: fires on every Streamlit rerun ──
  function triggerFade() {
    document.querySelectorAll('.page-content').forEach(function(el) {
      el.classList.remove('visible');
      void el.offsetWidth; // force reflow
      el.classList.add('visible');
    });
  }
  // ── Service button hover enhancements ──
  function patchButtons() {
    document.querySelectorAll('.svc-wrap button').forEach(function(btn) {
      if (btn._patched) return;
      btn._patched = true;
      btn.addEventListener('mouseover', function() {
        btn.style.transform = 'translateX(5px)';
        btn.style.borderColor = '#FF3B30';
        btn.style.boxShadow = '0 6px 28px rgba(255,59,48,.22)';
      });
      btn.addEventListener('mouseout', function() {
        btn.style.transform = '';
        btn.style.borderColor = '';
        btn.style.boxShadow = '';
      });
      btn.addEventListener('mousedown', function() {
        btn.style.transform = 'translateX(2px) scale(0.985)';
      });
      btn.addEventListener('mouseup', function() {
        btn.style.transform = 'translateX(5px)';
      });
    });
  }
  var obs = new MutationObserver(function() {
    triggerFade();
    patchButtons();
  });
  obs.observe(document.body, {childList: true, subtree: true});
  setTimeout(function() { triggerFade(); patchButtons(); }, 200);
  setTimeout(function() { triggerFade(); patchButtons(); }, 800);
})();
</script>
""", unsafe_allow_html=True)

# ─── Data ─────────────────────────────────────────────────────────────────────
DRIVERS = [
    {"name":"Ravi Kumar",   "phone":"+91 98100 45612","vehicle":"MH-12 AM 4421"},
    {"name":"Suresh Mehta", "phone":"+91 97330 11829","vehicle":"DL-09 EM 7731"},
    {"name":"Arjun Singh",  "phone":"+91 99870 33451","vehicle":"KA-01 AM 2209"},
    {"name":"Priya Nair",   "phone":"+91 98205 67890","vehicle":"TN-05 EM 9902"},
    {"name":"Deepak Verma", "phone":"+91 96540 23178","vehicle":"UP-32 AM 1154"},
]
HOSPITALS = [
    {"name":"Apollo Hospitals",    "phone":"+91 1800 102 0101","eta_h":"14 min"},
    {"name":"Fortis Healthcare",   "phone":"+91 1800 111 9990","eta_h":"18 min"},
    {"name":"AIIMS Emergency",     "phone":"+91 11 2658 8500", "eta_h":"22 min"},
    {"name":"Max Super Specialty", "phone":"+91 1800 655 1111","eta_h":"16 min"},
]
GOVT = {"name":"National Emergency — GOVT Hub","phone":"112"}
SVCS = {
    "PUBLIC":  {"icon":"🏛️","label":"Public",  "tag":"FREE",
                "desc":"Government-operated ambulance from nearest civic hub. No charges.",
                "eta":"12–20 min","lo":18,"hi":28,"prob":.60,"p_lo":12,"p_hi":20},
    "FASTEST": {"icon":"⚡","label":"Fastest", "tag":"PRIORITY",
                "desc":"AI-priority dispatch — nearest paramedic, zero wait.",
                "eta":"5–9 min","lo":5,"hi":15,"prob":.85,"p_lo":5,"p_hi":9},
    "PRIVATE": {"icon":"🏥","label":"Private", "tag":"PAID",
                "desc":"Network-partner hospital dispatches a fully-equipped private unit.",
                "eta":"8–14 min","lo":10,"hi":22,"prob":.75,"p_lo":8,"p_hi":14},
}
HOSPITAL_REPLIES = [
    "Emergency received. Our trauma team is preparing right now. Please keep the patient still, loosen any tight clothing, and make sure their airway is clear. Help is on its way — stay calm.",
    "ER team briefed and standing by. Keep the patient conscious and talking if possible. Do not give food or water. Our driver has your GPS and is en route.",
    "Alert acknowledged. ER suite is being set up as we speak. Reassure the patient — paramedics are minutes away. We will take it from here.",
    "Message received by our emergency coordinator. Please keep the patient calm and monitor their breathing. If they lose consciousness, keep them on their side. We are ready.",
    "Received and confirmed. Our critical care team is on standby. You are doing great — help is coming. Keep the patient warm and comfortable until the ambulance arrives.",
]
BASE_LAT, BASE_LON = 28.6139, 77.2090

# ─── Helpers ─────────────────────────────────────────────────────────────────
def lerp(a, b, t): return a + (b-a)*t

def get_amb_pos(elapsed, total_secs, s_lat, s_lon):
    t = min(max(elapsed/total_secs, 0), 0.97)
    t = 1-(1-t)**2
    return lerp(s_lat, BASE_LAT, t), lerp(s_lon, BASE_LON, t)

def build_map(amb_lat, amb_lon, route_coords, height=290):
    center_lat = (BASE_LAT+amb_lat)/2
    center_lon = (BASE_LON+amb_lon)/2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14,
                   tiles=MAP_TILE, attr="CartoDB",
                   zoom_control=True, scrollWheelZoom=False)
    if route_coords and len(route_coords) > 1:
        folium.PolyLine(route_coords, color=RED, weight=4,
                        opacity=0.85, dash_array="10 6").add_to(m)
    else:
        folium.PolyLine([[amb_lat,amb_lon],[BASE_LAT,BASE_LON]],
                        color=RED, weight=4, opacity=0.85, dash_array="10 6").add_to(m)
    folium.CircleMarker(location=[BASE_LAT, BASE_LON],
                        radius=9, color=BLUE, fill=True, fill_color=BLUE,
                        fill_opacity=0.9, weight=2.5, tooltip="Your location").add_to(m)
    folium.CircleMarker(location=[BASE_LAT, BASE_LON],
                        radius=18, color=BLUE, fill=False,
                        weight=1.5, opacity=0.35).add_to(m)
    folium.Marker(location=[amb_lat, amb_lon],
                  icon=folium.DivIcon(
                      html='<div style="font-size:28px;filter:drop-shadow(0 2px 5px rgba(0,0,0,.4));transform:translate(-14px,-14px);">🚑</div>',
                      icon_size=(28,28), icon_anchor=(0,0)),
                  tooltip="Ambulance en route").add_to(m)
    return m

def maybe_set_hospital_reply():
    """Check if enough time has passed since condition was sent; set reply."""
    if st.session_state.reply_shown:
        return
    symptom = st.session_state.symptom.strip()
    claimed = st.session_state.claimed
    # Start countdown once: condition typed AND ambulance claimed
    if claimed and symptom and st.session_state.condition_sent_ts is None:
        st.session_state.condition_sent_ts = time.time()
        # Random delay 5–8 seconds so it feels like a real response
        rng_delay = random.Random(int(st.session_state.start_ts or 0) + 77)
        st.session_state["reply_delay"] = rng_delay.uniform(5.0, 8.0)
    delay = st.session_state.get("reply_delay", 6.0)
    if (st.session_state.condition_sent_ts and
            time.time() - st.session_state.condition_sent_ts >= delay):
        rng3 = random.Random(int(st.session_state.start_ts or 0) + 42)
        st.session_state.hospital_reply = rng3.choice(HOSPITAL_REPLIES)
        st.session_state.reply_shown = True

def render_condition_and_reply(key_suffix: str):
    """Shared widget: patient condition text area + hospital reply bubble."""
    maybe_set_hospital_reply()
    st.markdown(f"""<div class="condition-card">
      <div class="condition-title">🩺 Patient Condition — Tell us while we dispatch</div>""",
                unsafe_allow_html=True)
    sym = st.text_area(
        "Condition",
        value=st.session_state.symptom,
        placeholder="e.g. Severe chest pain, difficulty breathing, patient is unconscious…",
        height=85,
        label_visibility="collapsed",
        key=f"sym_{key_suffix}",
    )
    if sym != st.session_state.symptom:
        st.session_state.symptom = sym
        # Do NOT reset the timer on edits — countdown starts on first input

    h = st.session_state.hospital
    if st.session_state.hospital_reply and h:
        st.markdown(f"""
        <div class="hosp-reply">
          <div class="hosp-reply-from">🏥 {h['name']} ER — Response</div>
          <div class="hosp-reply-txt">{st.session_state.hospital_reply}</div>
        </div>""", unsafe_allow_html=True)
    elif st.session_state.claimed and st.session_state.symptom.strip():
        st.markdown(f'<div style="font-size:12px;color:{MUTED};margin-top:8px;">⏳ Sending to ER… reply incoming in a moment</div>',
                    unsafe_allow_html=True)
    elif not st.session_state.claimed and st.session_state.symptom.strip():
        st.markdown(f'<div style="font-size:12px;color:{MUTED};margin-top:8px;">Message will be sent once ambulance is claimed</div>',
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "splash":
    elapsed_splash = time.time() - st.session_state.splash_start
    if elapsed_splash >= 3.2:
        st.session_state.phase = "service_select"
        st.rerun()

    # Full-screen black background — hide all Streamlit chrome
    st.markdown("""
    <style>
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main { background: #000 !important; }
    .block-container {
        padding-top: 0 !important; padding-bottom: 0 !important;
        padding-left: 0 !important; padding-right: 0 !important;
        max-width: 100% !important;
    }
    footer, header, #MainMenu { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Use a single full-viewport fixed HTML block — most reliable centering
    logo_src = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else None
    logo_html = (
        f'<img src="{logo_src}" style="width:240px;max-width:60vw;'
        f'animation:logoIn .7s cubic-bezier(.34,1.56,.64,1) forwards;" />'
        if logo_src else
        '<div style="font-size:72px;animation:logoIn .7s ease forwards;">🚑</div>'
    )
    st.markdown(f"""
    <div style="
      position:fixed;top:0;left:0;width:100vw;height:100vh;
      background:#000;
      display:flex;flex-direction:column;
      align-items:center;justify-content:center;
      z-index:99999;
    ">
      {logo_html}
      <div style="color:rgba(255,255,255,.45);font-size:13px;font-weight:500;
                  letter-spacing:.18em;text-transform:uppercase;margin-top:22px;
                  animation:logoIn .7s ease .3s both;">
        Emergency Response Platform
      </div>
      <div style="display:flex;gap:8px;margin-top:24px;animation:logoIn .5s ease .5s both;">
        <div style="width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.7);animation:blink 1s ease 0s infinite;"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.7);animation:blink 1s ease .22s infinite;"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.7);animation:blink 1s ease .44s infinite;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(0.35)
    st.rerun()
    st.stop()

# ─── Header ───────────────────────────────────────────────────────────────────
h1, h2 = st.columns([5,1])
with h1:
    st.markdown('<div class="ll-wordmark">LifeLine AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="ll-title">Emergency Response</div>', unsafe_allow_html=True)
    st.markdown('<div class="ll-sub">Instant ambulance dispatch, powered by AI</div>', unsafe_allow_html=True)
with h2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🌙" if not dark else "☀️", key="mode_toggle"):
        st.session_state.dark = not st.session_state.dark
        st.rerun()

now_str = datetime.now().strftime("%H:%M:%S")
st.markdown(f'<div class="ll-live"><div class="ll-live-dot"></div>SYSTEM LIVE &nbsp;·&nbsp; {now_str}</div>',
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── open page-content div — JS will add 'visible' to trigger fadeUp ──────────
st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — Service Selection
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "service_select":

    st.markdown('<div class="step-pill"><div class="sp-dot"></div>Step 1 of 2 &nbsp;·&nbsp; Choose Service</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="ll-label">Select Ambulance Service</div>', unsafe_allow_html=True)

    for key, s in SVCS.items():
        label = (f"{s['icon']}  {s['label'].upper()}  ·  {s['tag']}\n"
                 f"{s['desc']}\n"
                 f"⏱  Est. pickup: {s['eta']}  ›")
        st.markdown('<div class="svc-wrap">', unsafe_allow_html=True)
        if st.button(label, key=f"svc_{key}", use_container_width=True):
            st.session_state.service = key
            st.session_state.phase = "sos_trigger"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="ll-muted" style="text-align:center;margin-top:4px;">Tap a tile to continue.</div>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — SOS Trigger
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "sos_trigger":

    svc = SVCS[st.session_state.service]
    st.markdown(f'<div class="step-pill"><div class="sp-dot"></div>{svc["icon"]} {svc["label"]} &nbsp;·&nbsp; {svc["tag"]}</div>',
                unsafe_allow_html=True)
    st.markdown(f"""<div class="ll-card" style="text-align:center;">
      <div class="ll-label">Emergency Trigger</div>
      <div class="sos-wrap">
        <div class="sos-outer"><div class="sos-mid"><div class="sos-circle">
          <div class="sos-txt">SOS</div><div class="sos-hint">Tap below</div>
        </div></div></div>
      </div>
      <div class="ll-muted" style="margin-top:4px;">Dispatches {svc['icon']} {svc['label']} ambulance · {svc['eta']}</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([3,1])
    with c1:
        if st.button("🚨  Launch SOS", type="primary", use_container_width=True):
            rng = random.Random(int(time.time()))
            svc_cfg = SVCS[st.session_state.service]
            st.session_state.start_ts          = time.time()
            st.session_state.eta_pickup        = rng.randint(svc_cfg["p_lo"], svc_cfg["p_hi"])
            st.session_state.claimed           = False
            st.session_state.driver            = None
            st.session_state.hospital          = None
            st.session_state.eta_hosp_min      = None
            st.session_state.route_coords      = None
            st.session_state.amb_start_lat     = None
            st.session_state.amb_start_lon     = None
            st.session_state.hospital_reply    = None
            st.session_state.condition_sent_ts = None
            st.session_state.reply_shown       = False
            st.session_state.phase             = "confirming"
            st.rerun()
    with c2:
        if st.button("← Back", use_container_width=True):
            st.session_state.phase = "service_select"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 2b — Confirmation
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "confirming":

    svc = SVCS[st.session_state.service]
    elapsed = time.time() - st.session_state.start_ts
    units_pinged = min(int(elapsed * 4) + 2, 52)

    st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
      <div class="bcast-badge"><div class="bcast-dot"></div>BROADCASTING TO NEARBY UNITS</div>
      <div class="ll-muted">{units_pinged} units pinged</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="ll-card" style="text-align:center;border:1.5px solid {RED}22;">
      <div style="font-size:50px;margin-bottom:12px;">🚨</div>
      <div class="ll-title" style="font-size:22px;margin-bottom:8px;">Confirm Emergency Dispatch</div>
      <div class="ll-muted" style="margin-bottom:16px;font-size:14px;">Broadcasting is <b>already live</b> — confirming locks in your dispatch.</div>
      <div class="confirm-box" style="text-align:left;">
        <b>Service:</b> {svc['icon']} {svc['label']} · {svc['tag']}<br>
        <b>Est. pickup:</b> {svc['eta']}<br>
        <b>Location:</b> GPS coordinates locked ✓<br>
        <b>Status:</b> <span style="color:{ORANGE};font-weight:600;">● Broadcasting to {units_pinged} units…</span>
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅  YES — Confirm SOS", type="primary", use_container_width=True):
            st.session_state.phase = "running"
            st.rerun()
    with c2:
        if st.button("✗  Cancel", use_container_width=True):
            st.session_state.start_ts = None
            st.session_state.phase = "sos_trigger"
            st.rerun()

    time.sleep(1)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — Running
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "running":

    elapsed  = time.time() - st.session_state.start_ts
    svc_cfg  = SVCS[st.session_state.service]
    eta_secs = st.session_state.eta_pickup * 60

    # Ambulance start position
    if st.session_state.amb_start_lat is None:
        rng0 = random.Random(int(st.session_state.start_ts))
        st.session_state.amb_start_lat = BASE_LAT + rng0.uniform(-0.022, 0.022)
        st.session_state.amb_start_lon = BASE_LON + rng0.uniform(-0.022, 0.022)
    s_lat = st.session_state.amb_start_lat
    s_lon = st.session_state.amb_start_lon

    # Road route
    if st.session_state.route_coords is None:
        st.session_state.route_coords = get_road_route(s_lat, s_lon, BASE_LAT, BASE_LON)

    # Claim logic
    random.seed(int(st.session_state.start_ts))
    claim_delay = random.uniform(svc_cfg["lo"], svc_cfg["hi"])
    will_claim  = random.random() < svc_cfg["prob"]
    if will_claim and elapsed >= claim_delay and not st.session_state.claimed:
        st.session_state.claimed = True
        rng2 = random.Random(int(st.session_state.start_ts)+7)
        st.session_state.driver       = rng2.choice(DRIVERS)
        st.session_state.hospital     = rng2.choice(HOSPITALS)
        st.session_state.eta_hosp_min = st.session_state.eta_pickup + rng2.randint(10,20)

    if elapsed >= 30 and not st.session_state.claimed:
        st.session_state.phase = "escalated"
        st.rerun()

    stage = 0
    if elapsed >= 2: stage = 1
    if st.session_state.claimed and elapsed >= claim_delay+2: stage = 2
    if st.session_state.claimed and elapsed >= claim_delay+5: stage = 3
    if stage == 3:
        # Run reply check one last time before leaving this phase
        maybe_set_hospital_reply()
        st.session_state.phase = "done"
        st.rerun()
    st.session_state.stage = stage

    remaining = max(0, 30-int(elapsed))
    pct = min(int(elapsed/30*100), 100)
    bar_col = GREEN if st.session_state.claimed else (ORANGE if pct < 70 else RED)
    d = st.session_state.driver

    # Banner
    st.markdown(f"""<div class="alert-red">
      <span style="font-size:22px;">🚨</span>
      <div class="alert-txt">SOS ACTIVE — {svc_cfg['icon']} {svc_cfg['label']} Dispatching
        <div class="alert-sub">Broadcasting to all nearby units</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Map
    amb_lat, amb_lon = get_amb_pos(elapsed, eta_secs, s_lat, s_lon)
    route = st.session_state.route_coords or []
    if route:
        best_i, best_d = 0, float('inf')
        for i, (rl, rlo) in enumerate(route):
            d2 = (rl-amb_lat)**2 + (rlo-amb_lon)**2
            if d2 < best_d:
                best_d, best_i = d2, i
        visible_route = route[best_i:] if best_i < len(route)-1 else route
    else:
        visible_route = [[amb_lat, amb_lon], [BASE_LAT, BASE_LON]]

    fmap = build_map(amb_lat, amb_lon, visible_route)
    st_folium(fmap, use_container_width=True, height=290, returned_objects=[])
    st.markdown('<div class="ll-muted" style="text-align:center;margin-top:4px;margin-bottom:14px;font-size:12px;">🔵 Your location &nbsp;·&nbsp; 🚑 Ambulance following road route</div>',
                unsafe_allow_html=True)

    # ETAs
    pickup_rem = max(0, st.session_state.eta_pickup - int(elapsed/60))
    hosp_val   = f"{st.session_state.eta_hosp_min}" if st.session_state.eta_hosp_min else "—"
    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">Estimated Times</div>
      <div class="eta-row">
        <div class="eta-box">
          <div class="eta-label">🏠 Ambulance to You</div>
          <div class="eta-val-r">{pickup_rem}<span style="font-size:16px;font-weight:600;"> min</span></div>
          <div class="eta-sub">En route</div>
        </div>
        <div class="eta-box">
          <div class="eta-label">🏥 You to Hospital</div>
          <div class="eta-val-b">{hosp_val}<span style="font-size:16px;font-weight:600;">{'min' if st.session_state.eta_hosp_min else ''}</span></div>
          <div class="eta-sub">{'Pickup + transit' if st.session_state.eta_hosp_min else 'Awaiting claim'}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Steps
    labels = [
        "Broadcasting to nearby units",
        f"Ambulance Claimed — {d['name']}" if (d and st.session_state.claimed) else "Ambulance Claimed",
        "ER Preparing for patient" if st.session_state.claimed else "Hospital API Handshake",
        "Priority Corridor Activated",
    ]
    def shtml(idx):
        lb = labels[idx]
        if idx < stage: return f'<div class="step-row"><div class="dot-done"><span class="di">✓</span></div><div class="tt-done">Stage {idx+1} — {lb}</div></div>'
        if idx == stage: return f'<div class="step-row"><div class="dot-active"><span class="di">●</span></div><div class="tt-active">Stage {idx+1} — {lb}</div></div>'
        return f'<div class="step-row"><div class="dot-wait"><span class="di" style="color:{MUTED}">·</span></div><div class="tt-wait">Stage {idx+1} — {lb}</div></div>'

    steps = "".join(shtml(i) for i in range(4))
    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">Live Dispatch Status</div>
      {steps}
      <div style="margin-top:14px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
          <span class="ll-muted" style="font-size:12px;">Claim window</span>
          <span class="ll-muted" style="font-size:12px;">{remaining}s remaining</span>
        </div>
        <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{bar_col};"></div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Contact card
    if st.session_state.claimed and d:
        h = st.session_state.hospital
        st.markdown(f"""<div class="ll-card">
          <div class="ll-label">Ambulance Confirmed</div>
          <div class="contact-row">
            <div class="c-icon">🚑</div>
            <div><div class="c-name">{d['name']}</div>
              <div class="c-phone">{d['phone']}</div>
              <div class="c-role">Plate: <b>{d['vehicle']}</b> &nbsp;·&nbsp; En Route</div>
            </div>
          </div>
          <div class="contact-row">
            <div class="c-icon">🏥</div>
            <div><div class="c-name">{h['name']}</div>
              <div class="c-phone">{h['phone']}</div>
              <div class="c-role">Emergency Room · {h['eta_h']} from pickup</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Condition + reply (always visible)
    render_condition_and_reply("running")

    time.sleep(1)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 4 — Done
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "done":

    # Keep checking reply even in done phase (may have just arrived)
    maybe_set_hospital_reply()

    d   = st.session_state.driver
    h   = st.session_state.hospital
    svc = SVCS[st.session_state.service]
    hosp_eta = (f"{st.session_state.eta_hosp_min} min"
                if st.session_state.eta_hosp_min else (h["eta_h"] if h else "—"))
    symptom  = st.session_state.symptom or "Not specified"

    st.markdown("""<div class="alert-green">
      <span style="font-size:22px;">✅</span>
      <div class="alert-txt">Priority Corridor Activated — Help is on the way
        <div class="alert-sub">All dispatch stages completed</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Map
    s_lat = st.session_state.amb_start_lat or (BASE_LAT+0.015)
    s_lon = st.session_state.amb_start_lon or (BASE_LON+0.015)
    elapsed_total = time.time() - st.session_state.start_ts
    eta_secs = st.session_state.eta_pickup * 60
    amb_lat, amb_lon = get_amb_pos(elapsed_total, eta_secs, s_lat, s_lon)
    route = st.session_state.route_coords or [[amb_lat,amb_lon],[BASE_LAT,BASE_LON]]
    fmap = build_map(amb_lat, amb_lon, route)
    st_folium(fmap, use_container_width=True, height=290, returned_objects=[])
    st.markdown('<div class="ll-muted" style="text-align:center;margin-top:4px;margin-bottom:14px;font-size:12px;">🔵 Your location &nbsp;·&nbsp; 🚑 Ambulance en route via road</div>',
                unsafe_allow_html=True)

    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">Final ETAs</div>
      <div class="eta-row">
        <div class="eta-box">
          <div class="eta-label">🏠 Ambulance to You</div>
          <div class="eta-val-r">{st.session_state.eta_pickup}<span style="font-size:16px;font-weight:600;"> min</span></div>
          <div class="eta-sub">En route now</div>
        </div>
        <div class="eta-box">
          <div class="eta-label">🏥 You to Hospital</div>
          <div class="eta-val-b">{hosp_eta}</div>
          <div class="eta-sub">Total from now</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    labels_d = [
        "Broadcasting to nearby units",
        f"Ambulance Claimed — {d['name'] if d else 'N/A'}",
        f"ER Preparing: {symptom[:42]}{'…' if len(symptom)>42 else ''}",
        "Priority Corridor Activated",
    ]
    steps_d = "".join(
        f'<div class="step-row"><div class="dot-done"><span class="di">✓</span></div><div class="tt-done">Stage {i+1} — {labels_d[i]}</div></div>'
        for i in range(4))
    st.markdown(f'<div class="ll-card"><div class="ll-label">Dispatch Complete</div>{steps_d}</div>',
                unsafe_allow_html=True)

    if d and h:
        st.markdown(f"""<div class="ll-card">
          <div class="ll-label">Contact Exchange</div>
          <div class="contact-row">
            <div class="c-icon">🚑</div>
            <div><div class="c-name">{d['name']}</div>
              <div class="c-phone">{d['phone']}</div>
              <div class="c-role">Plate No: <b>{d['vehicle']}</b> &nbsp;·&nbsp; {svc['icon']} {svc['label']}</div>
            </div>
          </div>
          <div class="contact-row">
            <div class="c-icon">🏥</div>
            <div><div class="c-name">{h['name']}</div>
              <div class="c-phone">{h['phone']}</div>
              <div class="c-role">Emergency Room · {h['eta_h']} from pickup</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Condition + reply — always accessible and visible
    render_condition_and_reply("done")

    # If still waiting for the hospital reply, keep polling every 2s
    if (not st.session_state.reply_shown
            and st.session_state.condition_sent_ts is not None):
        time.sleep(2)
        st.rerun()

    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">While You Wait</div>
      <div style="font-size:14px;color:{TEXT2};line-height:1.9;">
        • Keep the patient calm and still<br>
        • Unlock the front door / entrance<br>
        • Do not give food or water unless directed<br>
        • Driver will call you on arrival
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button("↩  New Emergency", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k != "dark": del st.session_state[k]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — Escalated
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "escalated":

    symptom   = st.session_state.symptom or "Not specified"
    sym_short = symptom.split()[0] if symptom.strip() else "Condition"

    st.markdown(f"""<div class="ll-card" style="border:1.5px solid {ORANGE}55;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
        <span style="font-size:26px;">⚠️</span>
        <span style="font-size:17px;font-weight:700;color:{ORANGE};">ALERT: No Units Claimed in 30s</span>
      </div>
      <div style="font-size:14px;color:{TEXT2};">Force dispatching from nearest Government hub…</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="alert-red">
      <span style="font-size:22px;">🏛️</span>
      <div class="alert-txt">FORCE DISPATCHING — Nearest GOVT Hub
        <div class="alert-sub">National Emergency Coordination · Priority Override Active</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">Government Dispatch ETAs</div>
      <div class="eta-row">
        <div class="eta-box">
          <div class="eta-label">🏠 GOVT Unit to You</div>
          <div class="eta-val-r">~15<span style="font-size:16px;font-weight:600;"> min</span></div>
          <div class="eta-sub">Calculating route…</div>
        </div>
        <div class="eta-box">
          <div class="eta-label">🏥 You to Nearest ER</div>
          <div class="eta-val-b">~30<span style="font-size:16px;font-weight:600;"> min</span></div>
          <div class="eta-sub">AIIMS / Govt. Hospital</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    elapsed_esc = time.time() - st.session_state.start_ts
    rng3 = random.Random(int(st.session_state.start_ts or 0)+999)
    g_slat = BASE_LAT + rng3.uniform(-0.04, 0.04)
    g_slon = BASE_LON + rng3.uniform(-0.04, 0.04)
    t_e = min(max((elapsed_esc-30)/(15*60), 0), 0.97)
    t_e = 1-(1-t_e)**2
    g_lat = lerp(g_slat, BASE_LAT, t_e)
    g_lon = lerp(g_slon, BASE_LON, t_e)
    govt_route = get_road_route(g_slat, g_slon, BASE_LAT, BASE_LON)
    fmap2 = build_map(g_lat, g_lon, govt_route)
    st_folium(fmap2, use_container_width=True, height=290, returned_objects=[])
    st.markdown('<div class="ll-muted" style="text-align:center;margin-top:4px;margin-bottom:14px;font-size:12px;">🔵 Your location &nbsp;·&nbsp; 🚑 GOVT unit dispatched via road route</div>',
                unsafe_allow_html=True)

    steps_e = f"""
    <div class="step-row"><div class="dot-done"><span class="di">✓</span></div><div class="tt-done">Stage 1 — Broadcasting to nearby units</div></div>
    <div class="step-row"><div class="dot-alert"><span class="di">!</span></div><div class="tt-alert">Stage 2 — NO CLAIM IN 30s — Escalating to GOVT Hub</div></div>
    <div class="step-row"><div class="dot-active"><span class="di">●</span></div><div class="tt-active">Stage 3 — GOVT Unit Dispatched: ER Preparing for {sym_short}</div></div>
    <div class="step-row"><div class="dot-wait"><span class="di" style="color:{MUTED}">·</span></div><div class="tt-wait">Stage 4 — Priority Corridor (pending)</div></div>
    """
    st.markdown(f'<div class="ll-card"><div class="ll-label">Escalated Dispatch Status</div>{steps_e}</div>',
                unsafe_allow_html=True)

    st.markdown(f"""<div class="ll-card">
      <div class="ll-label">Emergency Contact</div>
      <div class="contact-row">
        <div class="c-icon">🏛️</div>
        <div><div class="c-name">{GOVT['name']}</div>
          <div class="c-phone" style="color:{RED};">{GOVT['phone']}</div>
          <div class="c-role">National Emergency · Priority Override</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    render_condition_and_reply("esc")

    if st.button("↩  New Emergency", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k != "dark": del st.session_state[k]
        st.rerun()

# ── close page-content div ────────────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<hr style="border:none;border-top:1px solid {BORDER};margin:28px 0 14px 0;">
<div style="text-align:center;">
  <div class="ll-muted">LifeLine AI · Emergency Dispatch Network</div>
  <div class="ll-muted" style="margin-top:3px;font-size:11px;">For real emergencies always call <b>112</b> · Demonstration system</div>
</div>""", unsafe_allow_html=True)
