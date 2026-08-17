#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>

#include "edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/enums/edge_engine_state_enum.hpp"
#include "edge_control/anomaly_failsafe/domain/enums/interlock_state_enum.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "edge_control/common/exceptions/edge_system_exception.hpp"
#include "edge_control/common/logging/edge_logger.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/ports/outbound/i_hardware_interlock.hpp"
#include "edge_control/ports/outbound/i_recovery_sequence.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe;

class MockHardwareInterlock : public IHardwareInterlock {
   public:
    MOCK_METHOD(void, trigger_physical_relay, (), (override));
    MOCK_METHOD(bool, release_interlock, (const std::string& operator_approval_token), (override));
    MOCK_METHOD(domain::InterlockState, get_state, (), (const, override));
};

class MockFailsafePublisher : public IFailsafePublisher {
   public:
    MOCK_METHOD(bool, publish, (const std::string&, const FailsafeCommandDto&), (override));
};

class MockRecoverySequence : public IRecoverySequence {
   public:
    MOCK_METHOD(bool, execute_recovery_sequence, (const std::string&), (override));
};

class FailsafeRecoveryTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockRecoverySequence> mock_recovery;

    domain::FailsafeRule default_rule;
    std::unique_ptr<application::TriggerFailsafeUseCase> usecase;

    void SetUp() override {
        EdgeLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_recovery = std::make_shared<NiceMock<MockRecoverySequence>>();

        usecase = std::make_unique<application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_recovery, default_rule);
    }
};

TEST_F(FailsafeRecoveryTest, HappyPath_ManualEStop_Success) {
    EXPECT_EQ(usecase->get_current_state(), domain::EdgeEngineState::ACTIVE_MONITORING);
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    EXPECT_NO_THROW({ usecase->trigger_manual_estop("MANUAL_EMERGENCY"); });

    EXPECT_EQ(usecase->get_current_state(), domain::EdgeEngineState::INTERLOCK_ENGAGED);
}

TEST_F(FailsafeRecoveryTest, HappyPath_ResumeProcess_Success) {
    usecase->trigger_manual_estop("MANUAL_EMERGENCY");
    EXPECT_EQ(usecase->get_current_state(), domain::EdgeEngineState::INTERLOCK_ENGAGED);

    EXPECT_CALL(*mock_recovery, execute_recovery_sequence("<root>valid_xml</root>")).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, publish("failsafe/resume", _)).WillOnce(Return(true));

    bool result = false;
    EXPECT_NO_THROW({ result = usecase->execute_recovery_sequence("<root>valid_xml</root>"); });

    EXPECT_TRUE(result);
    EXPECT_EQ(usecase->get_current_state(), domain::EdgeEngineState::ACTIVE_MONITORING);
}

TEST_F(FailsafeRecoveryTest, EdgeCase_InvalidStateTransition_Blocked) {
    EXPECT_EQ(usecase->get_current_state(), domain::EdgeEngineState::ACTIVE_MONITORING);

    EXPECT_CALL(*mock_recovery, execute_recovery_sequence(_)).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    try {
        EXPECT_FALSE(usecase->execute_recovery_sequence("<root>invalid_request</root>"));
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_INVALID_INPUT");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}
