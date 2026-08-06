/**
 * @brief 파이썬 서빙용 Pybind11 래퍼
 */
#include <memory>
#include <string>

#include "edge_command_facade.hpp"
#include "edge_query_facade.hpp"

namespace sftwin::edge_control::facades {

class EdgeFacadePybind {
   private:
    std::shared_ptr<EdgeCommandFacadeCPP> _command_facade;
    std::shared_ptr<EdgeQueryFacade> _query_facade;

   public:
    // Command와 Query 파사드를 분리하여 주입받음 (CQRS 패턴 고려)
    EdgeFacadePybind(std::shared_ptr<EdgeCommandFacadeCPP> command_facade,
                     std::shared_ptr<EdgeQueryFacade> query_facade)
        : _command_facade(std::move(command_facade)), _query_facade(std::move(query_facade)) {}

    void execute_failsafe_estop(const std::string& reason) {
        _command_facade->execute_failsafe_estop_native(reason.c_str());
    }

    bool resume_process(const std::string& command_script) {
        return _command_facade->resume_process_native(command_script);
    }

    std::string get_telemetry_status_serialized(const std::string& device_id) {
        auto proto = _query_facade->get_telemetry_status(device_id);
        std::string serialized_data;
        proto.SerializeToString(&serialized_data);
        return serialized_data;
    }
};

}  // namespace sftwin::edge_control::facades