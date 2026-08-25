#include <gtest/gtest.h>
#include <memory>
#include <string>

#include "edge_control/anomaly_failsafe/application/reset_interlock/reset_interlock_dto.hpp"
#include "edge_control/anomaly_failsafe/application/reset_interlock/reset_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/estop_reset_policy.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"
#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe::application;
using namespace sftwin::edge_control::anomaly_failsafe::domain;
using namespace sftwin::shared;

namespace {

class MockFailsafePublisher : public IFailsafePublisher {
public:
    int publish_count{0};
    std::string last_topic{};
    std::string last_action{};

    void publish(const std::string& topic, const FailsafeCommandDto& data) override {
        publish_count++;
        last_topic = topic;
        last_action = data.action_type();
    }
};

} // namespace

class ResetInterlockUseCaseTest : public ::testing::Test {
protected:
    std::shared_ptr<InterlockManager> interlock_mgr;
    std::shared_ptr<MockFailsafePublisher> mock_pub;
    EstopResetPolicy policy;
    std::unique_ptr<ResetInterlockUseCase> usecase;

    void SetUp() override {
        // 인터록이 걸린 상태(ENGAGED)에서 시작
        interlock_mgr = std::make_shared<InterlockManager>(InterlockState::ENGAGED);
        mock_pub = std::make_shared<MockFailsafePublisher>();
        usecase = std::make_unique<ResetInterlockUseCase>(interlock_mgr, policy, mock_pub);
    }
};

TEST_F(ResetInterlockUseCaseTest, Reset2StepSuccessWhenBothApproved) {
    ResetInterlockRequestDto req{
        /* is_field_inspected = */ true,
        /* is_manager_approved = */ true,
        /* device_id = */ "ROBOT_01"
    };

    const auto state = usecase->execute(req);

    EXPECT_EQ(state, InterlockState::RELEASED);
    EXPECT_EQ(interlock_mgr->state(), InterlockState::RELEASED);
    EXPECT_EQ(mock_pub->publish_count, 1);
    EXPECT_EQ(mock_pub->last_topic, "failsafe/resume");
    EXPECT_EQ(mock_pub->last_action, "RESUME");
}

TEST_F(ResetInterlockUseCaseTest, ThrowsExceptionWhenManagerApprovalMissing) {
    ResetInterlockRequestDto req{
        /* is_field_inspected = */ true,
        /* is_manager_approved = */ false,
        /* device_id = */ "ROBOT_01"
    };

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
    EXPECT_EQ(interlock_mgr->state(), InterlockState::ENGAGED);
    EXPECT_EQ(mock_pub->publish_count, 0);
}

TEST_F(ResetInterlockUseCaseTest, ThrowsExceptionWhenFieldInspectionMissing) {
    ResetInterlockRequestDto req{
        /* is_field_inspected = */ false,
        /* is_manager_approved = */ true,
        /* device_id = */ "ROBOT_01"
    };

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
    EXPECT_EQ(interlock_mgr->state(), InterlockState::ENGAGED);
    EXPECT_EQ(mock_pub->publish_count, 0);
}

TEST_F(ResetInterlockUseCaseTest, ThrowsExceptionWhenCurrentStateIsNotEngaged) {
    // 이미 정상(RELEASED) 상태일 때 리셋 시도
    interlock_mgr->release();

    ResetInterlockRequestDto req{true, true, "ROBOT_01"};

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
    EXPECT_EQ(mock_pub->publish_count, 0);
}
