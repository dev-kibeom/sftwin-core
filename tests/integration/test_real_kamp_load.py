# tests/integration/test_real_kamp_load.py
import os

import pytest
from asset_twin.twin_reconstruction.adapters.outbound.kamp_data_adapter import (
    KampDataAdapter,
)


def test_real_kamp_dataset_parsing():
    # KAMP 실제 파일 경로 지정
    real_kamp_path = "data/assets/kamp/cnc_sample.csv"

    if not os.path.exists(real_kamp_path):
        pytest.skip("실제 KAMP 데이터 파일이 data/assets/kamp/에 없으므로 스킵합니다.")

    adapter = KampDataAdapter(memory_chunk_size=10000)
    baseline = adapter.parse_sensor_log(real_kamp_path)

    print(f"\n[KAMP 데이터 로드 성공]")
    print(f"총 행 수(Total Rows): {baseline.raw_sensor_summary['total_rows']}")
    print(f"평균 편차(Mean Dev): {baseline.raw_sensor_summary['mean_deviation']}")

    assert baseline.raw_sensor_summary["total_rows"] > 0
