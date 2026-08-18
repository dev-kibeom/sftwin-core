#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>

#include "edge_control/anomaly_failsafe/application/reset_interlock/reset_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/estop_reset_policy.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/logger/global_system_logger.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::shared;
using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe;

class MockFailsafePublisher : public IFailsafePublisher {
   public:
    MOCK_METHOD(bool, publish, (const std::string&, const FailsafeCommandDto&), (override));
};

class ResetInterlockUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockFailsafePublisher> mock_pub;
    domain::EstopResetPolicy policy;
    std::unique_ptr<application::ResetInterlockUseCase> usecase;

    void SetUp() override {
        GlobalSystemLogger::init();
        mock_pub = std::make_shared<NiceMock<MockFailsafePublisher>>();
        usecase = std::make_unique<application::ResetInterlockUseCase>(
            "EDGE_NODE_001", policy, mock_pub);
    }
};

// 1. Happy Path: 현장 점검 완료 및 관리자 승인 시 정상 해제 (RELEASED 전환)
TEST_F(ResetInterlockUseCaseTest, HappyPath_TwoStepReset_Success) {
    EXPECT_CALL(*mock_pub, publish("failsafe/resume", _)).WillOnce(Return(true));

    auto next_state = usecase->execute(
        domain::InterlockState::ENGAGED,
        /*is_field_inspected=*/true,
        /*is_manager_approved=*/true);

    EXPECT_EQ(next_state, domain::InterlockState::RELEASED);
}

// 2. State Violation: 인터록 상태가 아닌데 리셋을 시도할 경우 ERR_COMMON_INVALID_INPUT 예외
TEST_F(ResetInterlockUseCaseTest, StateViolation_NotInterlocked_ThrowsException) {
    EXPECT_CALL(*mock_pub, publish(_, _)).Times(0);

    try {
        (void)usecase->execute(
            domain::InterlockState::RELEASED,
            /*is_field_inspected=*/true,
            /*is_manager_approved=*/true);
        FAIL() << "Expected GlobalExceptionHandler";
    } catch (const GlobalExceptionHandler& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_INVALID_INPUT");
    }
}

// 3. Approval Rejected: 현장 점검이나 관리자 승인 중 하나라도 누락되면 ERR_COMMON_FORBIDDEN 예외
TEST_F(ResetInterlockUseCaseTest, ApprovalRejected_MissingApproval_ThrowsForbidden) {
    EXPECT_CALL(*mock_pub, publish(_, _)).Times(0);

    // 현장 점검은 되었으나 관리자 승인이 없는 경우
    try {
        (void)usecase->execute(
            domain::InterlockState::ENGAGED,
            /*is_field_inspected=*/true,
            /*is_manager_approved=*/false);
        FAIL() << "Expected GlobalExceptionHandler";
    } catch (const GlobalExceptionHandler& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_FORBIDDEN");
    }
}
