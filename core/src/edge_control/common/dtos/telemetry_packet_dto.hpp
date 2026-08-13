#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace sftwin::edge_control::common::dtos {

/**
 * @brief 로봇 및 설비 실시간 제어 상태 DTO
 */
class TelemetryPacketDto {
   private:
    std::string _device_id;
    uint64_t _timestamp_ns{0};
    std::vector<float> _joint_positions;
    std::vector<float> _joint_torques;
    bool _is_warning{false};

   public:
    TelemetryPacketDto() = default;

    TelemetryPacketDto(std::string device_id,
                       uint64_t timestamp_ns,
                       std::vector<float> joint_positions = {},
                       std::vector<float> joint_torques = {})
        : _device_id(std::move(device_id)),
          _timestamp_ns(timestamp_ns),
          _joint_positions(std::move(joint_positions)),
          _joint_torques(std::move(joint_torques)) {}

    [[nodiscard]] const std::string& device_id() const { return _device_id; }
    [[nodiscard]] uint64_t timestamp_ns() const { return _timestamp_ns; }
    [[nodiscard]] const std::vector<float>& joint_positions() const { return _joint_positions; }
    [[nodiscard]] const std::vector<float>& joint_torques() const { return _joint_torques; }
    [[nodiscard]] bool is_warning() const { return _is_warning; }

    void set_warning(bool is_warning) { _is_warning = is_warning; }
};

}  // namespace sftwin::edge_control::common::dtos
