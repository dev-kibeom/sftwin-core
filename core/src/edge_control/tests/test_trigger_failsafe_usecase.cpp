#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <vector>

#include "edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/enums/interlock_state_enum.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/logger/global_system_logger.hpp"
#include "shared/utils/time_provider.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "edge_control/ports/inbound/dtos/telemetry_packet_dto.hpp"
#include "edge_control/ports/inbound/dtos/vision_detection_dto.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/ports/outbound/i_hardware_interlock.hpp"
#include "edge_control/ports/outbound/i_recovery_sequence.hpp"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::shared;
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

class TriggerFailsafeUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockRecoverySequence> mock_recovery;

    std::unique_ptr<application::TriggerFailsafeUseCase> usecase;
    domain::FailsafeRule default_rule;

    void SetUp() override {
        GlobalSystemLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_recovery = std::make_shared<NiceMock<MockRecoverySequence>>();

        default_rule.max_torque_limit_nm = 150.5f;
        default_rule.heartbeat_timeout_ns = 100'000'000ULL;
        default_rule.vision_critical_distance_m = 0.5f;
        default_rule.vision_warning_distance_m = 1.5f;
        default_rule.max_ai_anomaly_score = 0.85f;

        usecase = std::make_unique<application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_recovery, default_rule);
    }
};

TEST_F(TriggerFailsafeUseCaseTest, HappyPath_NoViolations) {
    const uint64_t now = GlobalTimeProvider::get_steady_time_ns();
    const TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {100.0f});
    const std::vector<VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry, detections); });
}

TEST_F(TriggerFailsafeUseCaseTest, EdgeCase_WarningIntrusion_TriggersBypass) {
    const uint64_t now = GlobalTimeProvider::get_steady_time_ns();
    const TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {50.0f});

    const VisionDetectionDto warning_obj{"WORKER", 0.9f, {0.0f, 0.0f, 1.2f, 0.0f}, now};
    const std::vector<VisionDetectionDto> detections{warning_obj};

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry, detections); });
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_TorqueExceeded_TriggersEStop) {
    const uint64_t now = GlobalTimeProvider::get_steady_time_ns();
    const TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {160.0f});
    const std::vector<VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    try {
        usecase->evaluate_and_trigger(telemetry, detections);
        FAIL() << "Expected GlobalExceptionHandler to be thrown";
    } catch (const GlobalExceptionHandler& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_FAILSAFE_TRIGGERED");
    } catch (...) {
        FAIL() << "Expected GlobalExceptionHandler, but a different exception was thrown";
    }
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_HeartbeatTimeout_TriggersEStop) {
    const uint64_t past_150ms = GlobalTimeProvider::get_steady_time_ns() - 150'000'000ULL;
    const TelemetryPacketDto telemetry("DOOSAN_M1013_002", past_150ms);
    const std::vector<VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    EXPECT_THROW({ usecase->evaluate_and_trigger(telemetry, detections); }, GlobalExceptionHandler);
}
