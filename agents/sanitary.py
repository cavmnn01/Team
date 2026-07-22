from typing import Dict, Any, Optional, List
from tools.vet_rules import evaluate_clinical_symptoms, check_vaccination_status

class SanitaryAgent:
    """Agente de Diagnóstico Sanitario: Evalúa síntomas clínicos en lenguaje natural, vacunas vencidas y pre-alertas epidemiológicas."""

    def __init__(self):
        self.agent_name = "SanitaryAgent"

    def process(self, animal_profile: Dict[str, Any], symptoms_text: str, image_description: Optional[str] = None) -> Dict[str, Any]:
        combined_symptoms = symptoms_text
        if image_description:
            combined_symptoms += f" [Análisis de imagen/visión: {image_description}]"

        # Evaluar síntomas clínicos
        diagnosis_eval = evaluate_clinical_symptoms(combined_symptoms)

        # Evaluar estado de vacunación
        vaccinations = animal_profile.get("vaccinations", [])
        vac_eval = check_vaccination_status(vaccinations)

        # Determinar si requiere pre-alerta de aislamiento
        requires_alert = (
            diagnosis_eval["severity"] in ["CRÍTICA", "EMERGENCIA EPIDEMIOLÓGICA", "ALTA"] or
            vac_eval["has_expired_vaccines"]
        )

        return {
            "agent": self.agent_name,
            "animal_id": animal_profile.get("id"),
            "symptoms_reported": symptoms_text,
            "image_description": image_description,
            "pre_diagnosis": diagnosis_eval["pre_diagnosis"],
            "confidence_percent": diagnosis_eval["confidence_percent"],
            "severity": diagnosis_eval["severity"],
            "recommended_treatment_plan": diagnosis_eval["recommended_action"],
            "quarantine_suggested": diagnosis_eval["quarantine_suggested"],
            "vaccination_status": vac_eval,
            "requires_alert": requires_alert,
            "disclaimer": "⚠️ PRE-DIAGNÓSTICO GENERADO POR IA. Requiere aprobación o modificación obligatoria por el veterinario a cargo."
        }
