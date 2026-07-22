import unittest
import os
import sqlite3
import json

# Asegurar entorno de pruebas
os.environ["DB_PATH"] = "test_bovino_manta.db"

from tools.database import init_db, get_connection, get_all_animals, get_ledger_records
from tools.vet_rules import evaluate_clinical_symptoms, calculate_yield_drop, check_vaccination_status
from agents.identifier import IdentifierAgent
from agents.sanitary import SanitaryAgent
from agents.productive import ProductiveAgent
from agents.ledger import LedgerAuditAgent
from agents.orchestrator import BovinoOrchestrator

class TestBovinoAIManta(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("test_bovino_manta.db"):
            try:
                os.remove("test_bovino_manta.db")
            except Exception:
                pass

    def test_01_database_init(self):
        animals = get_all_animals()
        self.assertGreater(len(animals), 0)
        self.assertEqual(animals[0]["id"], "BOV-104")

    def test_02_identifier_agent(self):
        agent = IdentifierAgent()
        result = agent.process("QR-MANTA-104", username="vaquero_sanlorenzo")
        self.assertTrue(result["success"])
        self.assertEqual(result["animal_id"], "BOV-104")
        self.assertEqual(result["hacienda"], "Hacienda El Encanto")

    def test_03_sanitary_rules(self):
        symptoms = "La vaca 104 tiene la ubre muy inflamada con grumos en la leche"
        eval_res = evaluate_clinical_symptoms(symptoms)
        self.assertIn("Mastitis", eval_res["pre_diagnosis"])
        self.assertGreaterEqual(eval_res["confidence_percent"], 50)

    def test_04_productive_agent_yield_drop(self):
        agent = ProductiveAgent()
        profile = {"id": "BOV-104", "purpose": "Leche", "avg_milk_daily_liters": 20.0}
        res = agent.process(profile, reported_milk_liters=15.0)

        # 20 -> 15 es una caída del 25%
        self.assertEqual(res.drop_percentage, 25.0)
        self.assertTrue(res.has_significant_drop)
        self.assertEqual(res.alert_level, "CRÍTICA")
        self.assertGreater(res.estimated_daily_financial_loss_usd, 0)

    def test_05_ledger_hash_integrity(self):
        ledger = LedgerAuditAgent()
        res = ledger.record_multiagent_evaluation(
            animal_id="BOV-104",
            sanitary_result={"pre_diagnosis": "Mastitis", "severity": "ALTA"},
            productive_result={"drop_percentage": 25.0},
            user_info={"username": "vaquero_sanlorenzo", "role": "Vaquero"}
        )
        self.assertIn("hash_sha256", res)
        self.assertEqual(len(res["hash_sha256"]), 64) # Longitud estándar SHA-256

        # Verificar firmas en DB
        records = get_ledger_records("BOV-104")
        self.assertGreater(len(records), 0)
        self.assertEqual(records[0]["hash_sha256"], res["hash_sha256"])

    def test_06_orchestrator_end_to_end_and_hitl(self):
        orchestrator = BovinoOrchestrator()
        report_res = orchestrator.process_field_report(
            qr_or_id="BOV-104",
            user_narrative="La vaca 104 comió muy poco hoy, tiene la ubre inflamada y produjo 15 litros de leche."
        )

        self.assertTrue(report_res["success"])
        self.assertTrue(report_res["requires_hitl_approval"])
        ticket_id = report_res["hitl_ticket_id"]

        # Resolver ticket HITL
        hitl_res = orchestrator.resolve_hitl_ticket(
            ticket_id=ticket_id,
            decision="APROBADO",
            reviewer_name="Dr. Roberto Intriago",
            comment="Aprobado tratamiento e infusión intramamaria."
        )

        self.assertEqual(hitl_res["decision"], "APROBADO")
        self.assertEqual(hitl_res["reviewer"], "Dr. Roberto Intriago")

if __name__ == "__main__":
    unittest.main()
