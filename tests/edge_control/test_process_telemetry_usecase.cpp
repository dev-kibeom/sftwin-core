#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <chrono>
#include <memory>
#include <string>
#include <vector>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/realtime_telemetry/application/process_telemetry_usecase.hpp"
#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"
#include "src/edge_control/realtime_telemetry/ports/i_telemetry_subscriber.hpp"
#include "src/edge_control/realtime_telemetry/ports/i_vision_detector.hpp"
#include "telemetry_packet.pb.h"

using ::testing::_;
using ::testing::NiceMock;
using ::testing::Return;
using namespace sftwin::edge_control;

// ==============================================================================
// 1. Mock Classes 생성 (DIP 인터페이스 모킹)
// ==============================================================================
class MockTelemetrySubscriber : public ports::ITelemetrySubscriber {
   public:
    MOCK_METHOD(bool, is_initialized, (), (const, override));
    MOCK_METHOD(dtos::TelemetryPacketDto, read_latest_packet, (const std::string&), (override));
};

class MockVisionDetector : public ports::IVisionDetector {
   public:
    MOCK_METHOD(std::vector<sftwin::telemetry::DetectedObject>, get_latest_detections, (),
                (override));
};

// ==============================================================================
// 2. Test Fixture 설정
// ==============================================================================
class ProcessTelemetryUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockTelemetrySubscriber> mock_dds;
    std::shared_ptr<MockVisionDetector> mock_vision;
    std::shared_ptr<application::ProcessTelemetryUseCase> usecase;

    void SetUp() override {
        mock_dds = std::make_shared<NiceMock<MockTelemetrySubscriber>>();
        mock_vision = std::make_shared<NiceMock<MockVisionDetector>>();
        usecase = std::make_shared<application::ProcessTelemetryUseCase>(mock_dds, mock_vision);
    }

    // 테스트용 타임스탬프 헬퍼 함수
    uint64_t get_time_ns_offset(int64_t offset_ms) {
        auto now = std::chrono::high_resolution_clock::now().time_since_epoch();
        auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
        return now_ns + (offset_ms * 1'000'000LL);
    }

    // 더미 Proto 생성 헬퍼 함수
    dtos::TelemetryPacketDto create_dummy_packet(const std::string& device_id,
                                                 uint64_t timestamp_ns) {
        sftwin::telemetry::TelemetryPacketProto proto;
        proto.set_device_id(device_id);
        proto.set_timestamp_ns(timestamp_ns);
        proto.set_packml_state("EXECUTE");
        proto.set_is_warning(false);
        return dtos::TelemetryPacketDto(proto);
    }
};

// ==============================================================================
// 3. 검증 시나리오 (Given-When-Then)
// ==============================================================================

/**
 * @brief TC-정상 (Happy Path): 10ms 지연 (정상), 비전 객체 1개 병합 성공
 */
TEST_F(ProcessTelemetryUseCaseTest, HappyPath_SuccessWithin100ms) {
    // Given
    std::string target_device = "DOOSAN_M1013_001";
    uint64_t past_10ms = get_time_ns_offset(-10);  // 10ms 전

    EXPECT_CALL(*mock_dds, is_initialized()).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, read_latest_packet(target_device))
        .WillOnce(Return(create_dummy_packet(target_device, past_10ms)));

    std::vector<sftwin::telemetry::DetectedObject> dummy_vision(1);
    dummy_vision[0].set_class_name("Worker");
    dummy_vision[0].set_confidence(0.95f);
    EXPECT_CALL(*mock_vision, get_latest_detections()).WillOnce(Return(dummy_vision));

    // When
    auto start_time = std::chrono::high_resolution_clock::now();
    dtos::TelemetryPacketDto result = usecase->get_latest_telemetry(target_device);
    auto end_time = std::chrono::high_resolution_clock::now();

    // Then
    auto execution_time_ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();

    // 100ms TIS 제약 조건 통과 확인
    EXPECT_LT(execution_time_ms, 100);

    // 데이터 무결성 검증
    EXPECT_EQ(result.device_id(), target_device);
    EXPECT_EQ(result.get_proto().detected_objects_size(), 1);
    EXPECT_EQ(result.get_proto().detected_objects(0).class_name(), "Worker");
    EXPECT_TRUE(result.get_proto().is_warning());  // 병합 로직에서 Warning이 true로 세팅되는지 확인
}

/**
 * @brief TC-예외 (Edge Case): 99ms 지연 (임계치 직전 통과), 비전 객체 없음
 */
TEST_F(ProcessTelemetryUseCaseTest, EdgeCase_NoVisionAndBoundaryDelay) {
    // Given
    std::string target_device = "DOOSAN_M1013_001";
    uint64_t past_99ms = get_time_ns_offset(-99);  // 99ms 전 (경계선)

    EXPECT_CALL(*mock_dds, is_initialized()).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, read_latest_packet(target_device))
        .WillOnce(Return(create_dummy_packet(target_device, past_99ms)));

    std::vector<sftwin::telemetry::DetectedObject> empty_vision;
    EXPECT_CALL(*mock_vision, get_latest_detections()).WillOnce(Return(empty_vision));

    // When & Then (No Exception Thrown)
    dtos::TelemetryPacketDto result;
    EXPECT_NO_THROW({ result = usecase->get_latest_telemetry(target_device); });

    EXPECT_EQ(result.get_proto().detected_objects_size(), 0);
    EXPECT_EQ(result.get_proto().packml_state(), "EXECUTE");  // 상태 유지 검증
    EXPECT_FALSE(result.get_proto().is_warning());
}

/**
 * @brief TC-에러 (Error Handling): 150ms 지연 (통신 타임아웃 예외 발생)
 */
TEST_F(ProcessTelemetryUseCaseTest, ErrorCase_CommTimeoutThrowsException) {
    // Given
    std::string target_device = "DOOSAN_M1013_001";
    uint64_t past_150ms = get_time_ns_offset(-150);  // 150ms 전 (지연 발생)

    EXPECT_CALL(*mock_dds, is_initialized()).WillOnce(Return(true));
    EXPECT_CALL(*mock_dds, read_latest_packet(target_device))
        .WillOnce(Return(create_dummy_packet(target_device, past_150ms)));

    // When & Then
    try {
        usecase->get_latest_telemetry(target_device);
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        // 커스텀 예외 코드 매핑 검증
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_COMM_TIMEOUT");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}

/**
 * @brief TC-초기화 에러: FastDDS 초기화 실패 시 즉각 중단
 */
TEST_F(ProcessTelemetryUseCaseTest, ErrorCase_InitFailThrowsException) {
    // Given
    std::string target_device = "DOOSAN_M1013_001";

    EXPECT_CALL(*mock_dds, is_initialized()).WillOnce(Return(false));

    // When & Then
    try {
        usecase->get_latest_telemetry(target_device);
        FAIL() << "Expected EdgeSystemException to be thrown";
    } catch (const common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_DDS_INIT_FAIL");
    } catch (...) {
        FAIL() << "Expected EdgeSystemException, but a different exception was thrown";
    }
}