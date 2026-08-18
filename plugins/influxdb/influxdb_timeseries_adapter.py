"""
@file influxdb_timeseries_adapter.py
@description InfluxDB I/O 및 Flux 쿼리를 담당하는 BaseTimeSeriesPort 구현체
"""

import os
from typing import Any

from influxdb_client.client.influxdb_client import InfluxDBClient
from kpi_b2b.ports.outbound.i_time_series import ITimeSeries
from shared.context.log_context import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger


class InfluxDbTimeSeriesAdapter(ITimeSeries):
    def __init__(
        self, client: Any = None, system_logger: GlobalSystemLogger | None = None
    ):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="InfluxDbTimeSeriesAdapter"
        )
        url = os.getenv("INFLUXDB_URL", "http://sftwin-influxdb:8086")
        token = os.getenv("INFLUXDB_TOKEN", "sftwin-super-secret-auth-token-2026")
        org = os.getenv("INFLUXDB_ORG", "sftwin")
        self._bucket = os.getenv("INFLUXDB_BUCKET", "telemetry-bucket")

        if client:
            self._client = client
        else:
            try:
                self._client = InfluxDBClient(
                    url=url, token=token, org=org, timeout=3000
                )
            except Exception as e:
                self._system_logger.warn(f"InfluxDB client init fallback: {e}")
                self._client = None

    def fetch_simulation_logs(self, sim_id: str) -> list[dict[str, Any]]:
        if not self._client:
            return self._generate_mock_simulation_logs(sim_id)

        flux_query = f"""
        from(bucket: "{self._bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "telemetry_logs")
          |> filter(fn: (r) => r["sim_id"] == "{sim_id}")
        """
        try:
            query_api = self._client.query_api()
            tables = query_api.query(flux_query)
            results = []
            for table in tables:
                for record in table.records:
                    results.append(record.values)

            if not results:
                return self._generate_mock_simulation_logs(sim_id)
            return results
        except Exception as exc:
            log_ctx = LogContext(context={"sim_id": sim_id}, exc=exc)
            self._system_logger.warn(
                f"InfluxDB Query failed for {sim_id}: {exc}. Returning fallback logs.",
                log_ctx,
            )
            return self._generate_mock_simulation_logs(sim_id)

    def _generate_mock_simulation_logs(self, sim_id: str) -> list[dict[str, Any]]:
        """데모 및 시뮬레이션 초기 검증용 Mock 시계열 로그 생성"""
        return [
            {
                "sim_id": sim_id,
                "uptime": 3500.0,
                "total_time": 3600.0,
                "ideal_cycle": 12.0,
                "actual_cycle": 12.5,
                "good_count": 280,
                "total_count": 288,
            }
        ]
