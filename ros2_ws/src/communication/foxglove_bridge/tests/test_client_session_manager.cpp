#include <gtest/gtest.h>
#include <thread>
#include <vector>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/managers/client_session_manager.hpp"

using namespace sftwin::plugins::foxglove_bridge;

class ClientSessionManagerTest : public ::testing::Test {
protected:
    ClientSessionManager session_manager;
    void* fake_client_1{reinterpret_cast<void*>(0x1001)};
    void* fake_client_2{reinterpret_cast<void*>(0x1002)};
};

// 시나리오 1: 클라이언트 세션 등록/해제 및 정상 버퍼 범위 내 백프레셔 검증 (Happy Path)
TEST_F(ClientSessionManagerTest, AddClientAndCheckNormalBackpressure) {
    // Given: 클라이언트 등록
    session_manager.add_client(fake_client_1);
    EXPECT_EQ(session_manager.active_client_count(), 1U);

    // When: 허용 버퍼 한도(10MB) 이내의 바이트 적재 및 백프레셔 검사
    session_manager.update_queued_bytes(fake_client_1, 1024 * 1024); // 1MB
    bool is_healthy = session_manager.check_backpressure(fake_client_1, 10 * 1024 * 1024);

    // Then: 정상 수용 가능(true) 및 드롭 카운트 0 확인
    EXPECT_TRUE(is_healthy);
    EXPECT_EQ(session_manager.get_dropped_frames_count(fake_client_1), 0U);

    // When: 클라이언트 세션 제거
    session_manager.remove_client(fake_client_1);

    // Then: 세션 풀에서 정상 제거 확인
    EXPECT_EQ(session_manager.active_client_count(), 0U);
}

// 시나리오 2: 버퍼 한도 초과 시 백프레셔 감지 및 DROP_OLDEST 카운트 증가 검증 (Edge Case)
TEST_F(ClientSessionManagerTest, TriggerBackpressureOnBufferOverflow) {
    // Given: 클라이언트 등록 및 10MB 초과 바이트 적재
    session_manager.add_client(fake_client_2);
    size_t max_limit = 10 * 1024 * 1024; // 10MB
    session_manager.update_queued_bytes(fake_client_2, max_limit + 1024);

    // When: 백프레셔 검사 수행
    bool is_healthy = session_manager.check_backpressure(fake_client_2, max_limit);

    // Then: 오버플로우 감지(false) 및 드롭된 프레임 수 증가 확인
    EXPECT_FALSE(is_healthy);
    EXPECT_EQ(session_manager.get_dropped_frames_count(fake_client_2), 1U);
}

// 시나리오 3: 미등록 클라이언트 조회 방어 및 멀티스레드 동시성 안전성 검증 (Edge Case)
TEST_F(ClientSessionManagerTest, ThreadSafetyAndUnregisteredClientHandling) {
    void* unregistered_client = reinterpret_cast<void*>(0x9999);

    // Given & When & Then: 미등록 클라이언트 조회 시 안전하게 false 반환
    EXPECT_FALSE(session_manager.check_backpressure(unregistered_client, 1024));
    EXPECT_NO_THROW(session_manager.remove_client(unregistered_client));

    // When: 다중 스레드에서 세션 동시 추가 및 삭제
    constexpr int thread_count = 8;
    std::vector<std::thread> workers;
    workers.reserve(thread_count);

    for (int i = 0; i < thread_count; ++i) {
        workers.emplace_back([this, i]() {
            void* hdl = reinterpret_cast<void*>(static_cast<uintptr_t>(0x2000 + i));
            session_manager.add_client(hdl);
            session_manager.update_queued_bytes(hdl, 2048);
            session_manager.check_backpressure(hdl, 10485760);
            session_manager.remove_client(hdl);
        });
    }

    for (auto& t : workers) {
        t.join();
    }

    // Then: 레이스 컨디션 없이 최종 활성 클라이언트 수 0 확인
    EXPECT_EQ(session_manager.active_client_count(), 0U);
}
