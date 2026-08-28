#include "foxglove_bridge/server/foxglove_server_wrapper.hpp"
#include <iostream>
#include <asio/ip/tcp.hpp>

namespace sftwin::plugins::foxglove_bridge {

FoxgloveServerWrapper::FoxgloveServerWrapper() {
    _ws_server.clear_access_channels(websocketpp::log::alevel::all);
    _ws_server.set_access_channels(websocketpp::log::alevel::connect | websocketpp::log::alevel::disconnect);
    _ws_server.clear_error_channels(websocketpp::log::elevel::all);
    _ws_server.set_error_channels(websocketpp::log::elevel::rerror | websocketpp::log::elevel::fatal);

    _ws_server.init_asio();
    _ws_server.set_reuse_addr(true);

    _ws_server.set_open_handler([this](ConnectionHdl hdl) { on_open(hdl); });
    _ws_server.set_close_handler([this](ConnectionHdl hdl) { on_close(hdl); });
    _ws_server.set_message_handler([this](ConnectionHdl hdl, WsServer::message_ptr msg) {
        on_message(hdl, msg);
    });
}

FoxgloveServerWrapper::~FoxgloveServerWrapper() {
    stop();
}

void FoxgloveServerWrapper::set_endpoint_handler(IFoxgloveBridgeEndpoint* endpoint_handler) {
    _endpoint_handler = endpoint_handler;
}

bool FoxgloveServerWrapper::start(uint16_t port, const std::string& address) {
    if (_is_running.load()) {
        return true;
    }

    websocketpp::lib::error_code ec;
    asio::ip::tcp::endpoint endpoint;

    if (address == "0.0.0.0" || address.empty()) {
        endpoint = asio::ip::tcp::endpoint(asio::ip::tcp::v4(), port);
    } else {
        endpoint = asio::ip::tcp::endpoint(asio::ip::make_address(address, ec), port);
        if (ec) {
            return false;
        }
    }

    _ws_server.listen(endpoint, ec);
    if (ec) {
        return false;
    }

    _ws_server.start_accept(ec);
    if (ec) {
        return false;
    }

    _bound_port.store(port);
    _is_running.store(true);
    _state.store(FoxgloveConnectionState::LISTENING);

    _server_thread = std::make_unique<std::thread>([this]() {
        _ws_server.run();
    });

    return true;
}

void FoxgloveServerWrapper::stop() {
    if (!_is_running.exchange(false)) {
        return;
    }

    _state.store(FoxgloveConnectionState::SHUTTING_DOWN);

    websocketpp::lib::error_code ec;
    _ws_server.stop_listening(ec);

    {
        std::lock_guard<std::mutex> lock(_connections_mutex);
        for (const auto& hdl : _active_connections) {
            _ws_server.close(hdl, websocketpp::close::status::normal, "Server Shutdown", ec);
        }
        _active_connections.clear();
    }

    _ws_server.stop();

    if (_server_thread && _server_thread->joinable()) {
        _server_thread->join();
    }

    _bound_port.store(0);
    _state.store(FoxgloveConnectionState::DISCONNECTED);
}

void FoxgloveServerWrapper::on_open(ConnectionHdl hdl) {
    {
        std::lock_guard<std::mutex> lock(_connections_mutex);
        _active_connections.insert(hdl);
    }
    _state.store(FoxgloveConnectionState::CLIENT_CONNECTED);

    if (_endpoint_handler) {
        if (auto locked = hdl.lock()) {
            _endpoint_handler->on_client_connected(locked.get());
        }
    }
}

void FoxgloveServerWrapper::on_close(ConnectionHdl hdl) {
    void* client_raw_ptr = nullptr;
    if (auto locked = hdl.lock()) {
        client_raw_ptr = locked.get();
    }

    {
        std::lock_guard<std::mutex> lock(_connections_mutex);
        _active_connections.erase(hdl);
        if (_active_connections.empty()) {
            _state.store(FoxgloveConnectionState::LISTENING);
        }
    }

    if (_endpoint_handler && client_raw_ptr) {
        _endpoint_handler->on_client_disconnected(client_raw_ptr);
    }
}

void FoxgloveServerWrapper::on_message(ConnectionHdl hdl, WsServer::message_ptr msg) {
    if (!_endpoint_handler) return;

    if (msg->get_opcode() == websocketpp::frame::opcode::text) {
        if (auto locked = hdl.lock()) {
            _endpoint_handler->handle_client_message(locked.get(), msg->get_payload());
        }
    }
}

void FoxgloveServerWrapper::broadcast_binary(const uint8_t* data, size_t size) {
    if (!_is_running.load() || size == 0) return;

    std::lock_guard<std::mutex> lock(_connections_mutex);
    for (const auto& hdl : _active_connections) {
        websocketpp::lib::error_code ec;
        _ws_server.send(hdl, data, size, websocketpp::frame::opcode::binary, ec);
    }
}

void FoxgloveServerWrapper::send_text(ClientHandle client_hdl, const std::string& text_payload) {
    if (!_is_running.load() || !client_hdl) return;

    std::lock_guard<std::mutex> lock(_connections_mutex);
    for (const auto& hdl : _active_connections) {
        if (auto locked = hdl.lock()) {
            if (locked.get() == client_hdl) {
                websocketpp::lib::error_code ec;
                _ws_server.send(hdl, text_payload, websocketpp::frame::opcode::text, ec);
                break;
            }
        }
    }
}

void FoxgloveServerWrapper::broadcast_text(const std::string& text_payload) {
    if (!_is_running.load()) return;

    std::lock_guard<std::mutex> lock(_connections_mutex);
    for (const auto& hdl : _active_connections) {
        websocketpp::lib::error_code ec;
        _ws_server.send(hdl, text_payload, websocketpp::frame::opcode::text, ec);
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
