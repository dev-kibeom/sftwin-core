#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace sftwin::edge_control {

struct IceServerConfig {
    std::string urls{"stun:stun.l.google.com:19302"};
    std::string username;
    std::string credential;
};

class WebRtcSessionDto {
   public:
    WebRtcSessionDto() = default;

    WebRtcSessionDto(std::string device_id, std::string stream_type,
                     std::string signaling_url, std::string session_id,
                     bool is_active = true, uint64_t created_at_ns = 0)
        : _device_id(std::move(device_id)),
          _stream_type(std::move(stream_type)),
          _signaling_server_url(std::move(signaling_url)),
          _session_id(std::move(session_id)),
          _is_active(is_active),
          _created_at_ns(created_at_ns) {}

    [[nodiscard]] const std::string& device_id() const noexcept { return _device_id; }
    [[nodiscard]] const std::string& stream_type() const noexcept { return _stream_type; }
    [[nodiscard]] const std::string& signaling_server_url() const noexcept { return _signaling_server_url; }
    [[nodiscard]] const std::string& session_id() const noexcept { return _session_id; }
    [[nodiscard]] bool is_active() const noexcept { return _is_active; }
    [[nodiscard]] uint64_t created_at_ns() const noexcept { return _created_at_ns; }

   private:
    std::string _device_id;
    std::string _stream_type;           // "ROBOT_POV", "AMR_TOP_DOWN", "CCTV_CELL"
    std::string _signaling_server_url;  // ws://localhost:8080/webrtc/{device_id}
    std::string _session_id;
    bool _is_active{true};
    uint64_t _created_at_ns{0};
};

class DeviceStreamSummaryDto {
   public:
    DeviceStreamSummaryDto() = default;

    explicit DeviceStreamSummaryDto(std::vector<WebRtcSessionDto> streams)
        : _active_streams(std::move(streams)) {}

    [[nodiscard]] const std::vector<WebRtcSessionDto>& active_streams() const noexcept {
        return _active_streams;
    }

   private:
    std::vector<WebRtcSessionDto> _active_streams;
};

}  // namespace sftwin::edge_control
