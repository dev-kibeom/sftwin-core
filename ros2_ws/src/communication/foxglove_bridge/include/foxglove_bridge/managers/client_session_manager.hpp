#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <unordered_map>

#include "foxglove_bridge/domain/client_session_metadata.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

namespace sftwin::plugins::foxglove_bridge {

class ClientSessionManager {
public:
    ClientSessionManager() = default;
    ~ClientSessionManager() = default;

    ClientSessionManager(const ClientSessionManager&) = delete;
    ClientSessionManager& operator=(const ClientSessionManager&) = delete;

    void add_client(ClientHandle client_hdl);
    void remove_client(ClientHandle client_hdl);
    void update_queued_bytes(ClientHandle client_hdl, size_t bytes);
    bool check_backpressure(ClientHandle client_hdl, size_t max_queue_bytes);

    [[nodiscard]] size_t active_client_count() const;
    [[nodiscard]] uint32_t get_dropped_frames_count(ClientHandle client_hdl) const;

private:
    mutable std::shared_mutex _session_mutex;
    std::unordered_map<ClientHandle, std::shared_ptr<ClientSessionMetadata>> _client_sessions;
    uint64_t _next_client_id{1};
};

}  // namespace sftwin::plugins::foxglove_bridge
