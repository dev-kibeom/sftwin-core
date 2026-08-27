#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <atomic>
#include <functional>
#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

namespace sftwin::plugins::foxglove_bridge {

class FoxgloveServerWrapper {
public:
    FoxgloveServerWrapper();
    ~FoxgloveServerWrapper();

    FoxgloveServerWrapper(const FoxgloveServerWrapper&) = delete;
    FoxgloveServerWrapper& operator=(const FoxgloveServerWrapper&) = delete;

    bool start(uint16_t port = 8765, const std::string& address = "0.0.0.0");
    void stop();

    void broadcast_message(ChannelId channel_id, const uint8_t* data, size_t size);
    void send_service_response(uint32_t call_id, const std::string& response_data);

    [[nodiscard]] bool is_running() const noexcept;
    [[nodiscard]] uint16_t bound_port() const noexcept;
    [[nodiscard]] FoxgloveConnectionState state() const noexcept;

private:
    bool try_bind_and_listen(uint16_t port, const std::string& address);

    std::atomic<bool> _is_running{false};
    std::atomic<uint16_t> _bound_port{0};
    std::atomic<FoxgloveConnectionState> _state{FoxgloveConnectionState::DISCONNECTED};
    int _server_fd{-1};
};

}  // namespace sftwin::plugins::foxglove_bridge
