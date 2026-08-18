#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>

#include "edge_control/anomaly_failsafe/application/reset_estop_interlock/reset_estop_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/enums/edge_engine_state_enum.hpp"
#include "edge_control/anomaly_failsafe/domain/estop_reset_policy.hpp"
#include "edge_control/common/exceptions/edge_system_exception.hpp"
#include "edge_control/common/logging/edge_logger.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe;

class MockFailsafePublisher : public IFailsafePublisher {
   public:
    MOCK_METHOD(bool, publish, (const std::string&, const FailsafeCommandDto&), (override));
};

class ResetEstopInterlockUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockFailsafePublisher> mock_pub;
    domain::EstopResetPolicy policy;
    std::unique_ptr<application::ResetEstopInterlockUseCase> usecase;

    void SetUp() override {
        EdgeLogger::init();
        mock_pub = std::make_shared<NiceMock<MockFailsafePublisher>>();
        usecase = std::make_unique<application::ResetEstopInterlockUseCase>(
            "EDGE_NODE_001", policy, mock_pub);
    }
};

// 1. Happy Path: 현장 점검 완료 및 관리자 승인 시 정상 해제 (ACTIVE_MONITORING 전환)
TEST_F(ResetEstopInterlockUseCaseTest, HappyPath_TwoStepReset_Success) {
    EXPECT_CALL(*mock_pub, publish("failsafe/resume", _)).WillOnce(Return(true));

    auto next_state = usecase->execute(
        domain::EdgeEngineState::INTERLOCK_ENGAGED,
        /*is_field_inspected=*/true,
        /*is_manager_approved=*/true);

    EXPECT_EQ(next_state, domain::EdgeEngineState::ACTIVE_MONITORING);
}

// 2. State Violation: 인터록 상태가 아닌데 리셋을 시도할 경우 ERR_COMMON_INVALID_INPUT 예외
TEST_F(ResetEstopInterlockUseCaseTest, StateViolation_NotInterlocked_ThrowsException) {
    EXPECT_CALL(*mock_pub, publish(_, _)).Times(0);

    try {
        (void)usecase->execute(
            domain::EdgeEngineState::ACTIVE_MONITORING,
            /*is_field_inspected=*/true,
            /*is_manager_approved=*/true);
        FAIL() << "Expected EdgeSystemException";
    } catch (const EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_INVALID_INPUT");
    }
}

// 3. Approval Rejected: 현장 점검이나 관리자 승인 중 하나라도 누락되면 ERR_COMMON_FORBIDDEN 예외
TEST_F(ResetEstopInterlockUseCaseTest, ApprovalRejected_MissingApproval_ThrowsForbidden) {
    EXPECT_CALL(*mock_pub, publish(_, _)).Times(0);

    // 현장 점검은 되었으나 관리자 승인이 없는 경우
    try {
        (void)usecase->execute(
            domain::EdgeEngineState::INTERLOCK_ENGAGED,
            /*is_field_inspected=*/true,
            /*is_manager_approved=*/false);
        FAIL() << "Expected EdgeSystemException";
    } catch (const EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_FORBIDDEN");
    }
}
