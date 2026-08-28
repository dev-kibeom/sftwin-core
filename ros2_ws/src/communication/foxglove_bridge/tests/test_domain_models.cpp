#include <gtest/gtest.h>
#include <memory>
#include <string>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/domain/foxglove_frame_chunk.hpp"
#include "foxglove_bridge/domain/client_session_metadata.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

using namespace sftwin::plugins::foxglove_bridge;

TEST(DomainModelsTest, VerifyEnumValuesAndMemoryAlignment) {
    FoxgloveConnectionState conn_state = FoxgloveConnectionState::LISTENING;
    ChannelEncoding encoding = ChannelEncoding::CDR;
    WebClientCommandType cmd_type = WebClientCommandType::TRIGGER_ESTOP;
    BackpressurePolicy policy = BackpressurePolicy::DROP_OLDEST;

    EXPECT_EQ(conn_state, FoxgloveConnectionState::LISTENING);
    EXPECT_EQ(encoding, ChannelEncoding::CDR);
    EXPECT_EQ(cmd_type, WebClientCommandType::TRIGGER_ESTOP);
    EXPECT_EQ(policy, BackpressurePolicy::DROP_OLDEST);

    EXPECT_EQ(alignof(FoxgloveBinaryFrameChunk), 64);
    EXPECT_EQ(alignof(ClientSessionMetadata), 64);

    FoxgloveBinaryFrameChunk chunk{};
    chunk.channel_id = 1;
    chunk.timestamp_ns = 1000000000ULL;
    chunk.payload_size = 4;
    chunk.payload[0] = 0x01;
    EXPECT_EQ(chunk.channel_id, 1U);
    EXPECT_EQ(chunk.payload[0], 0x01);

    ClientSessionMetadata session{};
    session.client_id = 42;
    session.queued_bytes.store(1024);
    EXPECT_EQ(session.client_id, 42U);
    EXPECT_EQ(session.queued_bytes.load(), 1024ULL);
}

class MockFoxgloveBridgeEndpoint : public IFoxgloveBridgeEndpoint {
public:
    bool connected_called{false};
    bool disconnected_called{false};
    bool subscribed_called{false};
    ChannelId subscribed_channel_id{0};
    std::string received_message{};

    void on_client_connected(ClientHandle) override {
        connected_called = true;
    }
    void on_client_disconnected(ClientHandle) override {
        disconnected_called = true;
    }
    void on_client_subscribed(ChannelId channel_id, ClientHandle) override {
        subscribed_called = true;
        subscribed_channel_id = channel_id;
    }
    void handle_client_message(ClientHandle, const std::string& payload_json) override {
        received_message = payload_json;
    }
};

TEST(DomainModelsTest, VerifyBridgeEndpointInterfaceContract) {
    std::unique_ptr<IFoxgloveBridgeEndpoint> endpoint = std::make_unique<MockFoxgloveBridgeEndpoint>();
    auto* mock_ptr = static_cast<MockFoxgloveBridgeEndpoint*>(endpoint.get());
    void* fake_client_handle = reinterpret_cast<void*>(0x1234);

    endpoint->on_client_connected(fake_client_handle);
    endpoint->on_client_subscribed(101, fake_client_handle);
    endpoint->handle_client_message(fake_client_handle, "{\"op\":\"subscribe\"}");
    endpoint->on_client_disconnected(fake_client_handle);

    EXPECT_TRUE(mock_ptr->connected_called);
    EXPECT_TRUE(mock_ptr->subscribed_called);
    EXPECT_EQ(mock_ptr->subscribed_channel_id, 101U);
    EXPECT_EQ(mock_ptr->received_message, "{\"op\":\"subscribe\"}");
    EXPECT_TRUE(mock_ptr->disconnected_called);
}
