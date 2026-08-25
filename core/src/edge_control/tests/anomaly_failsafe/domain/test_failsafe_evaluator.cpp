#include <gtest/gtest.h>
#include "edge_control/anomaly_failsafe/domain/failsafe_evaluation/failsafe_evaluator.hpp"

using namespace sftwin::edge_control::anomaly_failsafe::domain;

class FailsafeEvaluatorTest : public ::testing::Test {
protected:
    FailsafeRule rule{
        150.5f,        // max_torque_limit_nm
        100'000'000ULL,// heartbeat_timeout_ns (100ms)
        0.5f,          // vision_critical_distance_m
        1.5f,          // vision_warning_distance_m
        0.85f          // max_anomaly_score
    };
    FailsafeEvaluator evaluator{rule};
};

TEST_F(FailsafeEvaluatorTest, EvaluateOkWhenWithinLimits) {
    TelemetrySnapshot snapshot{"ROBOT_01", 1'000'000'000ULL, {50.0f, 60.0f}, 2.0f, 0.1f};
    auto result = evaluator.evaluate_violations(snapshot, 1'000'050'000ULL); // 50ms 경과
    EXPECT_EQ(result.action, FailsafeAction::NONE);
    EXPECT_EQ(result.reason, "OK");
}

TEST_F(FailsafeEvaluatorTest, TriggersEstopOnHeartbeatLoss) {
    const uint64_t packet_timestamp_ns = 1'000'000'000ULL;
    TelemetrySnapshot snapshot{"ROBOT_01", packet_timestamp_ns, {50.0f}, 2.0f, 0.1f};

    // 150ms 경과 (100ms 초과)
    const uint64_t current_time_ns = packet_timestamp_ns + 150'000'000ULL;
    auto result = evaluator.evaluate_violations(snapshot, current_time_ns);

    EXPECT_EQ(result.action, FailsafeAction::ESTOP);
    EXPECT_EQ(result.reason, "HEARTBEAT_LOSS");
}

TEST_F(FailsafeEvaluatorTest, TriggersEstopOnTorqueExceeded) {
    TelemetrySnapshot snapshot{"ROBOT_01", 1'000'000'000ULL, {50.0f, 160.0f}, 2.0f, 0.1f};
    auto result = evaluator.evaluate_violations(snapshot, 1'000'010'000ULL);
    EXPECT_EQ(result.action, FailsafeAction::ESTOP);
    EXPECT_EQ(result.reason, "TORQUE_EXCEEDED");
}

TEST_F(FailsafeEvaluatorTest, TriggersEstopOnCriticalIntrusion) {
    TelemetrySnapshot snapshot{"ROBOT_01", 1'000'000'000ULL, {50.0f}, 0.3f, 0.1f}; // 0.3m (<0.5m)
    auto result = evaluator.evaluate_violations(snapshot, 1'000'010'000ULL);
    EXPECT_EQ(result.action, FailsafeAction::ESTOP);
    EXPECT_EQ(result.reason, "CRITICAL_INTRUSION");
}

TEST_F(FailsafeEvaluatorTest, TriggersBypassOnWarningIntrusion) {
    TelemetrySnapshot snapshot{"ROBOT_01", 1'000'000'000ULL, {50.0f}, 1.0f, 0.1f}; // 1.0m (<1.5m)
    auto result = evaluator.evaluate_violations(snapshot, 1'000'010'000ULL);
    EXPECT_EQ(result.action, FailsafeAction::BYPASS);
    EXPECT_EQ(result.reason, "WARNING_INTRUSION");
}

TEST_F(FailsafeEvaluatorTest, TriggersEstopOnAnomalyScoreExceeded) {
    TelemetrySnapshot snapshot{"ROBOT_01", 1'000'000'000ULL, {50.0f}, 2.0f, 0.95f}; // 0.95 (>0.85)
    auto result = evaluator.evaluate_violations(snapshot, 1'000'010'000ULL);
    EXPECT_EQ(result.action, FailsafeAction::ESTOP);
    EXPECT_EQ(result.reason, "ANOMALY_SCORE_EXCEEDED");
}
