#include "foxglove_bridge/managers/client_session_manager.hpp"
#include <chrono>

namespace sftwin::plugins::foxglove_bridge {

void ClientSessionManager::add_client(ClientHandle client_hdl) {
    if (client_hdl == nullptr) {
        return;
    }

    std::unique_lock<std::shared_mutex> lock(_session_mutex);
    auto metadata = std::make_shared<ClientSessionMetadata>();
    metadata->client_id = _next_client_id++;

    auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();

    metadata->connected_time_ns = static_cast<uint64_t>(now_ns);
    metadata->last_ack_time_ns = static_cast<uint64_t>(now_ns);
    metadata->queued_bytes.store(0);
    metadata->dropped_frames_count.store(0);
    metadata->is_throttled = false;

    _client_sessions[client_hdl] = metadata;
}

void ClientSessionManager::remove_client(ClientHandle client_hdl) {
    if (client_hdl == nullptr) {
        return;
    }

    std::unique_lock<std::shared_mutex> lock(_session_mutex);
    _client_sessions.erase(client_hdl);
}

void ClientSessionManager::update_queued_bytes(ClientHandle client_hdl, size_t bytes) {
    std::shared_lock<std::shared_mutex> lock(_session_mutex);
    auto it = _client_sessions.find(client_hdl);
    if (it != _client_sessions.end() && it->second != nullptr) {
        it->second->queued_bytes.store(bytes);
    }
}

bool ClientSessionManager::check_backpressure(ClientHandle client_hdl, size_t max_queue_bytes) {
    std::shared_lock<std::shared_mutex> lock(_session_mutex);
    auto it = _client_sessions.find(client_hdl);
    if (it == _client_sessions.end() || it->second == nullptr) {
        return false;
    }

    if (it->second->queued_bytes.load() > max_queue_bytes) {
        it->second->dropped_frames_count.fetch_add(1, std::memory_order_relaxed);
        it->second->is_throttled = true;
        return false;
    }

    it->second->is_throttled = false;
    return true;
}

size_t ClientSessionManager::active_client_count() const {
    std::shared_lock<std::shared_mutex> lock(_session_mutex);
    return _client_sessions.size();
}

uint32_t ClientSessionManager::get_dropped_frames_count(ClientHandle client_hdl) const {
    std::shared_lock<std::shared_mutex> lock(_session_mutex);
    auto it = _client_sessions.find(client_hdl);
    if (it != _client_sessions.end() && it->second != nullptr) {
        return it->second->dropped_frames_count.load();
    }
    return 0;
}

}  // namespace sftwin::plugins::foxglove_bridge
