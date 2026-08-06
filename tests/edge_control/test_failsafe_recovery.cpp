#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe_usecase.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;
using namespace sftwin::edge_control;

// ==============================================================================
// 1. Mock Classes
// ==============================================================================
class MockHardwareInterlock : public anomaly_failsafe::ports::IHardwareInterlock {
   public:
    MOCK_METHOD(void, trigger_physical_relay, (), (override));
};

class MockFailsafePublisher : public anomaly_failsafe::ports::IFailsafePublisher {
   public:
    MOCK_METHOD(bool, publish,
                (const std::string&, const anomaly_failsafe::dtos::FailsafeCommandDto&),
                (override));
};

class MockBehaviorTreeEngine : public anomaly_failsafe::ports::IBehaviorTreeEngine {
   public:
    MOCK_METHOD(bool, execute_script, (const std::string&), (override));
};

// ==============================================================================
// 2. Test Fixture
// ==============================================================================
class FailsafeRecoveryTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockBehaviorTreeEngine> mock_bt;
    std::shared_ptr<anomaly_failsafe::adapters::FailsafeProtobufMapper> mapper;

    // [FIX] 주입할 Rule 객체 선언
    anomaly_failsafe::domain::FailsafeRule default_rule;

    std::unique_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> usecase;

    void SetUp() override {
        common::logging::EdgeLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_bt = std::make_shared<NiceMock<MockBehaviorTreeEngine>>();
        mapper = std::make_shared<anomaly_failsafe::adapters::FailsafeProtobufMapper>();

        // [FIX] 파라미터 5개 주입 (Rule 포함)
        usecase = std::make_unique<anomaly_failsafe::application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_bt, mapper, default_rule);
    }
};

// ==============================================================================
// 3. 검증 시나리오 (Given-When-Then)
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

    EXPECT_CALL(*mock_bt, execute_script("<root>valid_xml</root>")).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, publish("failsafe/resume", _)).WillOnce(Return(true));

    bool result = false;
    EXPECT_NO_THROW(
        { result = usecase->execute_behavior_tree_recovery("<root>valid_xml</root>"); });

    EXPECT_TRUE(result);
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);
}

TEST_F(FailsafeRecoveryTest, EdgeCase_InvalidStateTransition_Blocked) {
    EXPECT_EQ(usecase->get_current_state(),
              anomaly_failsafe::domain::EdgeEngineState::ACTIVE_MONITORING);

    EXPECT_CALL(*mock_bt, execute_script(_)).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    try {
        usecase->execute_behavior_tree_recovery("<root>invalid_request</root>");
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_COMMON_INVALID_INPUT");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}

TEST_F(FailsafeRecoveryTest, HappyPath_MapperConversion) {
    std::string test_device = "TEST_DEVICE";
    std::string test_reason = "OVERHEAT";

    auto proto = mapper->to_protobuf(anomaly_failsafe::domain::FailsafeActionEnum::PAUSE,
                                     test_device, test_reason);

    EXPECT_EQ(proto.action_type(), "PAUSE");
    EXPECT_EQ(proto.target_device_id(), test_device);
    EXPECT_EQ(proto.trigger_reason(), test_reason);
    EXPECT_GT(proto.issued_timestamp_ns(), 0);
}