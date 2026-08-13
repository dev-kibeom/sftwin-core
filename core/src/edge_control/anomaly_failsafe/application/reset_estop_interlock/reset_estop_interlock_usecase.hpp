#pragma once
#include <memory>
#include <string>
#include <string_view>

#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"
#include "src/edge_control/anomaly_failsafe/domain/estop_reset_policy.hpp"
#include "src/edge_control/anomaly_failsafe/ports/outbound/i_failsafe_publisher.hpp"
#include "src/edge_control/anomaly_failsafe/ports/outbound/i_hardware_interlock.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class ResetEstopInterlockUseCase {
public:
    ResetEstopInterlockUseCase(std::string device_id,
                                domain::EstopResetPolicy policy,
                                std::shared_ptr<ports::IFailsafePublisher> failsafe_pub)
        : _edge_device_id(std::move(device_id)),
          _policy(std::move(policy)),
          _failsafe_pub(std::move(failsafe_pub)) {}

    /**
     * @brief E-Stop 2단계 리셋을 실행하고 변경된 엔진 상태를 반환합니다.
     * @note C++17 [[nodiscard]]: 반환값을 무시할 경우 컴파일 경고를 발생시킵니다.
     */
    [[nodiscard]] domain::EdgeEngineState execute(domain::EdgeEngineState current_state,
                                                   bool is_field_inspected,
                                                   bool is_manager_approved);

private:
    std::string _edge_device_id;
    domain::EstopResetPolicy _policy;
    std::shared_ptr<ports::IFailsafePublisher> _failsafe_pub;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
