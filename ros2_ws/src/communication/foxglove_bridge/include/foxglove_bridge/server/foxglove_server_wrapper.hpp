#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <atomic>
#include <thread>
#include <unordered_set>
#include <mutex>
#include <set>

#define ASIO_STANDALONE
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

namespace sftwin::plugins::foxglove_bridge {

using WsServer = websocketpp::server<websocketpp::config::asio>;
using ConnectionHdl = websocketpp::connection_hdl;

class FoxgloveServerWrapper {
public:
    FoxgloveServerWrapper();
    ~FoxgloveServerWrapper();

    FoxgloveServerWrapper(const FoxgloveServerWrapper&) = delete;
    FoxgloveServerWrapper& operator=(const FoxgloveServerWrapper&) = delete;

    // 엔드포인트 이벤트 인터페이스 등록
    void set_endpoint_handler(IFoxgloveBridgeEndpoint* endpoint_handler);

    bool start(uint16_t port = 8765, const std::string& address = "0.0.0.0");
    void stop();

    // 바이너리 데이터 브로드캐스트 (CDR 페이로드 송신용)
    void broadcast_binary(const uint8_t* data, size_t size);

    // 개별 클라이언트 텍스트 송신 (핸드셰이크/광고 JSON용)
    void send_text(ClientHandle client_hdl, const std::string& text_payload);
    void broadcast_text(const std::string& text_payload);

    [[nodiscard]] bool is_running() const noexcept;
    [[nodiscard]] uint16_t bound_port() const noexcept;
    [[nodiscard]] FoxgloveConnectionState state() const noexcept;

private:
    void on_open(ConnectionHdl hdl);
    void on_close(ConnectionHdl hdl);
    void on_message(ConnectionHdl hdl, WsServer::message_ptr msg);

    WsServer _ws_server;
    std::unique_ptr<std::thread> _server_thread;

    std::mutex _connections_mutex;
    std::set<ConnectionHdl, std::owner_less<ConnectionHdl>> _active_connections;

    IFoxgloveBridgeEndpoint* _endpoint_handler{nullptr};

    std::atomic<bool> _is_running{false};
    std::atomic<uint16_t> _bound_port{0};
    std::atomic<FoxgloveConnectionState> _state{FoxgloveConnectionState::DISCONNECTED};
};

}  // namespace sftwin::plugins::foxglove_bridge
