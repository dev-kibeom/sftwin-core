#include "foxglove_bridge/server/foxglove_server_wrapper.hpp"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>

namespace sftwin::plugins::foxglove_bridge {

FoxgloveServerWrapper::FoxgloveServerWrapper() = default;

FoxgloveServerWrapper::~FoxgloveServerWrapper() {
    stop();
}

bool FoxgloveServerWrapper::try_bind_and_listen(uint16_t port, const std::string& address) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return false;
    }

    int opt = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        close(fd);
        return false;
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, address.c_str(), &addr.sin_addr) <= 0) {
        addr.sin_addr.s_addr = INADDR_ANY;
    }

    if (bind(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0) {
        close(fd);
        return false;
    }

    if (listen(fd, 16) < 0) {
        close(fd);
        return false;
    }

    _server_fd = fd;
    _bound_port.store(port);
    return true;
}

bool FoxgloveServerWrapper::start(uint16_t port, const std::string& address) {
    if (_is_running.load()) {
        return true;
    }

    constexpr int max_retries = 3;
    uint16_t current_port = port;
    bool bound = false;

    for (int i = 0; i < max_retries; ++i) {
        if (try_bind_and_listen(current_port, address)) {
            bound = true;
            break;
        }
        current_port++;
    }

    if (!bound) {
        _state.store(FoxgloveConnectionState::DISCONNECTED);
        return false;
    }

    _is_running.store(true);
    _state.store(FoxgloveConnectionState::LISTENING);
    return true;
}

void FoxgloveServerWrapper::stop() {
    if (!_is_running.exchange(false)) {
        return;
    }

    _state.store(FoxgloveConnectionState::SHUTTING_DOWN);

    if (_server_fd >= 0) {
        close(_server_fd);
        _server_fd = -1;
    }

    _bound_port.store(0);
    _state.store(FoxgloveConnectionState::DISCONNECTED);
}

void FoxgloveServerWrapper::broadcast_message(ChannelId, const uint8_t*, size_t) {
    if (!_is_running.load()) {
        return;
    }
}

void FoxgloveServerWrapper::send_service_response(uint32_t, const std::string&) {
    if (!_is_running.load()) {
        return;
    }
}

bool FoxgloveServerWrapper::is_running() const noexcept {
    return _is_running.load();
}

uint16_t FoxgloveServerWrapper::bound_port() const noexcept {
    return _bound_port.load();
}

FoxgloveConnectionState FoxgloveServerWrapper::state() const noexcept {
    return _state.load();
}

}  // namespace sftwin::plugins::foxglove_bridge
