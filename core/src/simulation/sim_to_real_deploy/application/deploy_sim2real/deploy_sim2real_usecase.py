"""
[File Summary]
DeploySim2RealUseCase (Stateless Singleton)
도메인 객체를 생성하고 배포 패키지 추출을 조율하는 유즈케이스입니다.
사전 검증(Guard) 및 원시 I/O 에러에 대한 마스킹(500) 처리를 담당합니다.
"""

from typing import Any

from shared.dtos.log_dtos import LogContext
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext
from simulation.ports.outbound.i_fleet_deploy import IFleetDeploy
from simulation.sim_to_real_deploy.domain.deploy_format_enums import (
    DeployPackageFormatEnum,
)
from simulation.sim_to_real_deploy.domain.deploy_package import DeployPackage


class DeploySim2RealUseCase:
    def __init__(
        self, fleet_deploy_port: IFleetDeploy, logger: GlobalSystemLogger | None = None
    ):
        self._fleet_deploy_port = fleet_deploy_port
        self._logger = logger or GlobalSystemLogger(
            component_name="RunFmsSimulationUseCase"
        )

    def execute(
        self,
        package_id: str,
        format_type: str,
        config: dict[str, Any],
        ctx: UserContext,
    ) -> bool:
        log_ctx = LogContext(trace_id=f"TRC-DEPLOY-{package_id}")
        self._logger.info(
            f"Sim-to-Real deploy requested by {ctx.user_id}, format: {format_type}",
            log_ctx,
        )

        # 1. 시뮬레이션 결과 검증 (Guard Clause)
        if not self._verify_simulation_result(package_id):
            self._logger.warn(
                f"Unverified or invalid scenario for package {package_id}", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="FMS scenario is unverified or missing required configurations.",
                status_code=400,
            )

        # 2. 도메인 엔티티 생성
        try:
            target_format = DeployPackageFormatEnum(format_type)
        except ValueError as ve:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message=f"Unsupported deploy format: {format_type}",
                status_code=400,
            ) from ve

        pkg = DeployPackage(
            package_id=package_id, format=target_format, vda5050_config=config
        )
        pkg.generate_hash()
        self._logger.info(
            f"Generated package integrity hash: {pkg.package_hash}", log_ctx
        )

        # 3. 어댑터 호출을 통한 파일 추출 및 I/O 예외 마스킹
        try:
            is_success = self._fleet_deploy_port.export_package(pkg)
            if is_success:
                self._logger.info("Successfully exported deploy package", log_ctx)
            return is_success

        except OSError as exc:
            # 원시 예외를 마스킹하여 500 내부 에러로 래핑
            log_ctx.exc = exc
            self._logger.error("I/O Error during package export", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
                message="Failed to write package to file system due to I/O or permission error.",
                status_code=500,
            ) from exc

    def _verify_simulation_result(self, package_id: str) -> bool:
        """
        시뮬레이션 가동을 통해 검증(물리 충돌 0건 등)을 통과했는지 확인합니다.
        (본 예제에서는 테스트를 위해 'invalid'가 포함된 경우 False 반환)
        """
        # TODO: 실제 검증 로직은 시뮬레이션 결과 DB 조회 및 검증 로직으로 대체 필요
        return "invalid" not in package_id.lower()
