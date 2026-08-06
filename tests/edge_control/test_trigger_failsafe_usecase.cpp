#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <chrono>
#include <memory>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe_usecase.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "telemetry_packet.pb.h"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;
using namespace sftwin::edge_control;

// ==============================================================================
// 1. Mock Classes 생성 (DIP 인터페이스 모킹)
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

// ==============================================================================
// 2. Test Fixture 설정
// ==============================================================================
class TriggerFailsafeUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockHardwareInterlock> mock_hw;
    std::shared_ptr<MockFailsafePublisher> mock_dds;
    std::unique_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> usecase;
    anomaly_failsafe::domain::FailsafeRule default_rule;

    void SetUp() override {
        mock_hw = std::make_shared<NiceMock<MockHardwareInterlock>>();
        mock_dds = std::make_shared<NiceMock<MockFailsafePublisher>>();

        // FDS 요구사항 임계치 세팅
        default_rule.max_torque_limit_nm = 150.5f;
        default_rule.heartbeat_timeout_ns = 100'000'000ULL;
        default_rule.vision_critical_distance_m = 0.5f;
        default_rule.vision_warning_distance_m = 1.5f;
        default_rule.max_ai_anomaly_score = 0.85f;

        usecase = std::make_unique<anomaly_failsafe::application::TriggerFailsafeUseCase>(
            mock_hw, mock_dds, default_rule);
    }

    uint64_t get_current_time_ns() {
        auto now = std::chrono::steady_clock::now().time_since_epoch();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
    }
};

// ==============================================================================
// 3. 검증 시나리오 (Given-When-Then)
// ==============================================================================

/**
 * @brief TC-정상 (Happy Path): 모든 수치가 안전 임계치 내에 존재
 */
TEST_F(TriggerFailsafeUseCaseTest, HappyPath_NoViolations) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(get_current_time_ns());  // 지연 없음
    proto.add_joint_torques(100.0f);                // 150.5 미만 안전 토크
    dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    // When
    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry); });
}

/**
 * @brief TC-예외 (Edge Case): 주의 반경 진입 시 BYPASS 및 Warning 로깅
 */
TEST_F(TriggerFailsafeUseCaseTest, EdgeCase_WarningIntrusion_TriggersBypass) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(get_current_time_ns());
    proto.add_joint_torques(50.0f);

    // 주의 반경(0.5m ~ 1.5m) 조건 만족 (bbox 2번 인덱스를 거리로 사용)
    auto* obj = proto.add_detected_objects();
    obj->add_bbox(0.0f);
    obj->add_bbox(0.0f);
    obj->add_bbox(1.2f);  // 1.2m
    dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(0);
    EXPECT_CALL(*mock_dds, publish(_, _)).Times(0);

    // When
    EXPECT_NO_THROW({ usecase->evaluate_and_trigger(telemetry); });
}

/**
 * @brief TC-에러 (Error Handling): 치명적 위반(토크 초과) 시 ESTOP 발송 및 예외 발생
 */
TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_TorqueExceeded_TriggersEStop) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    proto.set_timestamp_ns(get_current_time_ns());
    proto.add_joint_torques(160.0f);  // 150.5 초과
    dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    // When
    auto start = std::chrono::high_resolution_clock::now();

    try {
        usecase->evaluate_and_trigger(telemetry);
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_FAILSAFE_TRIGGERED");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    // 결정론적 처리 시간 100ms 이내 보장 검증
    EXPECT_LT(duration_ms, 100);
}

/**
 * @brief TC-에러 (Error Handling): 통신 타임아웃 지연 시 HEARTBEAT_LOSS 발동
 */
TEST_F(TriggerFailsafeUseCaseTest, ErrorCase_HeartbeatTimeout_TriggersEStop) {
    // Given
    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_002");
    // 150ms 지연 발생 시뮬레이션
    uint64_t past_150ms = get_current_time_ns() - 150'000'000ULL;
    proto.set_timestamp_ns(past_150ms);
    dtos::TelemetryPacketDto telemetry(proto);

    // Then
    EXPECT_CALL(*mock_hw, trigger_physical_relay()).Times(1);
    EXPECT_CALL(*mock_dds, publish("failsafe/estop", _)).WillOnce(Return(true));

    // When
    EXPECT_THROW(
        { usecase->evaluate_and_trigger(telemetry); }, common::exceptions::EdgeSystemException);
}