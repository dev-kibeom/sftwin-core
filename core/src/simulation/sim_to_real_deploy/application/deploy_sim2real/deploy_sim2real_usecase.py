from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.ports.outbound.i_fleet_deploy import IFleetDeploy
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_dto import (
    DeploySim2RealRequestDto,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package import (
    DeployPackage,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package_format_enum import (
    DeployPackageFormat,
)


class DeploySim2RealUseCase:
    def __init__(
        self,
        fleet_deploy_port: IFleetDeploy,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._fleet_deploy_port = fleet_deploy_port
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="DeploySim2RealUseCase"
        )

    @require_user_context
    def execute(self, request_dto: DeploySim2RealRequestDto, ctx: UserContext) -> bool:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", f"TRC-DEPLOY-{request_dto.package_id}"),
            context={
                "user_id": ctx.user_id,
                "company_id": ctx.company_id,
                "package_id": request_dto.package_id,
                "format": request_dto.format_type,
            },
        )
        self._system_logger.info("Sim-to-Real deploy requested", log_ctx)

        # 1. 시뮬레이션 결과 검증 Guard Clause
        if not self._verify_simulation_result(request_dto.package_id):
            self._system_logger.warn(
                f"Unverified or invalid scenario for package {request_dto.package_id}",
                log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                message="FMS scenario is unverified or missing required configurations.",
                status_code=400,
            )

        # 2. 도메인 엔티티 생성
        try:
            target_format = DeployPackageFormat(request_dto.format_type)
            pkg = DeployPackage(
                package_id=request_dto.package_id,
                format=target_format,
                ros2_ws_path=request_dto.ros2_ws_path,
                vda5050_config=request_dto.config,
            )
        except ValueError as ve:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                message=str(ve),
                status_code=400,
            ) from ve

        # 3. 어댑터 호출 및 I/O 예외 마스킹
        try:
            is_success = self._fleet_deploy_port.export_package(pkg)
            if is_success:
                self._system_logger.info(
                    "Successfully exported deploy package", log_ctx
                )
            return is_success
        except OSError as exc:
            log_ctx.exc = exc
            self._system_logger.error("I/O Error during package export", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                message="Failed to write package to file system due to I/O or permission error.",
                status_code=500,
            ) from exc

    def _verify_simulation_result(self, package_id: str) -> bool:
        return "invalid" not in package_id.lower()
