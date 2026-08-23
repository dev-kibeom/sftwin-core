from pydantic_settings import BaseSettings


class KampParserSettings(BaseSettings):
    """KAMP CSV 파서 설정 및 런타임 제약 파라미터 (Settings Injection)"""

    # TODO: config로 세팅
    default_kamp_data_dir: str = "~/sftwin_project/data/raw/csv/kamp"
    allowed_file_extension: str = ".csv"  # 허용 파일 확장자
    csv_read_chunk_size: int = 50000  # 청크당 읽을 행 수
    max_allowable_file_size_mb: int = 100  # 파일당 최대 허용 크기 (100MB)
    drop_null_threshold: float = 0.05  # 결측치 5% 초과 시 파일 오류 처리
    default_sampling_rate_hz: float = 100.0  # 100Hz 기본 샘플링 주기
