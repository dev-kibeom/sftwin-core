#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;
using namespace sftwin::edge_control;

// ==============================================================================
// 1. Mock Classes (정화된  인터페이스 상속)
// ==============================================================================
class MockHardwareInterlock : public anomaly_failsafe::ports::IHardwareInterlock {
   public:
    MOCK_METHOD(void, trigger_physical_relay, (), (override));

    MOCK_METHOD(bool, release_interlock, (const std::string& operator_approval_token), (override));

    // 2. get_state 모킹 추가 (const 키워드 누락 주의!)
    MOCK_METHOD(sftwin::edge_control::anomaly_failsafe::enums::InterlockState, get_state, (), (const, override));
};

class MockFailsafePublisher : public anomaly_failsafe::ports::IFailsafePublisher {
   public:
    MOCK_METHOD(bool, publish,
                (const std::string&, const anomaly_failsafe::dtos::FailsafeCommandDto&),
                (override));
};

class MockRecoverySequence : public anomaly_failsafe::ports::IRecoverySequence {
   public:
    MOCK_METHOD(bool, execute_recovery_sequence, (const std::string&), (override));
};

// ==============================================================================
// 2. Test Fixture
// ==============================================================================
class FailsafeRecoveryTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockRecoverySequence> mock_recovery;

    anomaly_failsafe::domain::FailsafeRule default_rule;
    std::unique_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> usecase;

    void SetUp() override {
        common::logging::EdgeLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_recovery = std::make_shared<NiceMock<MockRecoverySequence>>();

        // Mapper 파라미터가 소멸된 4개 파라미터 생성자로 주입
        usecase = std::make_unique<anomaly_failsafe::application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_recovery, default_rule);
    }
};

// ==============================================================================
// 3. 검증 시나리오
// ==============================================================================

TEST_F(FailsafeRecoveryTest, HappyPath_ManualEStop_Success) {
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    EXPECT_NO_THROW({ usecase->trigger_manual_estop("MANUAL_EMERGENCY"); });

    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::INTERLOCK_ENGAGED);
}

TEST_F(FailsafeRecoveryTest, HappyPath_ResumeProcess_Success) {
    usecase->trigger_manual_estop("MANUAL_EMERGENCY");
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::INTERLOCK_ENGAGED);

    EXPECT_CALL(*mock_recovery, execute_recovery_sequence("<root>valid_xml</root>")).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, publish("failsafe/resume", _)).WillOnce(Return(true));

    bool result = false;
    EXPECT_NO_THROW(
        { result = usecase->execute_recovery_sequence("<root>valid_xml</root>"); });

    EXPECT_TRUE(result);
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);
}

TEST_F(FailsafeRecoveryTest, EdgeCase_InvalidStateTransition_Blocked) {
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);

    EXPECT_CALL(*mock_recovery, execute_recovery_sequence(_)).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    try {
        EXPECT_FALSE(usecase->execute_recovery_sequence("<root>invalid_request</root>"));
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_INVALID_INPUT");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}
