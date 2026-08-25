from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KampParserSettings(BaseSettings):
    """KAMP CSV 파서 설정 및 런타임 제약 파라미터 (Settings Injection)"""

    model_config = SettingsConfigDict(env_prefix="KAMP_PARSER_", extra="ignore")

    default_kamp_data_dir: Path = Field(
        default=Path("~/sftwin_project/data/raw/csv/kamp").expanduser(),
        description="KAMP 원시 데이터 디렉터리 경로",
    )
    allowed_file_extension: str = Field(
        default=".csv",
        description="허용 파일 확장자",
    )
    csv_read_chunk_size: int = Field(
        default=50000,
        gt=0,
        description="청크당 읽을 행 수",
    )
    max_allowable_file_size_mb: int = Field(
        default=100,
        gt=0,
        description="파일당 최대 허용 크기 (MB)",
    )
    drop_null_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="결측치 허용 임계 비율 (5%)",
    )
    default_sampling_rate_hz: float = Field(
        default=100.0,
        gt=0.0,
        description="목표 리샘플링 주기 (Hz)",
    )
    min_required_columns: int = Field(
        default=10,
        gt=0,
        description="CSV 헤더 최소 필수 컬럼 수",
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_allowable_file_size_mb * 1024 * 1024
