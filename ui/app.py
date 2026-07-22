import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import json
from datetime import datetime
import folium
from folium.plugins import Draw, MarkerCluster
from streamlit_folium import st_folium

# Añadir directorio raíz al PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.database import (
    init_db, get_all_animals, get_ledger_records, get_animal_by_id_or_qr,
    get_farm_perimeter, update_farm_perimeter, update_animal_gps
)
from agents.orchestrator import BovinoOrchestrator

# Inicializar DB y Orquestador
init_db()
orchestrator = BovinoOrchestrator()

# Configuración de página
st.set_page_config(
    page_title="BovinoAI Manta - GPS Interactivo & Cerco",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILOS CSS MIDNIGHT SLATE DARK MODE
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        color: #f8fafc !important;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 60%, #0b0f19 100%) !important;
    }

    header[data-testid="stHeader"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: rgba(30, 41, 59, 0.7) !important;
        padding: 6px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    button[role="tab"], 
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }

    button[role="tab"] *, 
    .stTabs [data-baseweb="tab"] * {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    button[role="tab"]:hover *, 
    .stTabs [data-baseweb="tab"]:hover * {
        color: #f8fafc !important;
    }

    button[role="tab"][aria-selected="true"], 
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #334155 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    }

    button[role="tab"][aria-selected="true"] *, 
    .stTabs [data-baseweb="tab"][aria-selected="true"] * {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    .midnight-card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 22px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .midnight-agent-card {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
        height: 100%;
    }

    .pill-cyan {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
    }

    .pill-emerald {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
    }

    .pill-amber {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
    }

    .pill-rose {
        background: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
    }

    .pill-purple {
        background: rgba(192, 132, 252, 0.15);
        color: #c084fc;
        border: 1px solid rgba(192, 132, 252, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
    }

    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    div[data-baseweb="select"], 
    div[data-baseweb="select"] *, 
    div[role="combobox"], 
    div[role="button"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
    }

    .stTextArea textarea, .stTextInput input, .stNumberInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 14px !important;
        font-size: 0.95rem !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9999px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado Principal Midnight
col_head1, col_head2 = st.columns([3, 1])

with col_head1:
    st.markdown("<h1 style='color:#f8fafc; font-size: 2.4rem; font-weight: 800; margin-bottom: 2px;'>🐄 BovinoAI Manta</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size: 0.98rem; margin-top: 0;'>Sistema Multiagente de IA para Diagnóstico, Control Sanitario & Trazabilidad | <b>Manta (San Lorenzo, Santa Marianita, San Mateo)</b></p>", unsafe_allow_html=True)

with col_head2:
    st.markdown("""
    <div style='text-align: right; padding-top: 8px;'>
        <span class='pill-emerald'>🌿 ODS 8: Trabajo Decente</span>
        <span class='pill-cyan' style='margin-left: 6px;'>⚡ ODS 9: Innovación</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 🌿 BovinoAI Manta")
st.sidebar.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin-top:-10px;'>Gestión Ganadera Inteligente</p>", unsafe_allow_html=True)

user_role = st.sidebar.selectbox(
    "👤 Usuario Activo (RBAC):",
    ["vaquero_sanlorenzo (Juan Carlos Delgado - Vaquero)",
     "vet_manabi (Dr. Roberto Intriago - Veterinario)",
     "admin_manta (Ing. Carmen Pinchao - Administrador)"]
)
username = user_role.split(" ")[0]

st.sidebar.divider()
animals_list = get_all_animals()
st.sidebar.markdown(f"**Bovinos Registrados:** <span class='pill-cyan'>{len(animals_list)} cabezas</span>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("**Haciendas Cobertura:** <span class='pill-cyan'>San Lorenzo, Santa Marianita, San Mateo</span>", unsafe_allow_html=True)

ledger_records = get_ledger_records()
pending_tickets = [r for r in ledger_records if r.get("hitl_status") == "PENDIENTE"]
if pending_tickets:
    st.sidebar.markdown(f"<div class='pill-amber' style='margin-top: 14px; width: 100%; text-align: center;'>⚠️ {len(pending_tickets)} Ticket(s) HITL Pendientes</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("🟢 **Estado Base de Datos:** <span class='pill-emerald'>SQLite Activa</span>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("🔒 **Seguridad Ledger:** <span class='pill-cyan'>SHA-256 Validado</span>", unsafe_allow_html=True)

# Pestañas Principales
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📱 Ingesta de Campo",
    "🤖 Agentes IA",
    "🩺 Supervisión (HITL)",
    "🗺️ Mapa GPS & Cerco Interactivo",
    "🔒 Bitácora Ledger",
    "📊 Rendimiento",
    "🌐 Impacto ODS"
])

# ---------------------------------------------------------
# TAB 1: INGESTA DE CAMPO
# ---------------------------------------------------------
with tab1:
    st.markdown("""
    <div class='midnight-card'>
        <h3 style='margin-top:0; color:#f8fafc; font-weight:800;'>📋 Registro Rápido de Novedades de Campo</h3>
        <p style='color:#cbd5e1; font-size:0.92rem; margin-bottom:0;'>
            El vaquero o técnico selecciona el Arete/QR e ingresa la novedad en lenguaje natural (dictado o escrito). La IA analizará los síntomas y caídas de leche.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_inp1, col_inp2 = st.columns([1, 2], gap="large")

    with col_inp1:
        st.markdown("##### 1. Identificación del Bovino")
        animal_options = [f"{a['id']} - {a['name']} ({a['breed']} / {a['hacienda']})" for a in animals_list]
        selected_animal_str = st.selectbox("Seleccionar Código Arete / QR:", animal_options)
        selected_animal_id = selected_animal_str.split(" - ")[0]

        profile_pre = get_animal_by_id_or_qr(selected_animal_id)
        if profile_pre:
            st.markdown(f"""
            <div style='background-color:#1e293b; padding: 20px; border-radius: 16px; border: 1px solid #475569; color:#f8fafc;'>
                <p style='margin: 4px 0; font-size:0.92rem;'><b>Nombre:</b> {profile_pre['name']}</p>
                <p style='margin: 4px 0; font-size:0.92rem;'><b>Raza / Propósito:</b> {profile_pre['breed']} ({profile_pre['purpose']})</p>
                <p style='margin: 4px 0; font-size:0.92rem;'><b>Ubicación:</b> {profile_pre['hacienda']} ({profile_pre['location']})</p>
                <p style='margin: 4px 0; font-size:0.92rem;'><b>Promedio Leche:</b> {profile_pre['avg_milk_daily_liters']} L/día</p>
                <p style='margin: 8px 0 0 0;'><b>Estado:</b> <span class='pill-emerald'>{profile_pre['current_status']}</span></p>
            </div>
            """, unsafe_allow_html=True)

    with col_inp2:
        st.markdown("##### 2. Novedad Registrada por Voz / Texto")
        field_narrative = st.text_area(
            "Dictado del vaquero en lenguaje natural:",
            value="La vaca 104 comió muy poco el día de hoy, tiene la ubre muy caliente e hinchada y produjo 4.5 litros menos de leche.",
            height=110
        )

        col_cam1, col_cam2 = st.columns([2, 1])
        with col_cam1:
            image_file = st.file_uploader("📷 Adjuntar foto de síntoma / inspección (Opcional):", type=["jpg", "png", "jpeg"])
            img_desc = None
            if image_file:
                img_desc = f"Fotografía adjunta: Inspección visual de tejido bovino ({image_file.name})"
        with col_cam2:
            if image_file:
                st.image(image_file, caption="Foto adjunta", width=140)

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        submit_btn = st.button("✨ Procesar Con Red Multiagente", type="primary", use_container_width=True)

    if submit_btn:
        with st.spinner("🤖 Evaluando novedad con red multiagente..."):
            result = orchestrator.process_field_report(
                qr_or_id=selected_animal_id,
                user_narrative=field_narrative,
                username=username,
                image_description=img_desc
            )
            st.session_state['latest_evaluation'] = result

        if result["success"]:
            st.toast("✅ Novedad procesada exitosamente", icon="🎉")
            if result["requires_hitl_approval"]:
                st.markdown(f"<div class='pill-rose' style='font-size:0.92rem; padding: 10px 18px; width: 100%; text-align: center; margin-top: 14px;'>🚨 Alerta Sanitaria Generada: Requiere aprobación del veterinario en 'Supervisión (HITL)' (Ticket #{result['hitl_ticket_id']})</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: AGENTES IA
# ---------------------------------------------------------
with tab2:
    st.markdown("### 🤖 Arquitectura Multiagente OpenAI SDK")
    st.markdown("<p style='color:#94a3b8; font-size:0.92rem;'>Visualización en tiempo real de la ejecución y salidas de cada agente especialista.</p>", unsafe_allow_html=True)

    latest_eval = st.session_state.get('latest_evaluation')

    if not latest_eval:
        st.info("💡 Ingrese una novedad en 'Ingesta de Campo' para visualizar los datos generados por cada agente.")
    else:
        outputs = latest_eval["agent_outputs"]

        col_a1, col_a2, col_a3, col_a4 = st.columns(4, gap="medium")

        with col_a1:
            ident = outputs["identifier"]
            st.markdown(f"""
            <div class='midnight-agent-card'>
                <h4 style='color:#38bdf8; margin-top:0; font-size:1.05rem; font-weight:800;'>🔍 IdentifierAgent</h4>
                <p style='color:#94a3b8; font-size:0.8rem; font-weight:700; margin-bottom:12px;'>Function Calling DB</p>
                <hr style='border-color:rgba(255,255,255,0.08); margin:10px 0;'>
                <p style='margin:6px 0; font-size:0.88rem;'><b>ID Bovino:</b> <span class='pill-cyan'>{ident['animal_id']}</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Nombre:</b> {ident['animal_name']}</p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Hacienda:</b> {ident['hacienda']}</p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Rol Usuario:</b> <span class='pill-cyan'>{ident['user']['role']}</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col_a2:
            san = outputs["sanitary"]
            st.markdown(f"""
            <div class='midnight-agent-card'>
                <h4 style='color:#c084fc; margin-top:0; font-size:1.05rem; font-weight:800;'>🩺 SanitaryAgent</h4>
                <p style='color:#94a3b8; font-size:0.8rem; font-weight:700; margin-bottom:12px;'>Diagnóstico Clínico</p>
                <hr style='border-color:rgba(255,255,255,0.08); margin:10px 0;'>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Pre-diagnóstico:</b> {san['pre_diagnosis']}</p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Confianza:</b> <span class='pill-purple'>{san['confidence_percent']}%</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Severidad:</b> <span class='pill-rose'>{san['severity']}</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col_a3:
            prod = outputs["productive"]
            st.markdown(f"""
            <div class='midnight-agent-card'>
                <h4 style='color:#34d399; margin-top:0; font-size:1.05rem; font-weight:800;'>📊 ProductiveAgent</h4>
                <p style='color:#94a3b8; font-size:0.8rem; font-weight:700; margin-bottom:12px;'>Structured Output</p>
                <hr style='border-color:rgba(255,255,255,0.08); margin:10px 0;'>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Valor Actual:</b> <span class='pill-cyan'>{prod['current_value']} L</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Caída:</b> <span class='pill-rose'>{prod['drop_percentage']}%</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Pérdida/día:</b> <b>${prod['estimated_daily_financial_loss_usd']}</b></p>
            </div>
            """, unsafe_allow_html=True)

        with col_a4:
            ledg = outputs["ledger"]
            st.markdown(f"""
            <div class='midnight-agent-card'>
                <h4 style='color:#f8fafc; margin-top:0; font-size:1.05rem; font-weight:800;'>🔒 LedgerAgent</h4>
                <p style='color:#94a3b8; font-size:0.8rem; font-weight:700; margin-bottom:12px;'>Firma SHA-256</p>
                <hr style='border-color:rgba(255,255,255,0.08); margin:10px 0;'>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Ticket HITL:</b> <span class='pill-amber'>#{ledg['ledger_ticket_id']}</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Estado:</b> <span class='pill-amber'>{ledg['hitl_status']}</span></p>
                <p style='margin:6px 0; font-size:0.88rem;'><b>Hash:</b> <span class='pill-cyan'>{ledg['hash_sha256'][:12]}...</span></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        with st.expander("📄 Ver estructura técnica en formato JSON (Opcional)"):
            st.json(outputs)

# ---------------------------------------------------------
# TAB 3: SUPERVISIÓN HUMANA (HITL)
# ---------------------------------------------------------
with tab3:
    st.markdown("### 🩺 Supervisión Médica Humana (*Human-In-The-Loop*)")
    st.caption("Control Sanitario: Ningún tratamiento médico se aplica sin la firma explícita del profesional veterinario.")

    all_ledger = get_ledger_records()
    pending_records = [r for r in all_ledger if r.get("hitl_status") == "PENDIENTE"]

    if not pending_records:
        st.markdown("""
        <div class='midnight-card' style='text-align: center; padding: 36px;'>
            <h4 style='color: #34d399; margin: 0;'>✨ No hay tickets pendientes</h4>
            <p style='color: #94a3b8; margin-top: 6px;'>Todas las evaluaciones sanitarias han sido supervisadas.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='pill-amber' style='font-size: 0.9rem; padding: 8px 18px; margin-bottom: 16px;'>🚨 {len(pending_records)} Ticket(s) Pendientes de Firma Médica</div>", unsafe_allow_html=True)

        for ticket in pending_records:
            ticket_id = ticket["id"]
            animal_id = ticket["animal_id"]
            payload = ticket.get("payload", {})
            sanitary = payload.get("sanitary", {})
            productive = payload.get("productive", {})

            with st.container():
                st.markdown(f"""
                <div class='midnight-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin:0; color: #f8fafc;'>📋 Ticket HITL #{ticket_id} — Bovino {animal_id}</h4>
                        <span class='pill-amber'>Pendiente Revisión</span>
                    </div>
                    <hr style='border-color: rgba(255,255,255,0.08); margin: 16px 0;'>
                </div>
                """, unsafe_allow_html=True)

                col_t1, col_t2 = st.columns(2)

                with col_t1:
                    st.markdown(f"**Pre-diagnóstico IA:** {sanitary.get('pre_diagnosis')}")
                    st.markdown(f"**Nivel de Confianza:** <span class='pill-cyan'>{sanitary.get('confidence_percent')}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**Síntomas:** *\"{sanitary.get('symptoms_reported')}\"*")
                    st.markdown(f"**Tratamiento Sugerido:** {sanitary.get('recommended_treatment_plan')}")

                with col_t2:
                    st.markdown(f"**Caída Productiva:** <span class='pill-rose'>{productive.get('drop_percentage')}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**Pérdida Diaria Est.:** `${productive.get('estimated_daily_financial_loss_usd')}/día`")
                    vac = sanitary.get("vaccination_status", {})
                    if vac.get("has_expired_vaccines"):
                        st.markdown("<span class='pill-rose'>Vacuna Aftosa Vencida</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='pill-emerald'>Vacunas al día</span>", unsafe_allow_html=True)

                comment_input = st.text_input(f"Prescripción / Observación Médica (Ticket #{ticket_id}):", value="Tratamiento validado. Aplicar infusión intramamaria y aislamiento por 48 horas.", key=f"comm_{ticket_id}")

                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    if st.button("✅ [APROBAR TRATAMIENTO]", key=f"app_{ticket_id}", type="primary", use_container_width=True):
                        orchestrator.resolve_hitl_ticket(
                            ticket_id=ticket_id,
                            decision="APROBADO",
                            reviewer_name=f"{username} (Veterinario)",
                            comment=comment_input
                        )
                        st.toast(f"Ticket #{ticket_id} APROBADO", icon="✅")
                        st.rerun()

                with col_b2:
                    if st.button("✏️ [MODIFICAR DIAGNÓSTICO]", key=f"mod_{ticket_id}", use_container_width=True):
                        orchestrator.resolve_hitl_ticket(
                            ticket_id=ticket_id,
                            decision="MODIFICADO",
                            reviewer_name=f"{username} (Veterinario)",
                            comment=comment_input
                        )
                        st.toast(f"Ticket #{ticket_id} MODIFICADO", icon="✏️")
                        st.rerun()

                with col_b3:
                    if st.button("❌ [RECHAZAR ALERTA]", key=f"rej_{ticket_id}", use_container_width=True):
                        orchestrator.resolve_hitl_ticket(
                            ticket_id=ticket_id,
                            decision="RECHAZADO",
                            reviewer_name=f"{username} (Veterinario)",
                            comment=comment_input
                        )
                        st.toast(f"Ticket #{ticket_id} RECHAZADO", icon="❌")
                        st.rerun()

# ---------------------------------------------------------
# TAB 4: MAPA GPS INTERACTIVO (DIBUJO Y CLIC DIRECTO)
# ---------------------------------------------------------
with tab4:
    st.markdown("### 🗺️ Mapa GPS Interactivo — Delimitación del Cerco & Bovinos")
    st.markdown("""
    <div class='midnight-card'>
        <h4 style='margin-top:0; color:#f8fafc; font-weight:800;'>📍 Dibuje o Clickee en el Mapa para Delimitar su Recinto en Ecuador</h4>
        <p style='color:#cbd5e1; font-size:0.92rem; margin-bottom:0;'>
            • <b>Dibujo en Mapa:</b> Utilice las herramientas de dibujo en la esquina superior izquierda del mapa (Polígono / Marcadores).<br>
            • <b>Clic Directo:</b> Haga clic en cualquier punto del mapa para capturar las coordenadas GPS e incorporarlas al perímetro del recinto.<br>
            • <b>Bovinos en Vivo:</b> Los marcadores muestran a cada animal con su estado de salud y producción.
        </p>
    </div>
    """, unsafe_allow_html=True)

    haciendas = ["Hacienda El Encanto", "Rancho San Mateo", "Finca Santa Marianita"]
    col_map_h, col_map_s = st.columns([2, 1])

    with col_map_h:
        sel_hacienda = st.selectbox("Seleccionar Recinto / Hacienda:", haciendas, key="sel_hac_map")

    with col_map_s:
        tile_style = st.selectbox("Estilo de Mapa Visual:", ["CartoDB dark_matter", "OpenStreetMap", "Esri WorldImagery (Satélite)"])

    # Cargar coordenadas del cerco
    polygon_pts = get_farm_perimeter(sel_hacienda)
    if not polygon_pts:
        polygon_pts = [
            {"latitude": -1.055, "longitude": -80.905},
            {"latitude": -1.052, "longitude": -80.892},
            {"latitude": -1.062, "longitude": -80.888},
            {"latitude": -1.065, "longitude": -80.901},
            {"latitude": -1.055, "longitude": -80.905}
        ]

    center_lat = sum(p["latitude"] for p in polygon_pts) / len(polygon_pts) if polygon_pts else -1.058
    center_lon = sum(p["longitude"] for p in polygon_pts) / len(polygon_pts) if polygon_pts else -80.897

    # Crear mapa Folium interactivo
    tile_attr = "Map tiles by CartoDB / Esri"
    if tile_style == "Esri WorldImagery (Satélite)":
        tiles_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    elif tile_style == "CartoDB dark_matter":
        tiles_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    else:
        tiles_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles=tiles_url, attr=tile_attr)

    # 1. Dibujar el polígono de perímetro actual de la hacienda
    poly_coords = [[p["latitude"], p["longitude"]] for p in polygon_pts]
    folium.Polygon(
        locations=poly_coords,
        color="#38bdf8",
        weight=3,
        fill=True,
        fill_color="#0284c7",
        fill_opacity=0.25,
        popup=f"Cerco Delimitado: {sel_hacienda}",
        tooltip=f"<b>Recinto:</b> {sel_hacienda}"
    ).add_to(m)

    # 2. Agregar marcadores de los bovinos
    current_animals = get_all_animals()
    for anim in current_animals:
        status = anim.get("current_status", "Saludable")
        icon_color = "green" if status == "Saludable" else "orange" if status == "Bajo Observación" else "red"

        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 13px; color: #1e293b;">
            <b style="color: #0284c7;">🐄 Bovino {anim['id']} ({anim['name']})</b><br>
            <b>Raza:</b> {anim['breed']} ({anim['purpose']})<br>
            <b>Hacienda:</b> {anim['hacienda']} ({anim['location']})<br>
            <b>Estado:</b> <b style="color:{icon_color};">{anim['current_status']}</b><br>
            <b>Leche:</b> {anim['avg_milk_daily_liters']} Litros/día<br>
            <b>GPS:</b> Lat {anim.get('latitude', 0.0):.4f}, Lon {anim.get('longitude', 0.0):.4f}
        </div>
        """
        folium.Marker(
            location=[anim.get("latitude", -1.058), anim.get("longitude", -80.897)],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"<b>{anim['id']} ({anim['name']})</b> — {anim['current_status']}",
            icon=folium.Icon(color=icon_color, icon="heart", prefix="fa")
        ).add_to(m)

    # 3. Herramienta de Dibujo Interactivo (Draw Plugin)
    draw_plugin = Draw(
        export=True,
        filename=f"cerco_{sel_hacienda}.geojson",
        position="topleft",
        draw_options={
            'polyline': True,
            'polygon': True,
            'rectangle': True,
            'circle': False,
            'marker': True,
            'circlemarker': False
        },
        edit_options={'edit': True}
    )
    draw_plugin.add_to(m)

    # Renderizar mapa interactivo con st_folium
    st.markdown("##### 📍 Lienzo Interactivo — Dibuje Polígonos o Clickee en el Mapa")
    st_data = st_folium(m, width="100%", height=550, key="folium_interactive_map")

    # Captura de Eventos de Clic y Dibujo
    col_act1, col_act2 = st.columns(2, gap="medium")

    with col_act1:
        st.markdown("##### 📍 Captura de Clic Directo en Mapa")
        if st_data and st_data.get("last_clicked"):
            click_lat = st_data["last_clicked"]["lat"]
            click_lon = st_data["last_clicked"]["lng"]

            st.markdown(f"""
            <div style='background:#1e293b; padding:14px; border-radius:14px; border:1px solid #38bdf8;'>
                <b>Punto Clickeado:</b> Lat <code>{click_lat:.6f}</code> | Lon <code>{click_lon:.6f}</code>
            </div>
            """, unsafe_allow_html=True)

            if st.button("➕ Añadir Punto Clickeado al Cerco", type="primary", use_container_width=True):
                updated_pts = polygon_pts.copy()
                # Insertar antes del último punto de cierre
                updated_pts.insert(-1, {"latitude": click_lat, "longitude": click_lon})
                update_farm_perimeter(sel_hacienda, updated_pts)
                st.toast(f"✅ Punto ({click_lat:.4f}, {click_lon:.4f}) añadido al cerco", icon="📍")
                st.rerun()
        else:
            st.info("👆 Haga clic en cualquier punto del mapa para capturar sus coordenadas GPS y añadirlo al cerco.")

    with col_act2:
        st.markdown("##### ✏️ Captura de Polígono Dibujado en Pantalla")
        all_drawings = st_data.get("all_drawings") if st_data else None
        if all_drawings and len(all_drawings) > 0:
            last_shape = all_drawings[-1]
            geom_type = last_shape.get("geometry", {}).get("type")
            coords_raw = last_shape.get("geometry", {}).get("coordinates", [])

            st.markdown(f"**Figura Dibujada:** `<span class='pill-cyan'>{geom_type}</span>`", unsafe_allow_html=True)

            if geom_type in ["Polygon", "MultiPolygon"] and coords_raw:
                drawn_points = []
                ring = coords_raw[0] if geom_type == "Polygon" else coords_raw[0][0]
                for p in ring:
                    drawn_points.append({"latitude": p[1], "longitude": p[0]})

                if st.button("💾 Guardar Polígono Dibujado Como Nuevo Cerco", type="primary", use_container_width=True):
                    update_farm_perimeter(sel_hacienda, drawn_points)
                    st.toast("✅ Cerco actualizado con el dibujo del mapa", icon="🎨")
                    st.rerun()
        else:
            st.info("🎨 Use el botón de pentágono/polígono (esquina superior izquierda del mapa) para trazar visualmente el recinto.")

    st.divider()

    # Opción para reiniciar cerco a puntos por defecto
    if st.button("🗑️ Reiniciar Perímetro a Coordenadas por Defecto"):
        default_pts = [
            {"latitude": -1.055, "longitude": -80.905},
            {"latitude": -1.052, "longitude": -80.892},
            {"latitude": -1.062, "longitude": -80.888},
            {"latitude": -1.065, "longitude": -80.901},
            {"latitude": -1.055, "longitude": -80.905}
        ]
        update_farm_perimeter(sel_hacienda, default_pts)
        st.toast("Cerco reiniciado por defecto", icon="🔄")
        st.rerun()

# ---------------------------------------------------------
# TAB 5: BITÁCORA LEDGER
# ---------------------------------------------------------
with tab5:
    st.markdown("### 🔒 Trazabilidad Inmutable (SHA-256)")
    st.caption("Bitácora auditada digitalmente con sellos de tiempo ISO8601.")

    all_records = get_ledger_records()
    if all_records:
        df_ledger = pd.DataFrame(all_records)
        st.dataframe(
            df_ledger[["id", "timestamp", "animal_id", "agent_source", "action_type", "hitl_status", "hitl_reviewer", "hash_sha256"]],
            use_container_width=True
        )

        st.markdown("#### 🔍 Verificación de Hash SHA-256")
        sel_id = st.selectbox("Seleccionar Registro de Auditoría:", df_ledger["id"].tolist())
        rec = next(r for r in all_records if r["id"] == sel_id)

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown(f"**Hash SHA-256 Actual:**")
            st.markdown(f"<span class='pill-cyan'>{rec['hash_sha256']}</span>", unsafe_allow_html=True)
        with col_h2:
            st.markdown(f"**Hash Anterior (Encadenado):**")
            st.markdown(f"<span class='pill-cyan'>{rec['previous_hash']}</span>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 6: RENDIMIENTO & COSTOS
# ---------------------------------------------------------
with tab6:
    st.markdown("### 📊 Tablero de Rendimiento Productivo")
    st.caption("Monitoreo de curvas de ordeño y mermas en San Lorenzo, Santa Marianita y San Mateo.")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown("""
        <div class='midnight-card'>
            <p style='color: #94a3b8; font-size: 0.85rem; margin:0; font-weight:700;'>PRODUCCIÓN PROMEDIO</p>
            <h2 style='color: #38bdf8; margin: 4px 0; font-weight:800;'>19.3 L / día</h2>
            <span class='pill-emerald'>San Lorenzo</span>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown("""
        <div class='midnight-card'>
            <p style='color: #94a3b8; font-size: 0.85rem; margin:0; font-weight:700;'>PÉRDIDA EVITADA EST.</p>
            <h2 style='color: #34d399; margin: 4px 0; font-weight:800;'>$350.00 / mes</h2>
            <span class='pill-emerald'>+35% Eficiencia</span>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        st.markdown("""
        <div class='midnight-card'>
            <p style='color: #94a3b8; font-size: 0.85rem; margin:0; font-weight:700;'>AGROCALIDAD ECUADOR</p>
            <h2 style='color: #fbbf24; margin: 4px 0; font-weight:800;'>92% Vacunación</h2>
            <span class='pill-amber'>Aftosa</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 📈 Curvas Diarias de Producción de Leche (Litros)")
    chart_rows = []
    for a in animals_list:
        for ml in a.get("recent_milk_logs", []):
            chart_rows.append({
                "Bovino": f"{a['id']} ({a['name']})",
                "Fecha": ml["date"],
                "Litros": ml["liters"],
                "Hacienda": a["hacienda"]
            })

    if chart_rows:
        df_chart = pd.DataFrame(chart_rows)
        fig = px.line(
            df_chart,
            x="Fecha",
            y="Litros",
            color="Bovino",
            line_shape="spline",
            markers=True
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_family="Plus Jakarta Sans",
            font_color="#f8fafc"
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 7: IMPACTO ODS 8 & ODS 9
# ---------------------------------------------------------
with tab7:
    st.markdown("### 🌐 Impacto en Objetivos de Desarrollo Sostenible")

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        st.markdown("""
        <div class='midnight-card'>
            <h4 style='color: #38bdf8; margin-top:0;'>📈 ODS 8: Trabajo Decente & Crecimiento Económico</h4>
            <ul style='color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;'>
                <li><b>Simplificación Digital:</b> Reduce el tiempo de registro de 2 hours a 5 minutos dictados por voz.</li>
                <li><b>Protección de Ingresos:</b> Mitiga pérdidas del 35% mediante pre-diagnósticos veterinarios tempranos.</li>
                <li><b>Mercados Transparentes:</b> Certificación trazable del ganado de Manabí.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_o2:
        st.markdown("""
        <div class='midnight-card'>
            <h4 style='color: #34d399; margin-top:0;'>🏗️ ODS 9: Industria, Innovación e Infraestructura</h4>
            <ul style='color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;'>
                <li><b>Innovación en Campo:</b> Multiagente de IA, dibujo en mapa y QR en San Lorenzo, Santa Marianita y San Mateo.</li>
                <li><b>Criptografía Inmutable:</b> Sellado con marcas de tiempo e identificadores SHA-256.</li>
                <li><b>Bienestar Animal:</b> Garantiza aprobación humana (HITL) previa aplicación de tratamientos.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 24px; font-size: 0.85rem;'>✨ BovinoAI Manta v1.0 — Dibujo Interactivo en Mapa Folium</p>", unsafe_allow_html=True)
