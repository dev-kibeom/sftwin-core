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
                       std::vector<float> joint_torques = {},
                       float anomaly_score = 0.0f)
        : _device_id(std::move(device_id)),
          _timestamp_ns(timestamp_ns),
          _joint_positions(std::move(joint_positions)),
          _joint_torques(std::move(joint_torques)),
          _anomaly_score(anomaly_score) {}

    [[nodiscard]] const std::string& device_id() const noexcept { return _device_id; }
    [[nodiscard]] uint64_t timestamp_ns() const noexcept { return _timestamp_ns; }
    [[nodiscard]] const std::vector<float>& joint_positions() const noexcept { return _joint_positions; }
    [[nodiscard]] const std::vector<float>& joint_torques() const noexcept { return _joint_torques; }
    [[nodiscard]] float anomaly_score() const noexcept { return _anomaly_score; }
    [[nodiscard]] bool is_warning() const noexcept { return _is_warning; }

    void set_warning(bool is_warning) noexcept { _is_warning = is_warning; }
    void set_anomaly_score(float score) noexcept { _anomaly_score = score; }

   private:
    std::string _device_id;
    uint64_t _timestamp_ns{0};
    std::vector<float> _joint_positions;
    std::vector<float> _joint_torques;
    float _anomaly_score{0.0f};
    bool _is_warning{false};
};

}  // namespace sftwin::edge_control
