from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateDualKpiReportRequestDto:
    baseline_oee: float
    improved_oee: float
    baseline_fpy: float
    improved_fpy: float
    turnkey_quote_cost: float
