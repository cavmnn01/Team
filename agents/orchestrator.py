import os
import re
import json
from typing import Dict, Any, Optional, Tuple, List
from agents.identifier import IdentifierAgent
from agents.sanitary import SanitaryAgent
from agents.productive import ProductiveAgent
from agents.ledger import LedgerAuditAgent

class BovinoOrchestrator:
    """Orquestador Principal Multiagente para BovinoAI Manta.
    Coordina los agentes especializados (Identifier, Sanitary, Productive, Ledger)
    y gestiona la supervisión humana (Human-In-The-Loop).
    """

    def __init__(self):
        self.identifier = IdentifierAgent()
        self.sanitary = SanitaryAgent()
        self.productive = ProductiveAgent()
        self.ledger = LedgerAuditAgent()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

    def extract_numeric_value_from_text(self, text: str, historical_avg: float) -> Tuple[Optional[float], Optional[float]]:
        """Extrae de la novedad en lenguaje natural si se especificó litros o peso."""
        milk_liters = None
        weight_kg = None

        # Patrón: "produjo X litros", "bajó a X litros", "X L", "X litros"
        match_liters_to = re.search(r'(?:produjo|dio|baj[oó] a|rendimiento de)\s*(\d+(?:\.\d+)?)\s*(?:litros|l|lt)', text, re.IGNORECASE)
        if match_liters_to:
            milk_liters = float(match_liters_to.group(1))

        # Patrón: "4 litros menos", "bajó 4 litros", "menos 4L"
        match_liters_less = re.search(r'(?:baj[oó]|menos|perdi[oó])\s*(\d+(?:\.\d+)?)\s*(?:litros|l|lt)', text, re.IGNORECASE)
        if match_liters_less and milk_liters is None:
            diff = float(match_liters_less.group(1))
            milk_liters = max(0.0, historical_avg - diff)

        # Patrón: "peso X kg"
        match_weight = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilos)', text, re.IGNORECASE)
        if match_weight:
            weight_kg = float(match_weight.group(1))

        return milk_liters, weight_kg

    def process_field_report(
        self,
        qr_or_id: str,
        user_narrative: str,
        username: str = "vaquero_sanlorenzo",
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesa una novedad de campo completa ejecutando el pipeline multiagente."""

        # 1. Agente Identificador
        id_result = self.identifier.process(qr_or_id, username=username)
        if not id_result["success"]:
            return {
                "success": False,
                "orchestrator_status": "ERROR_IDENTIFICACION",
                "error": id_result["error"]
            }

        animal_profile = id_result["full_profile"]
        user_info = id_result["user"]
        hist_milk = float(animal_profile.get("avg_milk_daily_liters", 20.0))

        # Extraer litros o peso si están presentes en la voz/texto
        reported_milk, reported_weight = self.extract_numeric_value_from_text(user_narrative, hist_milk)

        # 2. Agente Sanitario
        sanitary_result = self.sanitary.process(
            animal_profile=animal_profile,
            symptoms_text=user_narrative,
            image_description=image_description
        )

        # 3. Agente Productivo (Structured Output con Pydantic)
        productive_result_obj = self.productive.process(
            animal_profile=animal_profile,
            reported_milk_liters=reported_milk,
            reported_weight_kg=reported_weight
        )
        productive_result = productive_result_obj.model_dump()

        # 4. Agente Ledger (Bitácora Inmutable + Creación de Ticket HITL)
        ledger_result = self.ledger.record_multiagent_evaluation(
            animal_id=animal_profile["id"],
            sanitary_result=sanitary_result,
            productive_result=productive_result,
            user_info=user_info
        )

        # Determinar si el ticket requiere intervención médica inmediata
        requires_hitl_approval = (
            sanitary_result.get("requires_alert") or
            productive_result.get("has_significant_drop")
        )

        workflow_summary = (
            f"🟢 **Paso 1 (IdentifierAgent):** Animal {animal_profile['id']} ({animal_profile['name']}) identificado.\n"
            f"🟡 **Paso 2 (SanitaryAgent):** Pre-diagnóstico: '{sanitary_result['pre_diagnosis']}' (Confianza: {sanitary_result['confidence_percent']}%).\n"
            f"📊 **Paso 3 (ProductiveAgent):** Caída productiva del {productive_result['drop_percentage']}% (${productive_result['estimated_daily_financial_loss_usd']}/día).\n"
            f"🔒 **Paso 4 (LedgerAuditAgent):** Ticket HITL #{ledger_result['ledger_ticket_id']} firmado con SHA-256."
        )

        return {
            "success": True,
            "orchestrator_status": "COMPLETADO_PENDIENTE_HITL" if requires_hitl_approval else "COMPLETADO_AUTO",
            "animal_profile": animal_profile,
            "user_info": user_info,
            "agent_outputs": {
                "identifier": id_result,
                "sanitary": sanitary_result,
                "productive": productive_result,
                "ledger": ledger_result
            },
            "requires_hitl_approval": requires_hitl_approval,
            "hitl_ticket_id": ledger_result["ledger_ticket_id"],
            "workflow_summary": workflow_summary
        }

    def resolve_hitl_ticket(
        self,
        ticket_id: int,
        decision: str,  # 'APROBADO', 'MODIFICADO', 'RECHAZADO'
        reviewer_name: str,
        comment: str
    ) -> Dict[str, Any]:
        """Resuelve el ticket de aprobación humana con firma digital en la bitácora."""
        return self.ledger.record_human_decision(
            ticket_id=ticket_id,
            decision=decision,
            reviewer_name=reviewer_name,
            comment=comment
        )
