/**
 * @brief 파이썬 서빙용 Pybind11 래퍼 (2단계 안전 해제 연동 확장)
 */
#include <memory>
#include <string>

#include "edge_command_facade.hpp"
#include "edge_query_facade.hpp"
#include "src/edge_control/anomaly_failsafe/application/reset_estop_interlock/reset_estop_interlock_usecase.hpp"

namespace sftwin::edge_control::facades {

class EdgeFacadePybind {
   private:
    std::shared_ptr<EdgeCommandFacadeCPP> _command_facade;
    std::shared_ptr<EdgeQueryFacade> _query_facade;
    std::shared_ptr<anomaly_failsafe::application::ResetEstopInterlockUseCase> _reset_usecase;

   public:
    EdgeFacadePybind(std::shared_ptr<EdgeCommandFacadeCPP> command_facade,
                     std::shared_ptr<EdgeQueryFacade> query_facade,
                     std::shared_ptr<anomaly_failsafe::application::ResetEstopInterlockUseCase>
                         reset_usecase = nullptr)
        : _command_facade(std::move(command_facade)),
          _query_facade(std::move(query_facade)),
          _reset_usecase(std::move(reset_usecase)) {}

    void execute_failsafe_estop(const std::string& reason) {
        _command_facade->execute_failsafe_estop_native(reason.c_str());
    }

    bool resume_process(const std::string& command_script) {
        return _command_facade->resume_process_native(command_script);
    }

    // 2단계 안전 점검 승인 기반 E-Stop 인터록 해제 바인딩 메서드
    bool reset_estop_2step(bool is_field_inspected, bool is_manager_approved) {
        if (!_reset_usecase) return false;
        // INTERLOCK_ENGAGED 상태 가정 하에 해제 실행
        auto new_state =
            _reset_usecase->execute(anomaly_failsafe::domain::EdgeEngineState::INTERLOCK_ENGAGED,
                                    is_field_inspected, is_manager_approved);
        return (new_state == anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);
    }

    std::string get_telemetry_status_serialized(const std::string& device_id) {
        auto proto = _query_facade->get_telemetry_status(device_id);
        std::string serialized_data;
        proto.SerializeToString(&serialized_data);
        return serialized_data;
    }
};

}  // namespace sftwin::edge_control::facades
