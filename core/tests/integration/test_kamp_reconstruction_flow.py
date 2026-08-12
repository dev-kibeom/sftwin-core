import pandas as pd
import pytest

from src.asset_twin.twin_reconstruction.adapters.outbound.kamp_data_adapter import (
    KampDataAdapter,
)


@pytest.fixture
def mock_kamp_csv(tmp_path):
    """임시 KAMP 센서 로그 CSV 생성"""
    file_path = tmp_path / "test_kamp.csv"
    df = pd.DataFrame(
        {"timestamp": range(100), "current": [10.0] * 100, "deviation": [0.03] * 100}
    )
    df.to_csv(file_path, index=False)
    return str(file_path)


def test_kamp_adapter_parsing_success(mock_kamp_csv):
    """KampDataAdapter chunksize 스트리밍 정상 동작 통전 검증"""
    adapter = KampDataAdapter(memory_chunk_size=50)
    baseline = adapter.parse_sensor_log(mock_kamp_csv)

    assert baseline is not None
    assert baseline.raw_sensor_summary["total_rows"] == 100
    assert pytest.approx(baseline.raw_sensor_summary["mean_deviation"], 0.001) == 0.03
