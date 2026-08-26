#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>
#include <memory>
#include <string>

// 1. core 계층의 pure C++ Inbound Port 및 Contract DTO 참조
#include "core/src/edge_control/contracts/dtos/recovery_execution_result_dto.hpp"
#include "core/src/edge_control/contracts/ports/inbound/i_edge_query_facade.hpp"
#include "core/src/edge_control/contracts/ports/inbound/i_edge_command_facade.hpp"

// 2. 독립된 Protobuf 변환 플러그인 참조
#include "plugins/protobuf_codec/include/telemetry_protobuf_mapper.hpp"

namespace py = pybind11;
using namespace sftwin::edge_control;

namespace sftwin::plugins::pybind {

class EdgeFacadePybind {
   private:
    std::shared_ptr<IEdgeQueryFacade> _query_facade;
    std::shared_ptr<IEdgeCommandFacade> _command_facade;

   public:
    EdgeFacadePybind(
        std::shared_ptr<IEdgeQueryFacade> query_facade,
        std::shared_ptr<IEdgeCommandFacade> command_facade)
        : _query_facade(std::move(query_facade)), _command_facade(std::move(command_facade)) {}

    // E-Stop 수동 발동 (IEdgeCommandFacade::execute_manual_estop 매핑)
    void execute_manual_estop(const std::string& reason) {
        if (_command_facade) {
            _command_facade->execute_manual_estop(reason);
        }
    }

    // Behavior Tree / 복구 시퀀스 실행 (IEdgeCommandFacade::resume_recovery_sequence 매핑)
    bool resume_recovery_sequence(const std::string& sequence_script) {
        if (!_command_facade) return false;
        const auto result = _command_facade->resume_recovery_sequence(sequence_script);
        return result.is_success();
    }

    // 2단계 현장 안전 점검 승인 기반 E-Stop 인터록 해제 (IEdgeCommandFacade::reset_estop_interlock 매핑)
    bool reset_estop_interlock(bool is_field_inspected, bool is_manager_approved) {
        if (!_command_facade) return false;
        return _command_facade->reset_estop_interlock(is_field_inspected, is_manager_approved);
    }

    // 텔레메트리 최신 상태 조회 (Protobuf 직렬화 바이너리 형태로 Python에 반환)
    py::bytes get_telemetry_status_serialized(const std::string& device_id) {
        if (!_query_facade) return py::bytes("");

        // 1) core facade로부터 순수 C++ DTO 획득
        auto core_dto = _query_facade->get_telemetry_status(device_id);

        // 2) plugins/protobuf_codec 모듈을 통해 Protobuf 객체로 변환
        auto proto = protobuf_codec::TelemetryProtobufMapper::to_protobuf(core_dto);

        // 3) 직렬화 수행 후 Python py::bytes로 반환
        std::string serialized_data;
        proto.SerializeToString(&serialized_data);
        return py::bytes(serialized_data);
    }
};

}  // namespace sftwin::plugins::pybind


// ============================================================================
// Pybind11 Python 모듈 바인딩 매크로
// ============================================================================
PYBIND11_MODULE(edge_control_pybind, m) {
    m.doc() = "sftwin C++ Edge Control Engine Pybind11 Binding Plugin";

    py::class_<sftwin::plugins::pybind::EdgeFacadePybind>(m, "EdgeFacadePybind")
        .def(py::init<std::shared_ptr<IEdgeQueryFacade>, std::shared_ptr<IEdgeCommandFacade>>(),
             py::arg("query_facade"), py::arg("command_facade"))
        .def("execute_manual_estop", &sftwin::plugins::pybind::EdgeFacadePybind::execute_manual_estop,
             py::arg("reason"))
        .def("resume_recovery_sequence", &sftwin::plugins::pybind::EdgeFacadePybind::resume_recovery_sequence,
             py::arg("sequence_script"))
        .def("reset_estop_interlock", &sftwin::plugins::pybind::EdgeFacadePybind::reset_estop_interlock,
             py::arg("is_field_inspected"), py::arg("is_manager_approved"))
        .def("get_telemetry_status_serialized", &sftwin::plugins::pybind::EdgeFacadePybind::get_telemetry_status_serialized,
             py::arg("device_id"));
}
