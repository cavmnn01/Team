from typing import Dict, Any, Optional, List
from tools.database import add_ledger_entry, update_hitl_decision, get_ledger_records

class LedgerAuditAgent:
    """Agente de Trazabilidad e Historial: Registra eventos en bitácora inmutable con firma criptográfica SHA-256 e ISO8601."""

    def __init__(self):
        self.agent_name = "LedgerAuditAgent"

    def record_multiagent_evaluation(
        self,
        animal_id: str,
        sanitary_result: Dict[str, Any],
        productive_result: Dict[str, Any],
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea una entrada pendiente de revisión HITL en la bitácora inmutable."""

        payload = {
            "sanitary": sanitary_result,
            "productive": productive_result,
            "reported_by": user_info,
            "suggested_status": "Bajo Tratamiento" if sanitary_result.get("requires_alert") else "Saludable"
        }

        entry = add_ledger_entry(
            animal_id=animal_id,
            agent_source="BovinoAI-Multiagent-System",
            action_type="EVALUACION_DE_CAMPO_HITL",
            payload=payload,
            hitl_status="PENDIENTE",
            hitl_reviewer=None,
            hitl_comment=None
        )

        return {
            "agent": self.agent_name,
            "ledger_ticket_id": entry["id"],
            "hash_sha256": entry["hash_sha256"],
            "previous_hash": entry["previous_hash"],
            "timestamp": entry["timestamp"],
            "hitl_status": entry["hitl_status"],
            "message": f"Registro de trazabilidad grabado exitosamente con Hash SHA-256: {entry['hash_sha256'][:16]}..."
        }

    def record_human_decision(
        self,
        ticket_id: int,
        decision: str,
        reviewer_name: str,
        comment: str
    ) -> Dict[str, Any]:
        """Registra la firma y decisión del supervisor humano (Veterinario/Admin)."""

        update_hitl_decision(
            entry_id=ticket_id,
            decision=decision,
            reviewer=reviewer_name,
            comment=comment
        )

        return {
            "agent": self.agent_name,
            "ticket_id": ticket_id,
            "decision": decision,
            "reviewer": reviewer_name,
            "comment": comment,
            "status": "FIRMADO_Y_REGISTRADO"
        }

    def get_audit_trail(self, animal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera la cadena completa de auditoría."""
        return get_ledger_records(animal_id)
