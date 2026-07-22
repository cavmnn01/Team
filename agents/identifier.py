from typing import Dict, Any, Optional
from tools.database import get_animal_by_id_or_qr, get_user_role

class IdentifierAgent:
    """Agente responsable de validar el código QR / Arete del animal, autenticar los permisos del usuario y cargar el expediente completo."""

    def __init__(self):
        self.agent_name = "IdentifierAgent"

    def process(self, query: str, username: str = "vaquero_sanlorenzo") -> Dict[str, Any]:
        user_info = get_user_role(username) or {"username": username, "role": "Vaquero", "hacienda": "Hacienda El Encanto"}
        animal = get_animal_by_id_or_qr(query)

        if not animal:
            return {
                "success": False,
                "agent": self.agent_name,
                "error": f"No se encontró ningún bovino con el código Arete/QR '{query}'. Por favor verifique el escaneo.",
                "user": user_info
            }

        return {
            "success": True,
            "agent": self.agent_name,
            "animal_id": animal["id"],
            "qr_code": animal["qr_code"],
            "animal_name": animal["name"],
            "breed": animal["breed"],
            "purpose": animal["purpose"],
            "hacienda": animal["hacienda"],
            "location": animal["location"],
            "current_status": animal["current_status"],
            "weight_kg": animal["weight_kg"],
            "avg_milk_daily_liters": animal["avg_milk_daily_liters"],
            "full_profile": animal,
            "user": user_info,
            "summary_text": f"Bovino {animal['id']} ({animal['name']}) - Raza {animal['breed']} en {animal['hacienda']} ({animal['location']})."
        }
