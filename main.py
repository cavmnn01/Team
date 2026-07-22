import sys
import json
import os

# Configurar stdout a UTF-8 para evitar errores de codificación en consolas Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from agents.orchestrator import BovinoOrchestrator
from tools.database import init_db

def main():
    print("=" * 70)
    print("BOVINOAI MANTA: SISTEMA MULTIAGENTE DE TRAZABILIDAD GANADERA")
    print("Zona: Manta, San Lorenzo, Santa Marianita, San Mateo (Manabí - Ecuador)")
    print("Alineado con ODS 8 (Trabajo Decente) y ODS 9 (Innovación e Infraestructura)")
    print("=" * 70)

    init_db()
    orchestrator = BovinoOrchestrator()

    # Ejemplo de prueba en consola
    test_qr = "QR-MANTA-104"
    test_narrative = "La vaca 104 comió muy poco el día de hoy, tiene la ubre muy caliente e hinchada y produjo 4.5 litros menos de leche."
    test_user = "vaquero_sanlorenzo"

    print(f"\n[+] Procesando reporte de campo para Arete/QR: {test_qr}")
    print(f"[+] Novedad dictada: '{test_narrative}'\n")

    result = orchestrator.process_field_report(
        qr_or_id=test_qr,
        user_narrative=test_narrative,
        username=test_user
    )

    if not result["success"]:
        print(f"❌ Error: {result.get('error')}")
        sys.exit(1)

    print("--- RESUMEN DE EJECUCIÓN MULTIAGENTE ---")
    print(result["workflow_summary"])

    print("\n--- DETALLE DE SALIDAS POR AGENTE ---")
    print("\n1. AGENTE SANITARIO:")
    print(json.dumps(result["agent_outputs"]["sanitary"], indent=2, ensure_ascii=False))

    print("\n2. AGENTE PRODUCTIVO (Pydantic / Structured Output):")
    print(json.dumps(result["agent_outputs"]["productive"], indent=2, ensure_ascii=False))

    print("\n3. AGENTE LEDGER (Trazabilidad SHA-256):")
    print(json.dumps(result["agent_outputs"]["ledger"], indent=2, ensure_ascii=False))

    if result["requires_hitl_approval"]:
        print("\n" + "!" * 70)
        print(f"SUPERVISIÓN HUMANA REQUERIDA (Ticket HITL #{result['hitl_ticket_id']})")
        print("El pre-diagnóstico y la pérdida calculada requieren firma médica de aprobación.")
        print("Acciones obligatorias: [APROBAR TRATAMIENTO] | [MODIFICAR DIAGNÓSTICO] | [RECHAZAR ALERTA]")
        print("!" * 70)

        # Simular firma veterinaria
        decision_res = orchestrator.resolve_hitl_ticket(
            ticket_id=result["hitl_ticket_id"],
            decision="APROBADO",
            reviewer_name="Dr. Roberto Intriago (Veterinario)",
            comment="Aprobada aplicación de infusión intramamaria y aislamiento preventivo por 48h."
        )
        print("\n[+] Firma de Supervisor registrada exitosamente:")
        print(json.dumps(decision_res, indent=2, ensure_ascii=False))

    print("\n✅ Proceso finalizado. Inicie la interfaz gráfica con: `streamlit run ui/app.py`\n")

if __name__ == "__main__":
    main()
