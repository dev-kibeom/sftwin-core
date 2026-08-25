#include <gtest/gtest.h>
#include "edge_control/realtime_telemetry/domain/telemetry_stream.hpp"

using namespace sftwin::edge_control::realtime_telemetry::domain;

TEST(TelemetryStreamTest, IsNotStaleWithinTimeoutLimit) {
    const uint64_t packet_time_ns = 1'000'000'000ULL;
    const uint64_t current_time_ns = packet_time_ns + 50'000'000ULL; // 50ms 경과

    TelemetryStream stream{"ROBOT_01", packet_time_ns};
    EXPECT_FALSE(stream.is_stale(current_time_ns));
}

TEST(TelemetryStreamTest, IsStaleWhenHeartbeatExceeds100ms) {
    const uint64_t packet_time_ns = 1'000'000'000ULL;
    const uint64_t current_time_ns = packet_time_ns + 150'000'000ULL; // 150ms 경과 (>100ms)

    TelemetryStream stream{"ROBOT_01", packet_time_ns};
    EXPECT_TRUE(stream.is_stale(current_time_ns));
}
