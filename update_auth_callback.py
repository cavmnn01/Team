import os

with open('ui/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Find the start and end of the # ── Clerk OAuth / Local callback ──────────────────────────────────────────────
start_marker = "# ── Clerk OAuth / Local callback"
end_marker = "# ── AUTH PAGE"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

new_callback_block = '''# ── Clerk OAuth / Local callback ──────────────────────────────────────────────
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

'''

new_content = content[:start_idx] + new_callback_block + content[end_idx:]

with open('ui/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
