#include <gtest/gtest.h>
#include <memory>
#include <string>

#include "edge_control/anomaly_failsafe/application/execute_recovery_sequence/execute_recovery_sequence_dto.hpp"
#include "edge_control/anomaly_failsafe/application/execute_recovery_sequence/execute_recovery_sequence_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"
#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "edge_control/contracts/dtos/recovery_execution_result_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/contracts/ports/outbound/i_recovery_sequence.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe::application;
using namespace sftwin::edge_control::anomaly_failsafe::domain;
using namespace sftwin::shared;

class MockRecoverySequence : public IRecoverySequence {
public:
    bool should_succeed{true};
    std::string received_script;

    RecoveryExecutionResultDto execute_sequence(const std::string& sequence_script) override {
        received_script = sequence_script;
        if (should_succeed) {
            return RecoveryExecutionResultDto::success();
        }
        return RecoveryExecutionResultDto::failure("No alternative recovery path found.", "ERR_SIM_RECOVER_EVAL_FAILED");
    }
};

class MockFailsafePublisher : public IFailsafePublisher {
public:
    int publish_count{0};
    std::string last_action;

    void publish(const std::string&, const FailsafeCommandDto& data) override {
        publish_count++;
        last_action = data.action_type();
    }
};

class ExecuteRecoverySequenceUseCaseTest : public ::testing::Test {
protected:
    std::shared_ptr<InterlockManager> interlock_mgr;
    std::shared_ptr<MockFailsafePublisher> mock_pub;
    std::shared_ptr<MockRecoverySequence> mock_recovery;
    std::unique_ptr<ExecuteRecoverySequenceUseCase> usecase;

    void SetUp() override {
        interlock_mgr = std::make_shared<InterlockManager>(InterlockState::ENGAGED);
        mock_pub = std::make_shared<MockFailsafePublisher>();
        mock_recovery = std::make_shared<MockRecoverySequence>();
        usecase = std::make_unique<ExecuteRecoverySequenceUseCase>(
            interlock_mgr, mock_pub, mock_recovery
        );
    }
};

TEST_F(ExecuteRecoverySequenceUseCaseTest, RecoverySuccessReleasesInterlock) {
    mock_recovery->should_succeed = true;
    ExecuteRecoverySequenceRequestDto req{"<root>recovery_behavior_tree</root>", "ROBOT_01"};

    const auto result = usecase->execute(req);

    EXPECT_TRUE(result.is_success());
    EXPECT_EQ(interlock_mgr->state(), InterlockState::RELEASED);
    EXPECT_EQ(mock_pub->publish_count, 1);
    EXPECT_EQ(mock_pub->last_action, "RESUME");
    EXPECT_EQ(mock_recovery->received_script, "<root>recovery_behavior_tree</root>");
}

TEST_F(ExecuteRecoverySequenceUseCaseTest, RecoveryFailureMaintainsEngagedState) {
    mock_recovery->should_succeed = false;
    ExecuteRecoverySequenceRequestDto req{"<invalid>syntax</invalid>", "ROBOT_01"};

    const auto result = usecase->execute(req);

    EXPECT_FALSE(result.is_success());
    EXPECT_EQ(result.error_code(), "ERR_SIM_RECOVER_EVAL_FAILED");
    EXPECT_EQ(interlock_mgr->state(), InterlockState::ENGAGED);
    EXPECT_EQ(mock_pub->publish_count, 0);
}

TEST_F(ExecuteRecoverySequenceUseCaseTest, ThrowsExceptionWhenNotInEngagedState) {
    interlock_mgr->release();  // 이미 정상 상태인 경우
    ExecuteRecoverySequenceRequestDto req{"<root>script</root>", "ROBOT_01"};

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
    EXPECT_EQ(mock_pub->publish_count, 0);
}
