#include <gtest/gtest.h>
#include <stdexcept>
#include "edge_control/anomaly_failsafe/domain/interlock_management/estop_reset_policy.hpp"

using namespace sftwin::edge_control::anomaly_failsafe::domain;

TEST(EstopResetPolicyTest, ResetSuccessWhenBothApproved) {
    EstopResetPolicy policy;
    EXPECT_NO_THROW(policy.validate_reset_request(InterlockState::ENGAGED, true, true));
}

TEST(EstopResetPolicyTest, ThrowsLogicErrorWhenNotEngaged) {
    EstopResetPolicy policy;
    EXPECT_THROW(policy.validate_reset_request(InterlockState::RELEASED, true, true), std::logic_error);
}

TEST(EstopResetPolicyTest, ThrowsInvalidArgumentWhenApprovalMissing) {
    EstopResetPolicy policy;
    EXPECT_THROW(policy.validate_reset_request(InterlockState::ENGAGED, true, false), std::invalid_argument);
    EXPECT_THROW(policy.validate_reset_request(InterlockState::ENGAGED, false, true), std::invalid_argument);
}
