#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <chrono>
#include <memory>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe_usecase.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"
#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"
#include "telemetry_packet.pb.h"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;
using namespace sftwin::edge_control;

// ==============================================================================
// 1. Mock Classes 생성
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

// [FIX] 테스트를 위한 추가 Mock 및 의존성 객체
class MockBehaviorTreeEngine : public anomaly_failsafe::ports::IBehaviorTreeEngine {
   public:
    MOCK_METHOD(bool, execute_script, (const std::string&), (override));
};

// ==============================================================================
// 2. Test Fixture 설정
// ==============================================================================
class TriggerFailsafeUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::shared_ptr<MockBehaviorTreeEngine> mock_bt;
    std::shared_ptr<anomaly_failsafe::adapters::FailsafeProtobufMapper> mapper;

    std::unique_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> usecase;
    anomaly_failsafe::domain::FailsafeRule default_rule;

    void SetUp() override {
        // [FIX] Async Logger 초기화 보장
        common::logging::EdgeLogger::init();

        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();
        mock_bt = std::make_shared<NiceMock<MockBehaviorTreeEngine>>();
        mapper = std::make_shared<anomaly_failsafe::adapters::FailsafeProtobufMapper>();

        default_rule.max_torque_limit_nm = 150.5f;
        default_rule.heartbeat_timeout_ns = 100'000'000ULL;
        default_rule.vision_critical_distance_m = 0.5f;
        default_rule.vision_warning_distance_m = 1.5f;
        default_rule.max_ai_anomaly_score = 0.85f;

        // [FIX] 파라미터 5개를 넘겨 인스턴스화
        usecase = std::make_unique<anomaly_failsafe::application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, mock_bt, mapper, default_rule);
    }
};

// ==============================================================================
// 3. 검증 시나리오 (Given-When-Then)
// ==============================================================================

TEST_F(TriggerFailsafeUseCaseTest, HappyPath_NoViolations) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns());
    proto.add_joint_torques(100.0f);

    // [FIX] 명시적인 네임스페이스 적용
    sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    // When
    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry); });
}

TEST_F(TriggerFailsafeUseCaseTest, EdgeCase_WarningIntrusion_TriggersBypass) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns());
    proto.add_joint_torques(50.0f);

    auto* obj = proto.add_detected_objects();
    obj->add_bbox(0.0f);
    obj->add_bbox(0.0f);
    obj->add_bbox(1.2f);

    sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    // When
    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry); });
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_TorqueExceeded_TriggersEStop) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns());
    proto.add_joint_torques(160.0f);

    sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    // When
    try {
        usecase->evaluate_and_trigger(telemetry);
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_FAILSAFE_TRIGGERED");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}

TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_HeartbeatTimeout_TriggersEStop) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    uint64_t past_150ms =
        sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns() - 150'000'000ULL;
    proto.set_timestamp_ns(past_150ms);

    sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    // When
    EXPECT_THROW(
        { usecase->evaluate_and_trigger(telemetry); }, common::exceptions::EdgeSystemException);
}
