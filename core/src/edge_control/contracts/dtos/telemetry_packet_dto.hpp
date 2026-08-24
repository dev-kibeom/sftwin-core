#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace sftwin::edge_control {

class TelemetryPacketDto {
   public:
    TelemetryPacketDto() = default;

    TelemetryPacketDto(std::string device_id, uint64_t timestamp_ns,
                       std::vector<float> joint_positions = {},
                       std::vector<float> joint_torques = {})
        : _device_id(std::move(device_id)),
          _timestamp_ns(timestamp_ns),
          _joint_positions(std::move(joint_positions)),
          _joint_torques(std::move(joint_torques)) {}

    [[nodiscard]] const std::string& device_id() const noexcept { return _device_id; }
    [[nodiscard]] uint64_t timestamp_ns() const noexcept { return _timestamp_ns; }
    [[nodiscard]] const std::vector<float>& joint_positions() const noexcept { return _joint_positions; }
    [[nodiscard]] const std::vector<float>& joint_torques() const noexcept { return _joint_torques; }
    [[nodiscard]] bool is_warning() const noexcept { return _is_warning; }

    void set_warning(bool is_warning) noexcept { _is_warning = is_warning; }

   private:
    std::string _device_id;
    uint64_t _timestamp_ns{0};
    std::vector<float> _joint_positions;
    std::vector<float> _joint_torques;
    bool _is_warning{false};
};

}  // namespace sftwin::edge_control
