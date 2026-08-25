#include "evaluate_telemetry_failsafe_usecase.hpp"

#include <utility>

#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

EvaluateTelemetryFailsafeUseCase::EvaluateTelemetryFailsafeUseCase(
    std::shared_ptr<domain::InterlockManager> interlock_mgr,
    std::shared_ptr<IHardwareInterlock> hw_interlock,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    const domain::FailsafeRule& rule,
    std::shared_ptr<GlobalSystemLogger> system_logger)
    : _interlock_mgr(std::move(interlock_mgr)),
      _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)),
      _evaluator(rule),
      _system_logger(system_logger ? std::move(system_logger)
                                   : std::make_shared<GlobalSystemLogger>("EvaluateTelemetryFailsafeUseCase")) {}

void EvaluateTelemetryFailsafeUseCase::execute(const EvaluateTelemetryFailsafeRequestDto& request_dto) {
    // 1. 현재 인터록 상태 검증 (이미 정지 상태이면 조기 반환)
    if (_interlock_mgr->state() != domain::InterlockState::RELEASED) {
        return;
    }

    // 2. 도메인 스냅샷 조립
    const domain::TelemetrySnapshot snapshot{
        request_dto.telemetry.device_id(),
        request_dto.telemetry.timestamp_ns(),
        request_dto.telemetry.joint_torques(),
        _extract_min_distance(request_dto.vision_detections),
        request_dto.telemetry.anomaly_score()
    };

    // 3. 도메인 세이프티 정책 평가 실행
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    const auto result = _evaluator.evaluate_violations(snapshot, current_time_ns);

    // 4. 평가 결과에 따른 안전 조치 분기
    if (result.action == domain::FailsafeAction::ESTOP) {
        if (_hw_interlock) {
            _hw_interlock->trigger_physical_relay();
        }
        if (_failsafe_pub) {
            _failsafe_pub->publish(
                "failsafe/estop",
                FailsafeCommandDto(request_dto.telemetry.device_id(), "ESTOP", result.reason, current_time_ns)
            );
        }

        _interlock_mgr->engage_estop();
        _system_logger->error("Failsafe Auto E-STOP Triggered! Device: {}, Reason: {}",
                         request_dto.telemetry.device_id(), result.reason);

        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_EDGE_FAILSAFE_TRIGGERED,
            "Critical safety breach: " + result.reason
        );
    }

    if (result.action == domain::FailsafeAction::BYPASS) {
        _system_logger->warn("Bypass triggered due to warning intrusion. Device: {}, Reason: {}",
                        request_dto.telemetry.device_id(), result.reason);
    }
}

float EvaluateTelemetryFailsafeUseCase::_extract_min_distance(
    const std::vector<VisionDetectionDto>& detections) const noexcept {
    float min_dist = 999.0f;
    for (const auto& det : detections) {
        if (det.distance_m > 0.0f && det.distance_m < min_dist) {
            min_dist = det.distance_m;
        }
    }
    return min_dist;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
