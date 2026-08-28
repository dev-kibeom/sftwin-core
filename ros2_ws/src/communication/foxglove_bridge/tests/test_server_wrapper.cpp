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

TEST_F(FoxgloveServerWrapperTest, StartAndStopServerSuccessfully) {
    EXPECT_FALSE(server.is_running());
    EXPECT_EQ(server.state(), FoxgloveConnectionState::DISCONNECTED);

    bool started = server.start(18765, "127.0.0.1");

    EXPECT_TRUE(started);
    EXPECT_TRUE(server.is_running());
    EXPECT_EQ(server.bound_port(), 18765);
    EXPECT_EQ(server.state(), FoxgloveConnectionState::LISTENING);

    server.stop();

    EXPECT_FALSE(server.is_running());
    EXPECT_EQ(server.state(), FoxgloveConnectionState::DISCONNECTED);
}

TEST_F(FoxgloveServerWrapperTest, RejectStartWhenPortAlreadyBound) {
    // 18766 포트를 사전 점유
    int dummy_socket = socket(AF_INET, SOCK_STREAM, 0);
    ASSERT_GE(dummy_socket, 0);

    int opt = 1;
    setsockopt(dummy_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(18766);

    int bind_res = bind(dummy_socket, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    ASSERT_EQ(bind_res, 0);
    listen(dummy_socket, 1);

    // 충돌 포트로 바인드 시도시 안전하게 false 리턴 확인
    bool started = server.start(18766, "127.0.0.1");
    EXPECT_FALSE(started);
    EXPECT_FALSE(server.is_running());
    EXPECT_EQ(server.state(), FoxgloveConnectionState::DISCONNECTED);

    close(dummy_socket);
}

TEST_F(FoxgloveServerWrapperTest, BroadcastBinaryAndTextSmokeTest) {
    bool started = server.start(18767, "127.0.0.1");
    ASSERT_TRUE(started);

    std::vector<uint8_t> payload = {0x01, 0x02, 0x03, 0x04};
    EXPECT_NO_THROW(server.broadcast_binary(payload.data(), payload.size()));
    EXPECT_NO_THROW(server.broadcast_text("{\"op\":\"serverInfo\"}"));

    server.stop();
}
