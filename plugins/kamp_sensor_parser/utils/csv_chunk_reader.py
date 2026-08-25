from collections.abc import Iterator
from pathlib import Path

import pandas as pd


class CsvChunkReader:
    """CSV 대용량 청크 스트리밍 및 헤더 샘플링 I/O 유틸리티"""

    def __init__(self, default_chunk_size: int = 50000) -> None:
        self._default_chunk_size = default_chunk_size

    def read_csv_in_chunks(
        self, file_path: Path | str, chunk_size: int | None = None
    ) -> Iterator[pd.DataFrame]:
        """CSV 파일을 지정된 청크 크기 단위로 스트리밍 생성"""
        size = chunk_size or self._default_chunk_size
        return pd.read_csv(file_path, chunksize=size)
