#include <gtest/gtest.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstdint>
#include <string>
#include <vector>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/server/foxglove_server_wrapper.hpp"

using namespace sftwin::plugins::foxglove_bridge;

class FoxgloveServerWrapperTest : public ::testing::Test {
protected:
    FoxgloveServerWrapper server;

    void TearDown() override {
        server.stop();
    }
};

// 시나리오 1: 서버 기동/종료 및 정상 포트 바인딩 검증 (Happy Path)
TEST_F(FoxgloveServerWrapperTest, StartAndStopServerSuccessfully) {
    // Given: 초기 정지 상태
    EXPECT_FALSE(server.is_running());

    // When: 포트 8765 및 바인드 주소 "0.0.0.0"으로 서버 기동
    bool started = server.start(8765, "0.0.0.0");

    // Then: 정상 기동 확인 및 바인딩된 포트 일치 확인
    EXPECT_TRUE(started);
    EXPECT_TRUE(server.is_running());
    EXPECT_EQ(server.bound_port(), 8765);

    // When: 서버 정지
    server.stop();

    // Then: 정지 상태 전이 확인
    EXPECT_FALSE(server.is_running());
}

// 시나리오 2: 포트 충돌 시 +1 순차 재시도(최대 3회) 및 대체 포트 바인딩 검증 (Edge Case)
TEST_F(FoxgloveServerWrapperTest, FallbackToNextPortOnBindingConflict) {
    // Given: 기본 포트(8765)를 임의의 더미 소켓으로 사전 점유
    int dummy_socket = socket(AF_INET, SOCK_STREAM, 0);
    ASSERT_GE(dummy_socket, 0);

    int opt = 1;
    setsockopt(dummy_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(8765);

    int bind_res = bind(dummy_socket, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    ASSERT_EQ(bind_res, 0);
    listen(dummy_socket, 1);

    // When: 점유된 8765 포트로 시작 시도 -> +1 재시도로 8766 바인딩 기대
    bool started = server.start(8765, "0.0.0.0");

    // Then: 8766 포트로 대체 바인딩 성공 확인
    EXPECT_TRUE(started);
    EXPECT_TRUE(server.is_running());
    EXPECT_EQ(server.bound_port(), 8766);

    // Clean up dummy socket
    close(dummy_socket);
}

// 시나리오 3: 바이너리 브로드캐스트 및 서비스 응답 인터페이스 호출 검증 (Happy Path)
TEST_F(FoxgloveServerWrapperTest, BroadcastMessageAndSendServiceResponse) {
    // Given: 서버 시작
    ASSERT_TRUE(server.start(8767, "0.0.0.0"));

    // When & Then: 데이터 브로드캐스트 및 서비스 응답 전송 시 크래시 없이 안전하게 실행됨
    std::vector<uint8_t> payload = {0x01, 0x02, 0x03, 0x04};
    EXPECT_NO_THROW({
        server.broadcast_message(101, payload.data(), payload.size());
    });

    EXPECT_NO_THROW({
        server.send_service_response(42, "{\"success\": true}");
    });
}
