from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from tools.vet_rules import calculate_yield_drop

class ProductiveAnalysisOutput(BaseModel):
    animal_id: str = Field(description="Identificador único del bovino")
    purpose: str = Field(description="Propósito del animal (Leche, Carne, Doble Propósito)")
    historical_avg: float = Field(description="Promedio histórico diario (litros o kg)")
    current_value: float = Field(description="Valor reportado el día de hoy")
    drop_percentage: float = Field(description="Porcentaje de caída calculada")
    has_significant_drop: bool = Field(description="True si la caída es >= 15%")
    estimated_daily_financial_loss_usd: float = Field(description="Pérdida económica estimada en USD por día")
    alert_level: str = Field(description="Nivel de alerta (NORMAL, ADVERTENCIA, CRÍTICA)")
    analysis_summary: str = Field(description="Resumen explicativo estructurado")

class ProductiveAgent:
    """Agente de Rendimiento y Costos: Analiza mermas de leche/peso, detecta variaciones >= 15% y calcula pérdidas financieras."""

    def __init__(self):
        self.agent_name = "ProductiveAgent"

    def process(
        self,
        animal_profile: Dict[str, Any],
        reported_milk_liters: Optional[float] = None,
        reported_weight_kg: Optional[float] = None
    ) -> ProductiveAnalysisOutput:
        animal_id = animal_profile.get("id", "UNKNOWN")
        purpose = animal_profile.get("purpose", "Leche")

        if purpose in ["Leche", "Doble Propósito"] and reported_milk_liters is not None:
            hist_avg = float(animal_profile.get("avg_milk_daily_liters", 20.0))
            current_val = float(reported_milk_liters)
            unit = "litros"
        elif reported_weight_kg is not None:
            hist_avg = float(animal_profile.get("weight_kg", 500.0))
            current_val = float(reported_weight_kg)
            unit = "kg"
        else:
            # Si no se envió valor numérico explícito en el reporte, tomamos el último log si existe o asumimos normalidad
            hist_avg = float(animal_profile.get("avg_milk_daily_liters", 20.0))
            current_val = hist_avg
            unit = "litros"

        yield_eval = calculate_yield_drop(hist_avg, current_val, unit)

        drop_pct = yield_eval["drop_percentage"]
        if drop_pct >= 25.0:
            alert_lvl = "CRÍTICA"
        elif drop_pct >= 15.0:
            alert_lvl = "ADVERTENCIA"
        else:
            alert_lvl = "NORMAL"

        summary = (
            f"Producción actual: {current_val} {unit} vs Promedio: {hist_avg} {unit}. "
            f"Variación: {drop_pct:.1f}%. Impacto financiero estimado: ${yield_eval['estimated_daily_financial_loss_usd']:.2f}/día."
        )

        return ProductiveAnalysisOutput(
            animal_id=animal_id,
            purpose=purpose,
            historical_avg=hist_avg,
            current_value=current_val,
            drop_percentage=drop_pct,
            has_significant_drop=yield_eval["has_significant_drop"],
            estimated_daily_financial_loss_usd=yield_eval["estimated_daily_financial_loss_usd"],
            alert_level=alert_lvl,
            analysis_summary=summary
        )
