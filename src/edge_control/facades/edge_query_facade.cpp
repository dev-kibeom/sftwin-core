#include <memory>

#include "src/edge_control/realtime_telemetry/application/process_telemetry_usecase.hpp"
#include "telemetry_packet.pb.h"

namespace sftwin::edge_control::facades {

class EdgeQueryFacade {
   private:
    std::shared_ptr<application::ProcessTelemetryUseCase> _telemetry_uc;

   public:
    explicit EdgeQueryFacade(std::shared_ptr<application::ProcessTelemetryUseCase> telemetry_uc)
        : _telemetry_uc(std::move(telemetry_uc)) {}

    sftwin::telemetry::TelemetryPacketProto get_telemetry_status(const std::string& device_id) {
        // 내부 유즈케이스로 하향 위임 (Delegation)
        // (Python pybind11 바인딩 계층에서 예외 포획 및 GlobalResponseDto 변환을 수행함)
        return _telemetry_uc->get_latest_telemetry(device_id).get_proto();
    }
};

}  // namespace sftwin::edge_control::facades