from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.audit.audit_event_type_enum import AuditEventType
from shared.security.audit.audit_events import AuditEvent
from shared.security.audit.audit_severity_enum import AuditSeverity
from shared.security.audit.global_audit_logger import GlobalAuditLogger
from shared.security.context_guard import require_user_context
from simulation.contracts.dtos.deploy_package_dto import DeployPackageDto
from simulation.contracts.ports.outbound.i_fleet_deployment_gateway import (
    IFleetDeploymentGateway,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_request_dto import (
    DeploySim2RealRequestDto,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_result_dto import (
    DeploySim2RealResultDto,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package import (
    DeployPackage,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package_format_enum import (
    DeployPackageFormat,
)


class DeploySim2RealUseCase:
    """검증된 가상 시뮬레이션 환경을 실 설비(ROS2/VDA5050) 배포 패키지로 변환 및 전송하는 유스케이스"""

    def __init__(
        self,
        gateway: IFleetDeploymentGateway,
        system_logger: GlobalSystemLogger | None = None,
        audit_logger: GlobalAuditLogger | None = None,
    ) -> None:
        self._gateway = gateway
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="DeploySim2RealUseCase"
        )
        self._audit_logger = audit_logger or GlobalAuditLogger()

    @require_user_context
    def execute(
        self, request_dto: DeploySim2RealRequestDto, ctx: UserContext
    ) -> DeploySim2RealResultDto:
        config_dict: dict[str, Any] = (
            asdict(request_dto.config)
            if is_dataclass(request_dto.config)
            else (request_dto.config or {})
        )

        # 1. 도메인 포맷 검증 및 해시 생성
        try:
            target_format = DeployPackageFormat(request_dto.format_type)
            pkg = DeployPackage.create(
                package_id=request_dto.package_id,
                format_type=target_format,
                ros2_ws_path=request_dto.ros2_ws_path,
                vda5050_config=config_dict,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 2. Contracts DTO 변환 및 게이트웨이 전송
        gateway_dto = DeployPackageDto(
            package_id=pkg.package_id,
            format_type=pkg.format.value,
            ros2_ws_path=pkg.ros2_ws_path or "",
            package_hash=pkg.package_hash,
            config=pkg.vda5050_config,
        )

        try:
            self._gateway.deploy(gateway_dto)
        except OSError as exc:
            self._system_logger.error(
                f"I/O Error during package deployment for {pkg.package_id}: {str(exc)}",
                extra={
                    "package_id": pkg.package_id,
                    "company_id": ctx.company_id,
                },
            )
            # 배포 실패 감사 로그 기록
            self._audit_logger.log(
                AuditEvent(
                    event_type=AuditEventType.SECURITY,
                    action="DEPLOY_PACKAGE_FAILED",
                    target=f"DeployPackage:{pkg.package_id}",
                    severity=AuditSeverity.CRITICAL,
                    user_ctx=ctx,
                    details={"error": str(exc), "format": pkg.format.value},
                )
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message="Failed to deploy package due to storage/network I/O failure.",
            ) from exc

        # 3. 배포 성공 감사 로그 및 비즈니스 마일스톤 기록
        self._audit_logger.log(
            AuditEvent(
                event_type=AuditEventType.SECURITY,
                action="DEPLOY_PACKAGE_SUCCESS",
                target=f"DeployPackage:{pkg.package_id}",
                severity=AuditSeverity.INFO,
                user_ctx=ctx,
                details={"format": pkg.format.value, "package_hash": pkg.package_hash},
            )
        )

        self._system_logger.info(
            f"Successfully deployed package: {pkg.package_id} (hash: {pkg.package_hash[:8]})",
            extra={
                "package_id": pkg.package_id,
                "company_id": ctx.company_id,
                "format": pkg.format.value,
                "package_hash": pkg.package_hash,
            },
        )

        return DeploySim2RealResultDto(
            package_id=pkg.package_id,
            package_hash=pkg.package_hash,
            is_success=True,
            deployed_at=datetime.now(timezone.utc).isoformat(),
        )
