import os

with open('ui/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire # ── AUTH PAGE block with the new pure HTML/CSS version

import re

# Find the start and end of the block
start_marker = "# ── AUTH PAGE"
end_marker = "# ── Authenticated area"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

new_auth_block = '''# ── AUTH PAGE (PURE HTML/CSS FOR ST.MARKDOWN) ──────────
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
    .stApp { background: radial-gradient(circle at 50% 30%, #e0f2fe 0%, #eaf4f8 65%, #dbeafe 100%) !important; }
    .stMainBlockContainer,.block-container{padding:0!important;max-width:100%!important;}
    [data-testid="stSidebar"]{display:none!important;}
    </style>""", unsafe_allow_html=True)
    
    st.markdown(auth_html, unsafe_allow_html=True)
    st.stop()

'''

new_content = content[:start_idx] + new_auth_block + "\n" + content[end_idx:]

with open('ui/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
