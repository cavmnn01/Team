from typing import Dict, Any, List, Tuple
from datetime import datetime

# Precio promedio de la leche en finca (Manabí / Ecuador): $0.50 por litro
PRICE_PER_LITER_USD = 0.50
# Precio promedio de carne en pie: $1.80 por kg
PRICE_PER_KG_MEAT_USD = 1.80

DISEASE_KNOWLEDGE_BASE = [
    {
        "disease": "Mastitis Subclínica / Clínica",
        "keywords": ["ubre", "inflamada", "leche", "grumos", "dolor", "bajada de leche", "cuarteto", "mastitis", "calor ubre"],
        "severity": "ALTA",
        "recommended_action": "Prueba CMT (California Mastitis Test), aislamiento en ordeño y tratamiento antibiótico intramamario previa orden veterinaria.",
        "requires_quarantine": False,
        "contagious": True
    },
    {
        "disease": "Anaplasmosis / Babesiosis (Fiebre de Garrapata)",
        "keywords": ["garrapata", "fiebre", "anemia", "mucosas amarillas", "ictericia", "debilidad", "orinando oscuro", "garrapatas"],
        "severity": "CRÍTICA",
        "recommended_action": "Hemograma urgente, aplicación de imidocarb / oxitetraciclina y baño garrapaticida.",
        "requires_quarantine": False,
        "contagious": False
    },
    {
        "disease": "Sospecha de Fiebre Aftosa",
        "keywords": ["afta", "boca", "babeo", "vesícula", "cojera", "pezuña", "lengua", "llagas boca", "babeando"],
        "severity": "EMERGENCIA EPIDEMIOLÓGICA",
        "recommended_action": "Aislamiento inmediato del animal, reporte obligatorio urgente a AGROCALIDAD Ecuador y suspensión de movimiento de ganado.",
        "requires_quarantine": True,
        "contagious": True
    },
    {
        "disease": "Neumonía Bovino / Síndrome Respiratorio",
        "keywords": ["tos", "secreción nasal", "dificultad respiratoria", "agitado", "pulmón", "respiración rápida", "moco"],
        "severity": "MEDIA-ALTA",
        "recommended_action": "Evaluación auscultatoria, antibióticoterapia sistémica de amplio espectro y refugio seco y ventilado.",
        "requires_quarantine": True,
        "contagious": True
    },
    {
        "disease": "Parasitosis Gastrointestinal",
        "keywords": ["flaco", "pelaje opaco", "diarrea", "barba hinchada", "edema submandibular", "heces blandas", "parasitos"],
        "severity": "MODERADA",
        "recommended_action": "Examen coproparasitológico y desparasitación oral / inyectable específica.",
        "requires_quarantine": False,
        "contagious": False
    }
]

def evaluate_clinical_symptoms(symptoms_text: str) -> Dict[str, Any]:
    """Analiza el texto de síntomas e identifica posibles afecciones sanitarias."""
    text_lower = symptoms_text.lower()
    matches = []

    for item in DISEASE_KNOWLEDGE_BASE:
        score = sum(1 for kw in item["keywords"] if kw in text_lower)
        if score > 0:
            confidence = min(95, score * 30 + 35)
            matches.append({
                "disease": item["disease"],
                "confidence_percent": confidence,
                "severity": item["severity"],
                "recommended_action": item["recommended_action"],
                "requires_quarantine": item["requires_quarantine"]
            })

    if not matches:
        return {
            "pre_diagnosis": "Indeterminado / Evaluación General Requerida",
            "confidence_percent": 40,
            "severity": "BAJA",
            "matches": [],
            "recommended_action": "Revisión física general por parte del vaquero o veterinario de turno.",
            "quarantine_suggested": False
        }

    # Ordenar por confianza
    matches.sort(key=lambda x: x["confidence_percent"], reverse=True)
    top_match = matches[0]

    return {
        "pre_diagnosis": top_match["disease"],
        "confidence_percent": top_match["confidence_percent"],
        "severity": top_match["severity"],
        "matches": matches,
        "recommended_action": top_match["recommended_action"],
        "quarantine_suggested": top_match["requires_quarantine"]
    }

def check_vaccination_status(vaccinations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verifica si el animal tiene vacunas vencidas o próximas a vencer."""
    expired = []
    up_to_date = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for vac in vaccinations:
        due_date = vac.get("due_date", "")
        disease = vac.get("disease", "")
        if due_date and due_date < today_str:
            expired.append({
                "disease": disease,
                "due_date": due_date,
                "batch": vac.get("batch", "N/A")
            })
        else:
            up_to_date.append({
                "disease": disease,
                "due_date": due_date
            })

    has_expired = len(expired) > 0
    return {
        "has_expired_vaccines": has_expired,
        "expired_vaccines": expired,
        "up_to_date_vaccines": up_to_date,
        "warning": "¡ALERTA AGROCALIDAD! Posee vacunas obligatorias vencidas." if has_expired else "Calendario de vacunación al día."
    }

def calculate_yield_drop(
    historical_avg: float,
    current_val: float,
    unit: str = "litros"
) -> Dict[str, Any]:
    """Calcula la caída porcentual y costo económico de la pérdida productiva."""
    if historical_avg <= 0:
        return {
            "has_significant_drop": False,
            "drop_percentage": 0.0,
            "loss_quantity": 0.0,
            "estimated_daily_financial_loss_usd": 0.0,
            "message": "Sin histórico previo de producción."
        }

    drop_qty = max(0.0, historical_avg - current_val)
    drop_pct = (drop_qty / historical_avg) * 100.0
    is_atypical = drop_pct >= 15.0

    if unit == "litros":
        daily_loss_usd = drop_qty * PRICE_PER_LITER_USD
    else:
        daily_loss_usd = drop_qty * PRICE_PER_KG_MEAT_USD

    return {
        "has_significant_drop": is_atypical,
        "drop_percentage": round(drop_pct, 2),
        "loss_quantity": round(drop_qty, 2),
        "estimated_daily_financial_loss_usd": round(daily_loss_usd, 2),
        "unit": unit,
        "message": f"Caída atípica del {drop_pct:.1f}% ({drop_qty:.1f} {unit}/día). Pérdida de ${daily_loss_usd:.2f}/día." if is_atypical else f"Variación normal del {drop_pct:.1f}%."
    }
