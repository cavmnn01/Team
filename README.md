# 🐄 BovinoAI Manta: Sistema Multiagente para Identificación, Control Sanitario y Trazabilidad Ganadera

> **Solución Multiagente de IA para la Gestión Ganadera Bovina en Manta y la Provincia de Manabí.**  
> *Alineado con el **ODS 8 (Trabajo Decente y Crecimiento Económico)** y el **ODS 9 (Industria, Innovación e Infraestructura)**.*

---

## 📋 Resumen del Proyecto

**BovinoAI Manta** es una plataforma integral basada en sistemas multiagente de Inteligencia Artificial que automatiza la ingesta de novedades de campo, el pre-diagnóstico veterinario, la detección de mermas productivas ($\ge 15\%$) y la auditoría digital inmutable (cadena SHA-256) para haciendas ganaderas en Manta (San Lorenzo, Santa Marianita, San Mateo) y Manabí.

---

## 🛠️ Arquitectura Multiagente

El sistema está compuesto por los siguientes agentes especializados:

1. **`Bovino-Orchestrator` (Agente Orquestador Principal):** Coordina las llamadas entre los agentes especializados, procesa dictados en lenguaje natural y gestiona la sesión de usuario.
2. **`IdentifierAgent` (Agente Identificador y Datos Base):** Valida la lectura del código QR/Arete, verifica permisos RBAC (Vaquero, Veterinario, Administrador) y carga la hoja de vida del bovino.
3. **`SanitaryAgent` (Agente de Diagnóstico Sanitario):** Diagnostica afecciones clínicas (Mastitis, Anaplasmosis, Fiebre Aftosa, Parasitosis), audita el esquema de vacunación (AGROCALIDAD Ecuador) y genera pre-alertas.
4. **`ProductiveAgent` (Agente de Rendimiento y Costos):** Implementa Structured Outputs con **Pydantic** para calcular caídas porcentuales de leche/peso, detectar caídas $\ge 15\%$ y estimar mermas económicas en USD.
5. **`LedgerAuditAgent` (Agente de Trazabilidad e Historial):** Genera bitácoras inmutables selladas con marca temporal ISO8601 y hash SHA-256 encadenado.

---

## 🛑 Supervisión Humana (*Human-In-The-Loop* - HITL)

Para salvaguardar la inocuidad alimentaria y evitar el uso desmedido de medicamentos:
* Los agentes de IA generan pre-diagnósticos y borradores de órdenes, pero **tienen prohibido aplicar fármacos o declarar aislamiento formal de forma autónoma**.
* El Veterinario o Administrador recibe un ticket interactivo en el dashboard y debe firmar obligatoriamente una de las tres opciones:
  * `[APROBAR TRATAMIENTO]`
  * `[MODIFICAR DIAGNÓSTICO]`
  * `[RECHAZAR ALERTA]`
* Cada firma queda auditada inmutablemente en el Ledger con el nombre del médico firmanter.

---

## 🚀 Guía de Instalación y Ejecución

### 1. Requisitos Previos
* Python 3.10+
* Virtualenv (opcional pero recomendado)

### 2. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecución Rápida en Consola (CLI)
```bash
python main.py
```

### 4. Ejecución del Dashboard Grafico Streamlit (Web UI)
```bash
streamlit run ui/app.py
```
El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## 🧪 Pruebas Automatizadas
Para ejecutar la suite completa de pruebas unitarias e integración:
```bash
python -m unittest discover tests
```

---

## 🌐 Impacto ODS 8 y ODS 9 en Manabí

* **ODS 8 (Trabajo Decente y Crecimiento Económico):** Reduce el trabajo administrativo de 2 horas a 5 minutos por jornada mediante dictado por voz/texto, protegiendo los ingresos rurales ante pérdidas del 35% de producción.
* **ODS 9 (Industria, Innovación e Infraestructura):** Digitaliza la infraestructura ganadera de Manabí mediante firmas criptográficas SHA-256 e IA multiagente.
