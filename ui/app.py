import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, sys, json, base64, urllib.parse
from datetime import datetime
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from dotenv import load_dotenv

load_dotenv(override=True)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import importlib.util
for mod in ["tools", "tools.database"]:
    if mod in sys.modules:
        del sys.modules[mod]

spec = importlib.util.spec_from_file_location(
    "tools.database", os.path.join(project_root, "tools", "database.py"))
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)
sys.modules["tools.database"] = db

from agents.orchestrator import BovinoOrchestrator
db.init_db()
orchestrator = BovinoOrchestrator()

# ── Clerk configuration ──────────────────────────────────────────────────────
CLERK_PUB_KEY = (
    os.getenv("CLERK_PUBLISHABLE_KEY")
    or os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") or "pk_test_c3RpcnJlZC1zbmFrZS0zNy5jbGVyay5hY2NvdW50cy5kZXYk")

def _get_frontend_api(pk: str) -> str:
    try:
        encoded = pk.split("_", 2)[-1]
        pad = 4 - len(encoded) % 4
        if pad != 4:
            encoded += "=" * pad
        decoded = base64.b64decode(encoded).decode("utf-8")
        return decoded.split("$")[0]
    except Exception:
        return "stirred-snake-37.clerk.accounts.dev"

CLERK_FRONTEND_API = os.getenv("CLERK_FRONTEND_API", _get_frontend_api(CLERK_PUB_KEY)).replace("https://", "").replace("http://", "")
CLERK_CONFIGURED = bool(os.getenv("CLERK_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"))

def get_clerk_google_oauth_url():
    import urllib.request, urllib.parse, json
    fapi = CLERK_FRONTEND_API
    pk = CLERK_PUB_KEY
    url = f"https://{fapi}/v1/client/sign_ins?_clerk_js_version=5.0.0"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {pk}"
    }
    data = urllib.parse.urlencode({
        "strategy": "oauth_google",
        "redirect_url": "http://localhost:8501",
        "action_complete_redirect_url": "http://localhost:8501"
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        res = urllib.request.urlopen(req)
        body = json.loads(res.read().decode("utf-8"))
        return body.get("response", {}).get("first_factor_verification", {}).get("external_verification_redirect_url")
    except Exception as e:
        return f"https://{fapi}/v1/oauth/google?redirect_url=http://localhost:8501"

# ── Session state ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_message = ""
    st.session_state.active_menu = "Dashboard"
    st.session_state.selected_hacienda = "Hacienda El Encanto"
    st.session_state.clerk_user = None
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": (
            "Hola! Soy **BovinoAI**, tu asistente veterinario inteligente 24/7. "
            "Menciona el ID del bovino y los sintomas para un diagnostico inmediato."
        )
    }]

st.set_page_config(
    page_title="BovinoAI Manta - Sanidad Bovina IA",
    page_icon="🐄", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',system-ui,sans-serif!important;color:#0f2942!important;background:#eaf4f8!important;}
.stApp{background:#eaf4f8!important;}
header[data-testid="stHeader"]{background:transparent!important;}
.stDeployButton,[data-testid="stToolbar"],[data-testid="manage-app-button"],footer{display:none!important;}

/* Force sidebar to always stay visible on desktop when authenticated */
@media (min-width: 768px) {
    html:not(:has(.f-login)) [data-testid="stSidebar"] {
        display: flex !important;
        transform: none !important;
        margin-left: 0 !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 18rem !important;
        min-width: 18rem !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        z-index: 99 !important;
    }
    html:not(:has(.f-login)) .stMainBlockContainer,
    html:not(:has(.f-login)) .block-container {
        margin-left: 18rem !important;
        max-width: calc(100% - 18rem) !important;
        padding-top: 20px !important;
        padding-bottom: 20px !important;
    }
}

[data-testid="stSidebar"]{background:linear-gradient(180deg,#07253a 0%,#051b2b 100%)!important;border-right:1px solid rgba(255,255,255,0.06)!important;}
[data-testid="stSidebar"] *{color:#e2e8f0!important;}
[data-testid="stSidebarContent"]{padding:0!important;}
.stSidebar .stButton>button{width:100%!important;background:transparent!important;color:#94a3b8!important;border:none!important;border-radius:10px!important;text-align:left!important;padding:9px 14px!important;font-weight:600!important;font-size:0.88rem!important;margin-bottom:2px!important;transition:all 0.15s!important;}
.stSidebar .stButton>button:hover{background:rgba(255,255,255,0.07)!important;color:#e2e8f0!important;}
.stSidebar .stButton>button[kind="primary"]{background:linear-gradient(135deg,#0284c7,#0369a1)!important;color:#fff!important;font-weight:700!important;box-shadow:0 4px 14px rgba(2,132,199,0.35)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0284c7,#0369a1)!important;color:#fff!important;border:none!important;border-radius:12px!important;font-weight:700!important;padding:10px 22px!important;box-shadow:0 4px 14px rgba(2,132,199,0.3)!important;transition:all 0.2s!important;}
.stButton>button[kind="primary"]:hover{transform:translateY(-1px)!important;box-shadow:0 8px 22px rgba(2,132,199,0.45)!important;}
.stTextArea textarea,.stTextInput input{background:#f8fafc!important;border:1.5px solid #e0ecf7!important;border-radius:12px!important;color:#0f2942!important;font-size:0.95rem!important;}
.stTabs [data-baseweb="tab-list"]{background:rgba(2,132,199,0.07)!important;border-radius:14px!important;padding:4px!important;gap:4px!important;border:1px solid rgba(2,132,199,0.13)!important;}
.stTabs [data-baseweb="tab"]{border-radius:10px!important;font-weight:700!important;color:#64748b!important;border:none!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#0284c7,#0369a1)!important;color:#fff!important;}
[data-testid="stPopover"]>div>button{background:#fff!important;border:1.5px solid #dbeafe!important;border-radius:12px!important;padding:0 12px!important;height:38px!important;font-size:1.05rem!important;color:#0f2942!important;box-shadow:0 2px 8px rgba(7,37,58,0.04)!important;transition:all 0.15s!important;white-space:nowrap!important;}
[data-testid="stPopover"]>div>button:hover{background:#f0f9ff!important;border-color:#7dd3fc!important;box-shadow:0 4px 14px rgba(2,132,199,0.14)!important;}
</style>
""", unsafe_allow_html=True)


def try_login(usr, pwd):
    user = db.authenticate_user(usr, pwd)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.auth_message = ""
        return True
    st.session_state.auth_message = "❌ Usuario o contraseña incorrectos."
    return False


def try_register(usr, name, pwd, hacienda):
    if not usr or not name or not pwd:
        st.session_state.auth_message = "❌ Completa todos los campos obligatorios."
        return False
    try:
        db.register_user(usr, name, pwd, role="Vaquero", hacienda=hacienda)
        st.session_state.auth_message = "✅ Cuenta registrada. Inicia sesión."
        return True
    except Exception as exc:
        st.session_state.auth_message = f"❌ {exc}"
        return False


# ── Clerk OAuth / Local callback ──────────────────────────────────────────────
if not st.session_state.authenticated:
    params = st.query_params
    if "clerk_auth" in params or "created_by" in params or "created_at" in params:
        try:
            uname = params.get("username", "google_user")
            fname = params.get("full_name", "Usuario Google")
            user_row = db.get_user_role(uname) or {
                "username": uname, "full_name": fname,
                "role": "Vaquero", "hacienda": "Hacienda El Encanto"}
            st.session_state.authenticated = True
            st.session_state.user = user_row
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error procesando autenticación con Google: {e}")

    if "local_auth" in params:
        try:
            action = params.get("action")
            username = params.get("username")
            password = params.get("password")
            if action == "local_login":
                if try_login(username, password):
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.query_params.clear()
            elif action == "local_register":
                full_name = params.get("full_name")
                hacienda = params.get("hacienda", "Hacienda El Encanto")
                ok = try_register(username, full_name, password, hacienda)
                st.query_params.clear()
                if ok:
                    if try_login(username, password):
                        st.rerun()
        except Exception as e:
            st.query_params.clear()
            st.error(f"Error: {e}")

# ── AUTH PAGE (PURE HTML/CSS FOR ST.MARKDOWN) ──────────
if not st.session_state.authenticated:
    google_oauth_url = get_clerk_google_oauth_url()

    auth_msg_display = ""
    if st.session_state.auth_message:
        msg_cls = "suc" if st.session_state.auth_message.startswith("✅") else "err"
        auth_msg_display = f'<div id="msg" class="{msg_cls}">{st.session_state.auth_message}</div>'
        st.session_state.auth_message = ""

    auth_html = f"""
<style>
.auth-wrapper {{
  display:flex; align-items:center; justify-content:center;
  min-height: 100vh; width: 100%;
  padding: 20px 16px;
}}
.card-container {{
  width:100%; max-width:440px;
  background:#ffffff; border-radius:28px; padding:36px 32px;
  border:1.5px solid #dbeafe;
  box-shadow:0 20px 50px rgba(7,37,58,0.07), 0 4px 14px rgba(2,132,199,0.04);
  max-height: 95vh; overflow-y: auto;
}}
.card-container::-webkit-scrollbar {{ width: 6px; }}
.card-container::-webkit-scrollbar-track {{ background: #f1f5f9; border-radius: 9999px; }}
.card-container::-webkit-scrollbar-thumb {{ background: #bae6fd; border-radius: 9999px; }}

.card-header{{text-align:center;margin-bottom:24px;}}
.logo-box{{
  width:60px;height:60px; background:linear-gradient(135deg,#0284c7,#0c4a6e);
  border-radius:20px; display:inline-flex;align-items:center;justify-content:center;
  font-size:32px; box-shadow:0 8px 22px rgba(2,132,199,0.35); margin-bottom:14px;
}}
.brand-title{{ font-family:'Outfit',sans-serif; font-size:1.85rem; font-weight:800; color:#07253a; line-height:1.1; }}
.brand-sub{{ font-size:0.85rem; color:#64748b; font-weight:600; margin-top:5px; }}

#msg{{padding:10px 14px;border-radius:12px;font-size:0.84rem;font-weight:600;margin-bottom:16px;}}
#msg.err{{background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;}}
#msg.suc{{background:#dcfce7;color:#15803d;border:1px solid #86efac;}}

.g-btn{{
  width:100%;padding:13px 16px;background:#ffffff;border:1.5px solid #dbeafe;
  border-radius:14px;display:flex;align-items:center;justify-content:center;gap:12px;
  cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.95rem;font-weight:700;
  color:#0f2942;transition:all 0.2s;margin-bottom:20px;
  box-shadow:0 2px 8px rgba(7,37,58,0.03); text-decoration:none!important;
}}
.g-btn:hover{{ background:#f0f9ff;border-color:#7dd3fc; box-shadow:0 6px 18px rgba(2,132,199,0.15);transform:translateY(-1px); }}

.divider{{display:flex;align-items:center;gap:12px;margin:18px 0;}}
.divider::before,.divider::after{{content:'';flex:1;height:1px;background:#e0ecf7;}}
.divider span{{font-size:0.8rem;color:#94a3b8;font-weight:600;white-space:nowrap;}}

.tabs-ui {{
  display:flex;gap:5px;margin-bottom:22px;background:rgba(2,132,199,0.06);
  border-radius:14px;padding:4px;border:1px solid rgba(2,132,199,0.12);
}}
.tab-lbl {{
  flex:1;padding:10px;border:none;border-radius:11px;cursor:pointer;
  font-family:'Plus Jakarta Sans',sans-serif;font-size:0.9rem;font-weight:700;
  color:#64748b;background:transparent;transition:all 0.2s; text-align: center;
}}
.form-container {{ display: none; }}

/* PURE CSS TAB LOGIC */
#tab-login:checked ~ .f-login {{ display: block; }}
#tab-register:checked ~ .f-reg {{ display: block; }}

#tab-login:checked ~ .tabs-ui .t-in {{
  background:linear-gradient(135deg,#0284c7,#0369a1);color:#ffffff;
  box-shadow:0 4px 14px rgba(2,132,199,0.32);
}}
#tab-register:checked ~ .tabs-ui .t-up {{
  background:linear-gradient(135deg,#0284c7,#0369a1);color:#ffffff;
  box-shadow:0 4px 14px rgba(2,132,199,0.32);
}}

.fld{{margin-bottom:16px;text-align:left;}}
.fld label{{display:block;font-size:0.84rem;font-weight:700;color:#0f2942;margin-bottom:6px;}}
.fld input{{
  width:100%;padding:12px 15px;background:#f8fafc;border:1.5px solid #e0ecf7;
  border-radius:13px;font-family:'Plus Jakarta Sans',sans-serif;font-size:0.94rem;color:#0f2942;
  transition:all 0.15s;outline:none; box-sizing: border-box;
}}
.fld input:focus{{border-color:#0284c7;box-shadow:0 0 0 3px rgba(2,132,199,0.12);background:#ffffff;}}

.sub{{
  width:100%;padding:14px;background:linear-gradient(135deg,#0284c7,#0369a1);
  border:none;border-radius:14px;color:#ffffff;font-family:'Plus Jakarta Sans',sans-serif;
  font-size:0.98rem;font-weight:800;cursor:pointer;transition:all 0.2s;
  box-shadow:0 4px 16px rgba(2,132,199,0.35);margin-top:8px;letter-spacing:0.3px;
}}
.sub:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(2,132,199,0.45);}}
</style>

<div class="auth-wrapper">
<div class="card-container">
  <div class="card-header">
    <div class="logo-box">🐄</div>
    <div class="brand-title">BovinoAI Manta</div>
    <div class="brand-sub">Sanidad Ganadera & IA Multiagente</div>
  </div>

  {auth_msg_display}

  <!-- Google OAuth Anchor Link -->
  <a href="{google_oauth_url}" target="_self" class="g-btn">
    <svg width="20" height="20" viewBox="0 0 48 48">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.2l6.8-6.8C35.7 2.1 30.2 0 24 0 14.8 0 6.9 5.5 3 13.5l7.9 6.1C12.8 13.5 17.9 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.2-.4-4.7H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.4 5.7c4.3-4 6.8-9.9 6.8-17.2z"/>
      <path fill="#FBBC05" d="M10.9 28.4A14.4 14.4 0 0 1 9.5 24c0-1.5.3-3 .8-4.4L2.4 13.5A23.9 23.9 0 0 0 0 24c0 3.8.9 7.4 2.4 10.5l8.5-6.1z"/>
      <path fill="#34A853" d="M24 48c6.2 0 11.4-2 15.2-5.5l-7.4-5.7c-2.1 1.4-4.7 2.2-7.8 2.2-6.1 0-11.2-4-13.1-9.5l-8.1 6.1C6.8 42.4 14.8 48 24 48z"/>
    </svg>
    <span>Continuar con Google</span>
  </a>

  <div class="divider"><span>o continúa con tu cuenta</span></div>

  <!-- PURE CSS TABS -->
  <input type="radio" id="tab-login" name="auth-tab" checked style="display:none;">
  <input type="radio" id="tab-register" name="auth-tab" style="display:none;">

  <div class="tabs-ui">
    <label for="tab-login" class="tab-lbl t-in">🔒 Iniciar Sesión</label>
    <label for="tab-register" class="tab-lbl t-up">📝 Crear Cuenta</label>
  </div>

  <!-- LOGIN FORM (Pure HTML, GET request) -->
  <div class="f-login form-container">
    <form action="" method="GET" target="_self">
      <input type="hidden" name="action" value="local_login">
      <input type="hidden" name="local_auth" value="1">
      <div class="fld"><label>Usuario</label><input type="text" name="username" placeholder="tu_usuario" required autocomplete="username"></div>
      <div class="fld"><label>Contraseña</label><input type="password" name="password" placeholder="••••••••" required autocomplete="current-password"></div>
      <button type="submit" class="sub">Ingresar al Sistema →</button>
    </form>
  </div>

  <!-- REGISTER FORM (Pure HTML, GET request) -->
  <div class="f-reg form-container">
    <form action="" method="GET" target="_self">
      <input type="hidden" name="action" value="local_register">
      <input type="hidden" name="local_auth" value="1">
      <div class="fld"><label>Usuario</label><input type="text" name="username" placeholder="usuario" required autocomplete="username"></div>
      <div class="fld"><label>Nombre completo</label><input type="text" name="full_name" placeholder="Nombre y Apellido" required autocomplete="name"></div>
      <div class="fld"><label>Contraseña</label><input type="password" name="password" placeholder="Mínimo 6 caracteres" required autocomplete="new-password"></div>
      <div class="fld"><label>Hacienda</label><input type="text" name="hacienda" placeholder="Nombre de tu hacienda" value="Hacienda El Encanto" required></div>
      <button type="submit" class="sub">Crear Cuenta →</button>
    </form>
  </div>
</div>
</div>
"""

    st.markdown("""
    <style>
    html:has(.f-login) .stApp { background: radial-gradient(circle at 50% 30%, #e0f2fe 0%, #eaf4f8 65%, #dbeafe 100%) !important; }
    html:has(.f-login) .stMainBlockContainer, html:has(.f-login) .block-container{padding:0!important;max-width:100%!important;}
    html:has(.f-login) [data-testid="stSidebar"]{display:none!important;}
    </style>""", unsafe_allow_html=True)
    
    st.markdown(auth_html, unsafe_allow_html=True)
    st.stop()


# ── Authenticated area ────────────────────────────────────────────────────────
current_user = st.session_state.user
username = current_user["username"]
current_role = current_user.get("role", "Vaquero")
animals_list = db.get_all_animals()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <style>[data-testid="stSidebarContent"]{padding:0!important;}</style>
    <div style="padding:20px 16px 14px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:8px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:46px;height:46px;background:linear-gradient(135deg,#0284c7,#0c4a6e);
          border-radius:14px;display:flex;align-items:center;justify-content:center;
          font-size:24px;box-shadow:0 6px 18px rgba(2,132,199,0.4);flex-shrink:0;">🐄</div>
        <div>
          <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:1.2rem;color:#fff;line-height:1.1;">BovinoAI</div>
          <div style="font-size:0.7rem;color:#38bdf8;font-weight:600;letter-spacing:0.5px;">Manta · IA Multiagente</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.68rem;color:#475569;font-weight:700;padding-left:16px;"
        "margin:6px 0;letter-spacing:1.2px;text-transform:uppercase;'>Menu Principal</p>",
        unsafe_allow_html=True)

    menu_items = [
        ("Dashboard",           "📊"),
        ("Mis Bovinos",         "🐄"),
        ("Escanear Bovino",     "📷"),
        ("Diagnosticos",        "🩺"),
        ("Enciclopedia",        "📖"),
        ("Mapa de Fincas",      "🗺️"),
        ("Clima y Suelo",       "🌤️"),
        ("Asistente IA",        "🤖"),
        ("Reportes",            "📈"),
        ("Mercados y Ledger",   "🔗"),
        ("Capacitacion HITL",   "👨‍⚕️"),
        ("Configuracion",       "⚙️"),
    ]
    for label, icon in menu_items:
        is_active = st.session_state.active_menu == label
        if st.button(f"{icon}  {label}", key=f"nav_{label}",
                     type="primary" if is_active else "secondary"):
            st.session_state.active_menu = label
            st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:12px 16px;'>",
                unsafe_allow_html=True)

    role_color = "#38bdf8" if current_role == "Administrador" else "#86efac" if current_role == "Veterinario" else "#fde047"
    clerk_av = (st.session_state.clerk_user or {}).get("avatar", "")
    av_html = (f'<img src="{clerk_av}" style="width:32px;height:32px;border-radius:9999px;border:2px solid #0284c7;"/>'
               if clerk_av else
               f'<div style="width:32px;height:32px;background:linear-gradient(135deg,#0284c7,#0c4a6e);border-radius:9999px;'
               f'display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;color:#fff;">'
               f'{current_user["full_name"][0].upper()}</div>')
    clerk_lbl = f'Clerk {"OAuth Google" if CLERK_CONFIGURED else "local"}'
    st.markdown(f"""
    <div style="margin:0 10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
         border-radius:14px;padding:12px 14px;">
      <div style="display:flex;align-items:center;gap:10px;">
        {av_html}
        <div>
          <div style="font-size:0.85rem;font-weight:700;color:#e2e8f0;">{current_user['full_name']}</div>
          <div style="font-size:0.7rem;color:{role_color};font-weight:600;">{current_role}</div>
        </div>
      </div>
      <div style="font-size:0.68rem;color:#64748b;margin-top:6px;">🔒 {clerk_lbl}</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesion", key="btn_logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.clerk_user = None
        st.rerun()


# ── TOP HEADER ────────────────────────────────────────────────────────────────
def top_header():
    col1, col2 = st.columns([3, 2])
    with col1:
        hora = datetime.now().hour
        saludo = "Buenos dias" if hora < 12 else "Buenas tardes" if hora < 18 else "Buenas noches"
        nombre = current_user["full_name"].split()[0]
        st.markdown(f"""
        <div style="padding:2px 0 10px 0;">
          <div style="font-size:0.7rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">
            Panel de control · {st.session_state.active_menu}
          </div>
          <div style="font-family:'Outfit',sans-serif;font-size:1.55rem;font-weight:800;color:#07253a;margin-top:3px;line-height:1.2;">
            {saludo}, {nombre} 👋
          </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        cs, cn, cu = st.columns([3, 1, 1])
        with cs:
            opts = ["Hacienda El Encanto", "Rancho San Mateo", "Finca Santa Marianita"]
            sel = st.selectbox("", opts, key="top_hac", label_visibility="collapsed")
            st.session_state.selected_hacienda = sel
        with cn:
            pending_alerts = [r for r in db.get_ledger_records() if r.get("hitl_status") == "PENDIENTE"]
            sick = [a for a in animals_list if a["current_status"] != "Saludable"]
            n_total = len(pending_alerts) + len(sick)
            badge = "🔴" if n_total > 0 else ""
            with st.popover(f"🔔{badge}", use_container_width=True):
                st.markdown(f"### 🔔 Notificaciones ({n_total})")
                if not pending_alerts and not sick:
                    st.success("Sin alertas activas")
                else:
                    if pending_alerts:
                        st.markdown("**Tickets HITL pendientes**")
                        for t in pending_alerts[:4]:
                            st.markdown(f"> Ticket **#{t['id']}** — `{t.get('animal_id','—')}` · {t.get('timestamp','')[:10]}")
                    if sick:
                        st.markdown("**Bovinos bajo atencion**")
                        for a in sick[:4]:
                            st.markdown(f"> **{a['id']}** {a['name']} — {a['current_status']}")
                    if st.button("Ver todos los tickets", key="notif_ver"):
                        st.session_state.active_menu = "Capacitacion HITL"
                        st.rerun()
        with cu:
            init = current_user["full_name"][0].upper()
            with st.popover(f"👤 {init}", use_container_width=True):
                st.markdown("### 👤 Mi perfil")
                if clerk_av:
                    st.image(clerk_av, width=54)
                st.markdown(f"""
                <div style="background:#f0f9ff;border-radius:12px;padding:13px;border:1px solid #bae6fd;margin:8px 0;">
                  <div style="font-weight:800;color:#07253a;">{current_user['full_name']}</div>
                  <div style="color:#0284c7;font-size:0.82rem;font-weight:600;margin-top:3px;">{current_role}</div>
                  <div style="color:#64748b;font-size:0.78rem;margin-top:5px;">🏡 {current_user.get('hacienda','Manta')}</div>
                  <div style="color:#64748b;font-size:0.78rem;">👤 @{username}</div>
                  <div style="color:#94a3b8;font-size:0.7rem;margin-top:4px;">🔒 {clerk_lbl}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("⚙️ Configuracion", key="prof_cfg", use_container_width=True):
                    st.session_state.active_menu = "Configuracion"
                    st.rerun()
                if st.button("🚪 Cerrar sesion", key="prof_out", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.user = None
                    st.session_state.clerk_user = None
                    st.rerun()

top_header()


def pill(text, color="blue"):
    pal = {"blue":("#e0f2fe","#0369a1","#7dd3fc"),"green":("#dcfce7","#15803d","#86efac"),
           "amber":("#fef3c7","#b45309","#fde047"),"red":("#fee2e2","#b91c1c","#fca5a5")}
    bg,fg,br = pal.get(color, pal["blue"])
    return f'<span style="background:{bg};color:{fg};border:1px solid {br};padding:3px 10px;border-radius:9999px;font-size:0.76rem;font-weight:700;">{text}</span>'


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if st.session_state.active_menu == "Dashboard":
    hora2 = datetime.now().hour
    saludo2 = "Buenos dias" if hora2 < 12 else "Buenas tardes" if hora2 < 18 else "Buenas noches"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#e0f2fe 0%,#bae6fd 60%,#e0f9ff 100%);
         border-radius:24px;padding:28px 36px 24px;border:1px solid #7dd3fc;margin-bottom:10px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;
           background:radial-gradient(circle,rgba(2,132,199,0.14) 0%,transparent 70%);border-radius:9999px;"></div>
      <div style="position:relative;z-index:1;">
        <div style="font-size:0.68rem;font-weight:800;letter-spacing:1.8px;color:#0369a1;text-transform:uppercase;margin-bottom:10px;">
          BovinoAI Manta — Plataforma Ganadera Inteligente
        </div>
        <h1 style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:#0c4a6e;margin:0 0 10px;line-height:1.2;">
          {saludo2} — Sistema activo
        </h1>
        <p style="color:#0369a1;font-size:0.95rem;margin:0;max-width:560px;line-height:1.6;">
          Sanidad bovina en tiempo real — detecta afecciones y caidas productivas antes de que el dano sea evidente.
        </p>
      </div>
    </div>""", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns([4, 1, 1])
    with cc2:
        if st.button("📷 Escanear bovino", type="primary", use_container_width=True):
            st.session_state.active_menu = "Escanear Bovino"
            st.rerun()
    with cc3:
        if st.button("🤖 Asistente IA", use_container_width=True):
            st.session_state.active_menu = "Asistente IA"
            st.rerun()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    total = len(animals_list)
    sick_n = len([a for a in animals_list if a["current_status"] != "Saludable"])
    healthy_pct = round((total - sick_n) / total * 100) if total else 100
    phitl = len([r for r in db.get_ledger_records() if r.get("hitl_status") == "PENDIENTE"])

    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, label, val, desc, icon, ibg, trend, up in [
        (sc1,"Bovinos activos",str(total),"en el sistema","🌱","#e0f2fe",f"+{total}",True),
        (sc2,"Bajo atencion",str(sick_n),"requieren revision","⚠️","#fef3c7","ver diagnosticos",False),
        (sc3,"Tickets HITL",str(phitl),"pendientes firma","🩺","#fce7f3","firma requerida",False),
        (sc4,"Indice de salud",f"{healthy_pct}%","promedio del rebano","💚","#dcfce7","estable",True),
    ]:
        tc = "#15803d" if up else "#b45309"
        with col:
            st.markdown(f"""
            <div style="background:#fff;border-radius:20px;padding:20px 22px;border:1px solid #e0ecf7;
                 box-shadow:0 4px 20px rgba(7,37,58,0.04);height:124px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
                <span style="font-size:0.8rem;font-weight:600;color:#64748b;">{label}</span>
                <div style="background:{ibg};border-radius:10px;width:34px;height:34px;
                     display:flex;align-items:center;justify-content:center;font-size:16px;">{icon}</div>
              </div>
              <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:#07253a;line-height:1;">{val}</div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
                <span style="font-size:0.75rem;color:#94a3b8;">{desc}</span>
                <span style="font-size:0.72rem;color:{tc};font-weight:700;">{trend}</span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    if sick_n > 0 or phitl > 0:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#fffbeb,#fef9c3);border:1.5px solid #fde047;
             border-radius:20px;padding:18px 22px;margin-bottom:20px;">
          <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:1rem;color:#b45309;margin-bottom:10px;">
            ⚠️ Alertas activas
            <span style="background:#fde047;color:#92400e;padding:2px 10px;border-radius:9999px;font-size:0.72rem;font-weight:800;margin-left:8px;">
              {sick_n + phitl} elementos
            </span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="background:rgba(255,255,255,0.7);border-radius:12px;padding:12px 16px;border:1px solid #fef08a;">
              <div style="font-weight:700;color:#0f2942;font-size:0.88rem;">🐄 Bovinos bajo atencion</div>
              <div style="font-size:0.8rem;color:#64748b;margin-top:4px;">{sick_n} animal(es) bajo observacion o tratamiento</div>
            </div>
            <div style="background:rgba(255,255,255,0.7);border-radius:12px;padding:12px 16px;border:1px solid #fef08a;">
              <div style="font-weight:700;color:#0f2942;font-size:0.88rem;">🩺 Tickets HITL pendientes</div>
              <div style="font-size:0.8rem;color:#64748b;margin-top:4px;">{phitl} ticket(s) esperan firma veterinaria</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    cm, cd = st.columns([1.6, 1])
    with cm:
        st.markdown('<div style="background:#fff;border-radius:20px;padding:20px;border:1px solid #e0ecf7;'
                    'box-shadow:0 4px 20px rgba(7,37,58,0.04);">'
                    '<div style="font-family:\'Outfit\',sans-serif;font-size:1rem;font-weight:800;color:#07253a;margin-bottom:12px;">🗺️ Mapa de fincas</div>',
                    unsafe_allow_html=True)
        poly = db.get_farm_perimeter(st.session_state.selected_hacienda) or [
            {"latitude":-1.055,"longitude":-80.905},{"latitude":-1.052,"longitude":-80.892},
            {"latitude":-1.062,"longitude":-80.888},{"latitude":-1.065,"longitude":-80.901},
            {"latitude":-1.055,"longitude":-80.905}]
        clat = sum(p["latitude"] for p in poly)/len(poly)
        clon = sum(p["longitude"] for p in poly)/len(poly)
        m = folium.Map(location=[clat,clon],zoom_start=13,tiles="CartoDB positron")
        folium.Polygon([[p["latitude"],p["longitude"]] for p in poly],
                       color="#0284c7",weight=3,fill=True,fill_color="#38bdf8",fill_opacity=0.15).add_to(m)
        for a in animals_list:
            clr = "green" if a["current_status"]=="Saludable" else "orange" if a["current_status"]=="Bajo Observacion" else "red"
            folium.CircleMarker([a.get("latitude",-1.058),a.get("longitude",-80.897)],
                                radius=9,color=clr,fill=True,fill_color=clr,fill_opacity=0.85,
                                popup=folium.Popup(f"<b>{a['id']} – {a['name']}</b><br>{a['current_status']}",max_width=180)).add_to(m)
        st_folium(m,width="100%",height=290,key="dash_map")
        st.markdown("</div>",unsafe_allow_html=True)

    with cd:
        st.markdown('<div style="background:#fff;border-radius:20px;padding:20px;border:1px solid #e0ecf7;'
                    'box-shadow:0 4px 20px rgba(7,37,58,0.04);">',unsafe_allow_html=True)
        sanos=len([a for a in animals_list if a["current_status"]=="Saludable"])
        riesgo=len([a for a in animals_list if a["current_status"]=="Bajo Observacion"])
        infect=len([a for a in animals_list if a["current_status"]=="En Tratamiento"])
        tot=max(1,len(animals_list))
        st.markdown('<div style="font-family:\'Outfit\',sans-serif;font-size:1rem;font-weight:800;color:#07253a;margin-bottom:4px;">Estado del rebano</div>',
                    unsafe_allow_html=True)
        fig=go.Figure(go.Pie(labels=["Sanos","Riesgo","Tratamiento"],values=[sanos,riesgo,infect],
                             hole=0.72,marker_colors=["#15803d","#eab308","#dc2626"],textinfo="none"))
        fig.add_annotation(text=f"<b>{sanos}/{tot}</b>",x=0.5,y=0.5,
                           font=dict(size=18,color="#07253a",family="Outfit"),showarrow=False)
        fig.update_layout(showlegend=False,margin=dict(t=10,b=0,l=0,r=0),height=190,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
        for lbl,val_n,color,icon in [("Sanos",sanos,"#15803d","🟢"),("En riesgo",riesgo,"#eab308","🟡"),("Tratamiento",infect,"#dc2626","🔴")]:
            pct=round(val_n/tot*100)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 margin-bottom:9px;padding:8px 12px;background:#f8fafc;border-radius:10px;border:1px solid #e0ecf7;">
              <div style="display:flex;align-items:center;gap:8px;">{icon}
                <span style="font-size:0.84rem;color:#64748b;font-weight:600;">{lbl}</span>
              </div>
              <div><span style="font-weight:800;color:#0f2942;font-size:0.9rem;">{val_n}</span>
                <span style="font-size:0.74rem;color:#94a3b8;margin-left:4px;">({pct}%)</span>
              </div>
            </div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)


# ── MIS BOVINOS ───────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Mis Bovinos":
    st.markdown('<h2 style="font-family:\'Outfit\',sans-serif;font-size:1.6rem;font-weight:800;color:#07253a;margin:0 0 4px;">🐄 Inventario de Bovinos</h2><p style="color:#64748b;font-size:0.9rem;margin:0 0 18px;">Hoja de vida ganadera, raza, produccion y estado sanitario.</p>',unsafe_allow_html=True)
    cols=st.columns(3)
    for i,a in enumerate(animals_list):
        sc=a["current_status"]
        color="#15803d" if sc=="Saludable" else "#eab308" if sc=="Bajo Observacion" else "#dc2626"
        with cols[i%3]:
            st.markdown(f"""
            <div style="background:#fff;border-radius:20px;padding:22px;border:1px solid #e0ecf7;
                 box-shadow:0 4px 20px rgba(7,37,58,0.04);margin-bottom:16px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                {pill(a['id'],'blue')}
                <span style="background:{color}18;color:{color};border:1px solid {color}44;
                     padding:3px 10px;border-radius:9999px;font-size:0.76rem;font-weight:700;">{sc}</span>
              </div>
              <div style="font-family:'Outfit',sans-serif;font-size:1.15rem;font-weight:800;color:#07253a;margin-bottom:3px;">{a['name']}</div>
              <div style="font-size:0.82rem;color:#94a3b8;margin-bottom:12px;">{a['breed']} · {a['purpose']}</div>
              <hr style="border:none;border-top:1px solid #f1f5f9;margin:10px 0;">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="background:#f8fafc;border-radius:10px;padding:8px 10px;">
                  <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;">HACIENDA</div>
                  <div style="font-size:0.83rem;color:#0f2942;font-weight:700;margin-top:2px;">📍 {a['hacienda']}</div>
                </div>
                <div style="background:#f8fafc;border-radius:10px;padding:8px 10px;">
                  <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;">PRODUCCION</div>
                  <div style="font-size:0.83rem;color:#0284c7;font-weight:700;margin-top:2px;">🥛 {a['avg_milk_daily_liters']} L/dia</div>
                </div>
                <div style="background:#f8fafc;border-radius:10px;padding:8px 10px;">
                  <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;">PESO</div>
                  <div style="font-size:0.83rem;color:#0f2942;font-weight:700;margin-top:2px;">⚖️ {a['weight_kg']} kg</div>
                </div>
                <div style="background:#f8fafc;border-radius:10px;padding:8px 10px;">
                  <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;">NACIMIENTO</div>
                  <div style="font-size:0.83rem;color:#0f2942;font-weight:700;margin-top:2px;">📅 {a['birth_date']}</div>
                </div>
              </div>
            </div>""",unsafe_allow_html=True)


# ── ESCANEAR BOVINO ───────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Escanear Bovino":
    st.markdown('<div style="background:#fff;border-radius:20px;padding:24px;border:1px solid #e0ecf7;box-shadow:0 4px 20px rgba(7,37,58,0.04);margin-bottom:18px;"><h3 style="font-family:\'Outfit\',sans-serif;font-weight:800;color:#07253a;margin:0 0 6px;">📷 Ingesta de Campo – Evaluacion Multiagente</h3><p style="color:#64748b;font-size:0.9rem;margin:0;">Selecciona el bovino, describe los sintomas y la red de IA evaluara el caso en tiempo real.</p></div>',unsafe_allow_html=True)
    ci,cn=st.columns([1,2],gap="large")
    with ci:
        st.markdown("##### 1. Identificar Bovino")
        opts=[f"{a['id']} – {a['name']} ({a['breed']})" for a in animals_list]
        sel_str=st.selectbox("Arete / QR",opts,key="scan_sel")
        sel_id=sel_str.split(" – ")[0]
        prof=db.get_animal_by_id_or_qr(sel_id)
        if prof:
            sc=prof["current_status"]
            color="#15803d" if sc=="Saludable" else "#eab308" if sc=="Bajo Observacion" else "#dc2626"
            st.markdown(f'<div style="background:#f0f9ff;padding:16px;border-radius:16px;border:1px solid #bae6fd;font-size:0.88rem;color:#0f2942;"><b>Nombre:</b> {prof["name"]}<br><b>Raza:</b> {prof["breed"]} ({prof["purpose"]})<br><b>Hacienda:</b> {prof["hacienda"]}<br><b>Leche prom.:</b> {prof["avg_milk_daily_liters"]} L/dia<br><b>Estado:</b> <span style="background:{color}18;color:{color};border:1px solid {color}44;padding:2px 8px;border-radius:9999px;font-weight:700;">{sc}</span></div>',unsafe_allow_html=True)
    with cn:
        st.markdown("##### 2. Novedad de Campo")
        narrative=st.text_area("Describe los sintomas:",value="La vaca tiene la ubre muy caliente e hinchada y produjo 4.5 litros menos de leche.",height=120,key="scan_narrative")
        fc1,fc2=st.columns([2,1])
        with fc1:
            img_file=st.file_uploader("📷 Foto (opcional)",type=["jpg","png","jpeg"])
        with fc2:
            if img_file:
                st.image(img_file,width=120)
        img_desc=f"Fotografia: inspeccion bovino ({img_file.name})" if img_file else None
        st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)
        if st.button("✨ Procesar con Red Multiagente",type="primary",use_container_width=True,key="btn_scan"):
            with st.spinner("Evaluando con red multiagente IA..."):
                result=orchestrator.process_field_report(qr_or_id=sel_id,user_narrative=narrative,username=username,image_description=img_desc)
                st.session_state["latest_evaluation"]=result
            if result["success"]:
                st.toast("Evaluacion completada",icon="✅")
                if result["requires_hitl_approval"]:
                    st.warning(f"Alerta sanitaria — Ticket #{result['hitl_ticket_id']} requiere firma en Capacitacion HITL")
                san=result["agent_outputs"]["sanitary"]
                prod=result["agent_outputs"]["productive"]
                r1,r2,r3=st.columns(3)
                for col,bg,br,title,body in [
                    (r1,"#f0fdf4","#86efac","🩺 Pre-diagnostico",f"<b>{san['pre_diagnosis']}</b><br><small>Confianza: {san['confidence_percent']}% · Severidad: {san['severity']}</small>"),
                    (r2,"#fef9ec","#fde047","📈 Produccion",f"Caida: <b>{prod['drop_percentage']}%</b><br><small>Perdida: ${prod['estimated_daily_financial_loss_usd']}/dia</small>"),
                    (r3,"#f0f9ff","#7dd3fc","💊 Tratamiento",f"<small>{san['recommended_treatment_plan']}</small>"),
                ]:
                    with col:
                        st.markdown(f'<div style="background:{bg};border-radius:14px;padding:14px;border:1px solid {br};"><b style="color:#0f2942;">{title}</b><br>{body}</div>',unsafe_allow_html=True)
            else:
                st.error(f"Error: {result.get('error','Desconocido')}")


# ── DIAGNOSTICOS ──────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Diagnosticos":
    st.markdown("### 🩺 Diagnosticos Multiagente")
    latest=st.session_state.get("latest_evaluation")
    if not latest:
        st.info("Realiza una ingesta en **Escanear Bovino** para ver el diagnostico detallado.")
    else:
        out=latest["agent_outputs"]
        ident,san,prod,ledg=out["identifier"],out["sanitary"],out["productive"],out["ledger"]
        c1,c2,c3,c4=st.columns(4)
        for col,title,color,items in [
            (c1,"🔍 Identificacion","#0284c7",[("Arete",ident["animal_id"]),("Nombre",ident["animal_name"]),("Hacienda",ident["hacienda"])]),
            (c2,"🩺 Sanitario","#15803d",[("Diagnostico",san["pre_diagnosis"]),("Confianza",f"{san['confidence_percent']}%"),("Severidad",san["severity"])]),
            (c3,"📈 Productivo","#b45309",[("Caida",f"{prod['drop_percentage']}%"),("Perdida",f"${prod['estimated_daily_financial_loss_usd']}/dia")]),
            (c4,"🔒 Ledger","#07253a",[("Ticket",f"#{ledg['ledger_ticket_id']}"),("HITL",ledg["hitl_status"])]),
        ]:
            with col:
                rows="".join(f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#64748b;font-weight:600;">{k}</span><span style="font-size:0.83rem;color:#0f2942;font-weight:700;text-align:right;">{v}</span></div>' for k,v in items)
                st.markdown(f'<div style="background:#fff;border-radius:18px;padding:18px;border:1px solid #e0ecf7;box-shadow:0 4px 14px rgba(7,37,58,0.03);"><h4 style="color:{color};margin:0 0 12px;font-size:0.95rem;font-family:\'Outfit\',sans-serif;">{title}</h4>{rows}</div>',unsafe_allow_html=True)
        with st.expander("Ver resumen completo del flujo multiagente"):
            st.markdown(latest.get("workflow_summary",""))
            st.caption(san.get("disclaimer",""))


# ── ENCICLOPEDIA ──────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Enciclopedia":
    st.markdown("### 📖 Enciclopedia Clinica Bovina")
    for e in [
        {"n":"Mastitis Bovina","r":"ALTA","c":"#b45309","s":"Ubre hinchada y caliente, grumos en leche, caida de produccion.","t":"Prueba CMT, infusion intramamaria, aislamiento 48h."},
        {"n":"Anaplasmosis / Babesiosis","r":"CRITICA","c":"#b91c1c","s":"Fiebre alta, anemia, mucosas palidas o amarillentas.","t":"Hemograma urgente, imidocarb / oxitetraciclina."},
        {"n":"Sospecha de Fiebre Aftosa","r":"EMERGENCIA","c":"#7c3aed","s":"Aftas en boca y pezunas, salivacion excesiva, cojera.","t":"Aislamiento inmediato y reporte a AGROCALIDAD Ecuador."},
        {"n":"Neumonia Bovina","r":"MEDIA-ALTA","c":"#0369a1","s":"Tos, secrecion nasal, dificultad respiratoria.","t":"Antibioticoterapia sistemica y refugio seco y ventilado."},
        {"n":"Parasitosis Gastrointestinal","r":"MODERADA","c":"#047857","s":"Perdida de peso, pelaje opaco, diarrea, edema submandibular.","t":"Coproparasitologico, Ivermectina o Albendazol."},
    ]:
        ic = "🔴" if e['r'] in ['CRITICA','EMERGENCIA'] else "🟡" if e['r']=="ALTA" else "🟢"
        with st.expander(f"{ic} {e['n']} — Riesgo: {e['r']}"):
            c1e,c2e=st.columns(2)
            with c1e: st.markdown(f"**Sintomas:**\n{e['s']}")
            with c2e: st.markdown(f"**Tratamiento:**\n{e['t']}")


# ── MAPA DE FINCAS ────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Mapa de Fincas":
    st.markdown("### 🗺️ Delimitacion de Recintos y Geofencing GPS")
    poly=db.get_farm_perimeter(st.session_state.selected_hacienda) or [
        {"latitude":-1.055,"longitude":-80.905},{"latitude":-1.052,"longitude":-80.892},
        {"latitude":-1.062,"longitude":-80.888},{"latitude":-1.065,"longitude":-80.901},
        {"latitude":-1.055,"longitude":-80.905}]
    clat=sum(p["latitude"] for p in poly)/len(poly)
    clon=sum(p["longitude"] for p in poly)/len(poly)
    m2=folium.Map(location=[clat,clon],zoom_start=14,tiles="OpenStreetMap")
    folium.Polygon([[p["latitude"],p["longitude"]] for p in poly],color="#0284c7",weight=3,fill=True,fill_color="#0284c7",fill_opacity=0.2).add_to(m2)
    for a in animals_list:
        clr="green" if a["current_status"]=="Saludable" else "orange" if a["current_status"]=="Bajo Observacion" else "red"
        folium.Marker([a.get("latitude",-1.058),a.get("longitude",-80.897)],
                      popup=folium.Popup(f"<b>{a['id']}: {a['name']}</b><br>{a['current_status']}",max_width=200),
                      icon=folium.Icon(color=clr,icon="info-sign")).add_to(m2)
    Draw(export=True).add_to(m2)
    st_folium(m2,width="100%",height=500,key="full_map")


# ── CLIMA Y SUELO ─────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Clima y Suelo":
    st.markdown("### 🌤️ Monitoreo Agroclimatico — Manta, Manabi")
    c1,c2,c3=st.columns(3)
    for col,title,val,badge,bc,desc in [
        (c1,"🌡️ Temperatura","28.5 °C","Estable","#0369a1","Condicion favorable para el ganado"),
        (c2,"💧 Humedad Relativa","72 %","Zona costera","#b45309","Monitorear ventilacion en establos"),
        (c3,"📊 Indice ITH","74.2","Estres leve","#15803d","Considera sombra adicional a mediodia"),
    ]:
        with col:
            st.markdown(f'<div style="background:#fff;border-radius:18px;padding:22px;border:1px solid #e0ecf7;box-shadow:0 4px 14px rgba(7,37,58,0.03);"><div style="font-size:0.88rem;font-weight:700;color:#64748b;margin-bottom:10px;">{title}</div><div style="font-family:\'Outfit\',sans-serif;font-size:2rem;font-weight:800;color:#0f2942;">{val}</div><div style="margin-top:10px;"><span style="background:{bc}18;color:{bc};border:1px solid {bc}44;padding:3px 10px;border-radius:9999px;font-size:0.76rem;font-weight:700;">{badge}</span></div><div style="font-size:0.78rem;color:#94a3b8;margin-top:10px;">{desc}</div></div>',unsafe_allow_html=True)


# ── ASISTENTE IA ──────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Asistente IA":
    st.markdown('<div style="background:#fff;border-radius:20px;padding:20px 24px;border:1px solid #e0ecf7;box-shadow:0 4px 20px rgba(7,37,58,0.04);margin-bottom:16px;"><h3 style="font-family:\'Outfit\',sans-serif;font-weight:800;color:#07253a;margin:0 0 4px;">🤖 Asistente BovinoAI</h3><p style="color:#64748b;font-size:0.88rem;margin:0;">Diagnostico IA. Menciona el ID del bovino y los sintomas para analisis inmediato.</p></div>',unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    user_q=st.chat_input("Ej.: 'La vaca BOV-104 tiene fiebre y la ubre caliente. Que puede ser?'")
    if user_q:
        st.session_state.chat_history.append({"role":"user","content":user_q})
        with st.chat_message("user"): st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Analizando con IA multiagente..."):
                q_lower=user_q.lower()
                ma=next((a for a in animals_list if a["id"].lower() in q_lower or a["name"].lower() in q_lower),None)
                if ma:
                    result=orchestrator.process_field_report(qr_or_id=ma["id"],user_narrative=user_q,username=username)
                    if result["success"]:
                        san=result["agent_outputs"]["sanitary"]
                        prod=result["agent_outputs"]["productive"]
                        answer=(f"📋 **Analisis para {ma['name']} ({ma['id']})**\n\n"
                                f"**Pre-diagnostico:** {san['pre_diagnosis']}\n"
                                f"**Confianza:** {san['confidence_percent']}% · **Severidad:** {san['severity']}\n\n"
                                f"**Tratamiento:**\n{san['recommended_treatment_plan']}\n\n"
                                f"**Impacto productivo:** Caida del {prod['drop_percentage']}% · ${prod['estimated_daily_financial_loss_usd']}/dia\n\n"
                                f"*{san['disclaimer']}*")
                        if result["requires_hitl_approval"]:
                            answer+=f"\n\n🚨 **Ticket HITL #{result['hitl_ticket_id']} generado** — requiere firma del veterinario."
                    else:
                        answer=f"No pude procesar: {result.get('error')}"
                elif any(w in q_lower for w in ["cuantos","rebano","ganado","inventario","lista","bovinos"]):
                    sanos_n=len([a for a in animals_list if a["current_status"]=="Saludable"])
                    tot=max(1,len(animals_list))
                    answer=(f"📊 **Estado del rebano — {st.session_state.selected_hacienda}:**\n\n"
                            f"- **Total:** {tot} bovinos\n- **Sanos:** {sanos_n} ({round(sanos_n/tot*100)}%)\n- **Con atencion:** {tot-sanos_n}\n\n")
                    for a in animals_list:
                        ic="🟢" if a["current_status"]=="Saludable" else "🟡" if a["current_status"]=="Bajo Observacion" else "🔴"
                        answer+=f"{ic} **{a['id']}** – {a['name']} | {a['breed']} | {a['avg_milk_daily_liters']} L/dia\n"
                else:
                    from tools.vet_rules import evaluate_clinical_symptoms
                    diag=evaluate_clinical_symptoms(user_q)
                    if diag["pre_diagnosis"]!="Indeterminado / Evaluacion General Requerida":
                        answer=(f"🔍 **Analisis de sintomas:**\n\n**Posible condicion:** {diag['pre_diagnosis']}\n"
                                f"**Confianza:** {diag['confidence_percent']}% · **Severidad:** {diag['severity']}\n\n"
                                f"**Recomendacion:** {diag['recommended_action']}\n\n💡 Para analisis completo ve a **Escanear Bovino**.")
                    elif any(w in q_lower for w in ["hola","ayuda","como","puedes"]):
                        answer=("👋 Hola! Soy **BovinoAI**.\n\n**Puedo ayudarte con:**\n"
                                "- 🩺 Diagnostico — menciona el ID del bovino y sintomas\n"
                                "- 📊 Estado del rebano — pregunta 'cuantos bovinos tengo'\n"
                                "- 💊 Info de enfermedades — mastitis, aftosa, etc.")
                    else:
                        fid=animals_list[0]["id"] if animals_list else "BOV-104"
                        answer=(f"No identifique sintomas especificos. Intenta con:\n"
                                f'- *"La vaca {fid} tiene fiebre y no come"*\n'
                                f"- *Cuantos bovinos tengo activos?*")
            st.markdown(answer)
            st.session_state.chat_history.append({"role":"assistant","content":answer})


# ── REPORTES ──────────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Reportes":
    st.markdown("### 📈 Reportes de Produccion")
    rows=[]
    for a in animals_list:
        for ml in a.get("recent_milk_logs",[]):
            rows.append({"Bovino":f"{a['id']} ({a['name']})","Fecha":ml["date"],"Litros":ml["liters"]})
    if rows:
        df=pd.DataFrame(rows)
        fig=px.line(df,x="Fecha",y="Litros",color="Bovino",markers=True,
                    color_discrete_sequence=["#0284c7","#15803d","#b45309"],
                    title="Produccion de Leche (L/dia) por Bovino")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_family="Plus Jakarta Sans")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#f1f5f9")
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("Sin datos de ordeno registrados todavia.")


# ── MERCADOS Y LEDGER ─────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Mercados y Ledger":
    st.markdown("### 🔗 Cadena de Auditoria SHA-256")
    recs=db.get_ledger_records()
    if recs:
        df=pd.DataFrame(recs)
        cols_show=[c for c in ["id","timestamp","animal_id","agent_source","hitl_status","hitl_reviewer","hash_sha256"] if c in df.columns]
        st.dataframe(df[cols_show],use_container_width=True)
    else:
        st.info("Sin registros en el ledger todavia.")


# ── CAPACITACION HITL ─────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Capacitacion HITL":
    st.markdown("### 👨‍⚕️ Supervision Medica — Human-In-The-Loop")
    st.caption("Solo el veterinario puede aprobar o rechazar tratamientos. Ningun farmaco se aplica de forma autonoma.")
    pending=[r for r in db.get_ledger_records() if r.get("hitl_status")=="PENDIENTE"]
    if not pending:
        st.success("Todos los tickets han sido revisados. Sin acciones pendientes.")
    else:
        st.warning(f"🚨 {len(pending)} ticket(s) requieren firma veterinaria.")
        for t in pending:
            tid=t["id"]
            payload=t.get("payload",{})
            san=payload.get("sanitary",{})
            prod=payload.get("productive",{})
            with st.expander(f"Ticket #{tid} — Bovino {t.get('animal_id')} · {t.get('timestamp','')[:10]}"):
                c1t,c2t=st.columns(2)
                with c1t:
                    st.markdown(f"**Pre-diagnostico:** {san.get('pre_diagnosis','—')}")
                    st.markdown(f"**Severidad:** {san.get('severity','—')}")
                with c2t:
                    st.markdown(f"**Caida productiva:** {prod.get('drop_percentage','—')}%")
                    st.markdown(f"**Perdida/dia:** ${prod.get('estimated_daily_financial_loss_usd','—')}")
                st.markdown(f"**Tratamiento propuesto:** {san.get('recommended_treatment_plan','—')}")
                prescripcion=st.text_area("Prescripcion medica:",key=f"presc_{tid}",value="Tratamiento validado. Aplicar conforme a protocolo clinico.")
                hc1,hc2,hc3=st.columns(3)
                with hc1:
                    if st.button(f"Aprobar #{tid}",key=f"ap_{tid}",type="primary"):
                        orchestrator.resolve_hitl_ticket(tid,"APROBADO",f"{username} (Veterinario)",prescripcion)
                        st.toast(f"Ticket #{tid} aprobado",icon="✅"); st.rerun()
                with hc2:
                    if st.button(f"Modificar #{tid}",key=f"mo_{tid}"):
                        orchestrator.resolve_hitl_ticket(tid,"MODIFICADO",f"{username} (Veterinario)",prescripcion)
                        st.toast(f"Ticket #{tid} modificado",icon="✏️"); st.rerun()
                with hc3:
                    if st.button(f"Rechazar #{tid}",key=f"re_{tid}"):
                        orchestrator.resolve_hitl_ticket(tid,"RECHAZADO",f"{username} (Veterinario)",prescripcion)
                        st.toast(f"Ticket #{tid} rechazado",icon="❌"); st.rerun()


# ── CONFIGURACION ─────────────────────────────────────────────────────────────
elif st.session_state.active_menu == "Configuracion":
    st.markdown("### ⚙️ Administracion del Sistema")
    if current_role != "Administrador":
        st.warning("Acceso restringido a Administradores.")
    else:
        tab1,tab2,tab3=st.tabs(["👥 Usuarios","🐄 Bovinos","🔒 Clerk API"])
        with tab1:
            users=db.get_all_users()
            if users:
                st.dataframe(pd.DataFrame(users)[["username","full_name","role","hacienda"]],use_container_width=True)
            with st.expander("Agregar usuario"):
                nu=st.text_input("Usuario",key="cfg_u"); nn=st.text_input("Nombre",key="cfg_n")
                nr=st.selectbox("Rol",["Administrador","Veterinario","Vaquero","Tecnico"],key="cfg_r")
                nh=st.text_input("Hacienda",value="Hacienda El Encanto",key="cfg_h")
                if st.button("Guardar",key="cfg_save"):
                    if nu and nn: db.add_user(nu,nn,nr,nh); st.success(f"Usuario {nu} guardado."); st.rerun()
                    else: st.error("Completa los campos.")
            with st.expander("Eliminar usuario"):
                du=st.text_input("Usuario a eliminar",key="cfg_del")
                if st.button("Eliminar",key="cfg_del_btn"):
                    if du: ok=db.delete_user(du); (st.success(f"Eliminado: {du}") if ok else st.error("No encontrado.")); st.rerun()
        with tab2:
            with st.expander("Agregar bovino"):
                b1,b2=st.columns(2)
                with b1:
                    bid=st.text_input("ID/ARETE",key="b_id"); bqr=st.text_input("QR",key="b_qr")
                    bname=st.text_input("Nombre",key="b_name"); bbreed=st.text_input("Raza",key="b_breed")
                with b2:
                    bpur=st.text_input("Proposito",key="b_pur"); bhac=st.text_input("Hacienda",value="Hacienda El Encanto",key="b_hac")
                    bloc=st.text_input("Ubicacion",key="b_loc"); bbd=st.text_input("Nacimiento",value="2022-01-01",key="b_bd")
                blat=st.number_input("Latitud",value=-1.058,format="%.6f",key="b_lat")
                blon=st.number_input("Longitud",value=-80.897,format="%.6f",key="b_lon")
                bw=st.number_input("Peso (kg)",value=250.0,key="b_w")
                bml=st.number_input("Leche prom. (L/dia)",value=8.0,key="b_ml")
                bst=st.selectbox("Estado",["Saludable","Bajo Observacion","En Tratamiento"],key="b_st")
                if st.button("Agregar bovino",key="b_add"):
                    try:
                        db.add_animal(bid,bqr,bname,bbreed,bpur,bhac,bloc,float(blat),float(blon),bbd,float(bw),float(bml),bst)
                        st.success(f"Bovino {bid} agregado."); st.rerun()
                    except Exception as e: st.error(str(e))
        with tab3:
            st.markdown("### 🔒 Configuracion de Clerk API")
            st.markdown(f"""
**Estado:** {"✅ Clerk configurado y activo (OAuth Google habilitado)" if CLERK_CONFIGURED else "⚠️ Autenticacion local activa (Clerk no configurado)"}

**Para activar Clerk con Google OAuth:**
1. Ve a [dashboard.clerk.com](https://dashboard.clerk.com) y crea una aplicacion
2. En **Social Connections** → activa **Google**
3. Copia tu **Publishable Key** (`pk_live_...` o `pk_test_...`)
4. Agrega en tu `.env`:
```
CLERK_PUBLISHABLE_KEY=pk_live_tu_clave_aqui
```
5. Reinicia la app: `streamlit run ui/app.py`

**Clave actual:** `{CLERK_PUB_KEY[:26] if CLERK_PUB_KEY else "No configurada"}...` {"(real)" if CLERK_CONFIGURED else "(placeholder — reemplazar)"}
            """)
