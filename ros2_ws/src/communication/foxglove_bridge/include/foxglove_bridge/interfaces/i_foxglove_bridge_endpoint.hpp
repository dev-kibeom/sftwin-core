#pragma once

#include <cstdint>
#include <string>

namespace sftwin::plugins::foxglove_bridge {

using ClientHandle = void*;
using ChannelId = uint32_t;

class IFoxgloveBridgeEndpoint {
public:
    virtual ~IFoxgloveBridgeEndpoint() = default;

    virtual void on_client_connected(ClientHandle client_hdl) = 0;
    virtual void on_client_disconnected(ClientHandle client_hdl) = 0;
    virtual void on_client_subscribed(ChannelId channel_id, ClientHandle client_hdl) = 0;
    virtual void handle_client_message(ClientHandle client_hdl, const std::string& payload_json) = 0;
};

}  // namespace sftwin::plugins::foxglove_bridge
