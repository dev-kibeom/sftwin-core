#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <vector>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"
#include "src/edge_control/common/dtos/telemetry_packet_dto.hpp"
#include "src/edge_control/common/dtos/vision_detection_dto.hpp"

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
// 2. Test Fixture 설정
// ==============================================================================
class TriggerFailsafeUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockRecoverySequence> mock_recovery;

    std::unique_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> usecase;
    anomaly_failsafe::domain::FailsafeRule default_rule;

    void SetUp() override {
        common::logging::EdgeLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_recovery = std::make_shared<NiceMock<MockRecoverySequence>>();

        default_rule.max_torque_limit_nm = 150.5f;
        default_rule.heartbeat_timeout_ns = 100'000'000ULL;
        default_rule.vision_critical_distance_m = 0.5f;
        default_rule.vision_warning_distance_m = 1.5f;
        default_rule.max_ai_anomaly_score = 0.85f;

        usecase = std::make_unique<anomaly_failsafe::application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_recovery, default_rule);
    }
};

// ==============================================================================
// 3. 검증 시나리오
// ==============================================================================

TEST_F(TriggerFailsafeUseCaseTest, HappyPath_NoViolations) {
    uint64_t now = common::utils::TimeProvider::get_steady_time_ns();
    realtime_telemetry::dtos::TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {100.0f});
    std::vector<realtime_telemetry::dtos::VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry, detections); });
}

TEST_F(TriggerFailsafeUseCaseTest, EdgeCase_WarningIntrusion_TriggersBypass) {
    uint64_t now = common::utils::TimeProvider::get_steady_time_ns();
    realtime_telemetry::dtos::TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {50.0f});

    // bbox[2] (width 역산) 1.2m -> 경고 구역 (1.5m 미만)
    realtime_telemetry::dtos::VisionDetectionDto warning_obj{"WORKER", 0.9f, {0.0f, 0.0f, 1.2f, 0.0f}, now};
    std::vector<realtime_telemetry::dtos::VisionDetectionDto> detections{warning_obj};

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry, detections); });
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_TorqueExceeded_TriggersEStop) {
    uint64_t now = common::utils::TimeProvider::get_steady_time_ns();
    // 토크 160.0f > 한계 150.5f
    realtime_telemetry::dtos::TelemetryPacketDto telemetry("DOOSAN_M1013_002", now, {0.0f}, {160.0f});
    std::vector<realtime_telemetry::dtos::VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    try {
        usecase->evaluate_and_trigger(telemetry, detections);
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_FAILSAFE_TRIGGERED");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_HeartbeatTimeout_TriggersEStop) {
    uint64_t past_150ms = common::utils::TimeProvider::get_steady_time_ns() - 150'000'000ULL;
    realtime_telemetry::dtos::TelemetryPacketDto telemetry("DOOSAN_M1013_002", past_150ms);
    std::vector<realtime_telemetry::dtos::VisionDetectionDto> detections;

    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    EXPECT_THROW(
        { usecase->evaluate_and_trigger(telemetry, detections); }, common::exceptions::EdgeSystemException);
}
