#include <gtest/gtest.h>
#include <memory>
#include <string>
#include <type_traits>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/domain/foxglove_frame_chunk.hpp"
#include "foxglove_bridge/domain/client_session_metadata.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

using namespace sftwin::plugins::foxglove_bridge;

// 시나리오 1: Enum 값 및 메모리 정렬(64바이트 캐시 라인) 검증 (Happy Path)
TEST(DomainModelsTest, VerifyEnumValuesAndMemoryAlignment) {
    // Given & When: 열거형 값 할당
    FoxgloveConnectionState conn_state = FoxgloveConnectionState::LISTENING;
    ChannelEncoding encoding = ChannelEncoding::CDR;
    WebClientCommandType cmd_type = WebClientCommandType::TRIGGER_ESTOP;
    BackpressurePolicy policy = BackpressurePolicy::DROP_OLDEST;

    // Then: Enum 타입 및 기본 값 매핑 검증
    EXPECT_EQ(conn_state, FoxgloveConnectionState::LISTENING);
    EXPECT_EQ(encoding, ChannelEncoding::CDR);
    EXPECT_EQ(cmd_type, WebClientCommandType::TRIGGER_ESTOP);
    EXPECT_EQ(policy, BackpressurePolicy::DROP_OLDEST);

    // Then: 64바이트 캐시 라인 정렬 제약 조건 검증
    EXPECT_EQ(alignof(FoxgloveBinaryFrameChunk), 64);
    EXPECT_EQ(alignof(ClientSessionMetadata), 64);

    // Frame Chunk 구조체 기본 할당 검증
    FoxgloveBinaryFrameChunk chunk{};
    chunk.channel_id = 1;
    chunk.timestamp_ns = 1000000000ULL;
    chunk.payload_size = 4;
    chunk.payload[0] = 0x01;
    EXPECT_EQ(chunk.channel_id, 1U);
    EXPECT_EQ(chunk.payload[0], 0x01);

    // Session Metadata 기본 상태 검증
    ClientSessionMetadata session{};
    session.client_id = 42;
    session.queued_bytes.store(1024);
    EXPECT_EQ(session.client_id, 42U);
    EXPECT_EQ(session.queued_bytes.load(), 1024ULL);
}

// Mock Endpoint 클래스를 통한 인터페이스 가상 테이블 검증
class MockFoxgloveBridgeEndpoint : public IFoxgloveBridgeEndpoint {
public:
    bool connected_called{false};
    bool disconnected_called{false};
    bool subscribed_called{false};
    std::string received_message{};
    std::string estop_reason{};

    void on_client_connected(ClientHandle) override {
        connected_called = true;
    }
    void on_client_disconnected(ClientHandle) override {
        disconnected_called = true;
    }
    void on_client_subscribed(ChannelId, ClientHandle) override {
        subscribed_called = true;
    }
    void handle_client_message(ClientHandle, const std::string& payload_json) override {
        received_message = payload_json;
    }
    void broadcast_emergency_stop(const std::string& trigger_reason) override {
        estop_reason = trigger_reason;
    }
};

// 시나리오 2: IFoxgloveBridgeEndpoint 인터페이스 가상 함수 호출 계약 검증 (Happy Path)
TEST(DomainModelsTest, VerifyBridgeEndpointInterfaceContract) {
    // Given: Mock 구현체를 가리키는 인터페이스 포인터
    std::unique_ptr<IFoxgloveBridgeEndpoint> endpoint = std::make_unique<MockFoxgloveBridgeEndpoint>();
    auto* mock_ptr = static_cast<MockFoxgloveBridgeEndpoint*>(endpoint.get());
    void* fake_client_handle = reinterpret_cast<void*>(0x1234);

    // When: 인터페이스 메서드 호출
    endpoint->on_client_connected(fake_client_handle);
    endpoint->on_client_subscribed(101, fake_client_handle);
    endpoint->handle_client_message(fake_client_handle, "{\"action\":\"TRIGGER_ESTOP\"}");
    endpoint->broadcast_emergency_stop("USER_REQUEST");
    endpoint->on_client_disconnected(fake_client_handle);

    // Then: 가상 메서드 디스패치 및 파라미터 전달 정합성 확인
    EXPECT_TRUE(mock_ptr->connected_called);
    EXPECT_TRUE(mock_ptr->subscribed_called);
    EXPECT_EQ(mock_ptr->received_message, "{\"action\":\"TRIGGER_ESTOP\"}");
    EXPECT_EQ(mock_ptr->estop_reason, "USER_REQUEST");
    EXPECT_TRUE(mock_ptr->disconnected_called);
}
