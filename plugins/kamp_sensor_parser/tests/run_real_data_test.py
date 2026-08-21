import json
import os
import sys
import time
from pathlib import Path

# core/src 및 루트 경로 바인딩
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "core" / "src"))

from plugins.kamp_sensor_parser.adapters.kamp_data_adapter import KampDataAdapter


def main() -> None:
    real_csv_path = "/home/kibeom/sftwin_project/data/raw/csv/kamp/experiment_01.csv"

    print("=" * 80)
    print(f"[실제 데이터 검증 시작] 대상 파일: {real_csv_path}")
    print("=" * 80)

    if not os.path.exists(real_csv_path):
        print(f"[ERROR] 대상 파일이 존재하지 않습니다: {real_csv_path}")
        return

    file_size_mb = os.path.getsize(real_csv_path) / (1024 * 1024)
    print(f"1. 파일 크기: {file_size_mb:.2f} MB")

    adapter = KampDataAdapter()

    # Step 1: FCN-KMP-001 사전 검증 테스트
    print("\n2. validate_file() 검증 수행 중...")
    try:
        is_valid = adapter.validate_file(real_csv_path)
        print(f"   -> [PASS] 사전 검증 성공 여부: {is_valid}")
    except Exception as e:
        print(f"   -> [FAIL] 사전 검증 실패: {e}")
        return

    # Step 2: FCN-KMP-002 & FCN-KMP-003 전체 파싱 파이프라인 실행
    print("\n3. parse() 파이프라인(스트리밍/보정/100Hz 리샘플링/직렬화) 실행 중...")
    start_t = time.perf_counter()
    try:
        parsed_result = adapter.parse(real_csv_path)
        elapsed = time.perf_counter() - start_t
        print(f"   -> [PASS] 파싱 완료 (소요 시간: {elapsed:.4f}초)")
    except Exception as e:
        print(f"   -> [FAIL] 파싱 실행 실패: {e}")
        return

    # Step 3: 반환된 실제 데이터 규격 및 요약 지표 출력
    print("\n4. 파싱 결과 메타데이터 확인:")
    print(f"   - 원본 파일명: {parsed_result.get('file_name')}")
    print(f"   - 총 정제 샘플 수: {parsed_result.get('total_samples'):,} rows")
    print(f"   - 샘플링 주기: {parsed_result.get('sampling_rate_hz')} Hz")
    print(
        f"   - 요약 통계 지표: {json.dumps(parsed_result.get('summary_metrics'), indent=6)}"
    )

    time_series = parsed_result.get("time_series", {})
    print(f"\n5. 시계열 컬럼별 데이터 길이 (Columnar Array):")
    for col, data in time_series.items():
        sample_preview = data[:3]
        print(f"   - {col:<10}: {len(data):,} 개 (처음 3개 샘플: {sample_preview})")

    print("\n" + "=" * 80)
    print("[SUCCESS] 실제 데이터 검증 파이프라인이 성공적으로 완료되었습니다.")
    print("=" * 80)


if __name__ == "__main__":
    main()
