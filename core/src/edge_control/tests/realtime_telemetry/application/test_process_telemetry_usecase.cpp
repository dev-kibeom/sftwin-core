#include <gtest/gtest.h>
#include <memory>
#include <vector>

#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/vision_detection_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_telemetry_subscriber.hpp"
#include "edge_control/contracts/ports/outbound/i_vision_detector.hpp"
#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_dto.hpp"
#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_usecase.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::realtime_telemetry::application;
using namespace sftwin::shared;

class MockTelemetrySubscriber : public ITelemetrySubscriber {
public:
    bool initialized{true};
    TelemetryPacketDto packet_to_return{};

    bool is_initialized() const override { return initialized; }

    TelemetryPacketDto read_latest_packet(const std::string&) override {
        return packet_to_return;
    }
};

class MockVisionDetector : public IVisionDetector {
public:
    std::vector<VisionDetectionDto> detections_to_return{};

    std::vector<VisionDetectionDto> get_latest_detections() override {
        return detections_to_return;
    }
};

class ProcessTelemetryUseCaseTest : public ::testing::Test {
protected:
    std::shared_ptr<MockTelemetrySubscriber> mock_sub;
    std::shared_ptr<MockVisionDetector> mock_vision;
    std::unique_ptr<ProcessTelemetryUseCase> usecase;

    void SetUp() override {
        mock_sub = std::make_shared<MockTelemetrySubscriber>();
        mock_vision = std::make_shared<MockVisionDetector>();
        usecase = std::make_unique<ProcessTelemetryUseCase>(mock_sub, mock_vision);
    }
};

TEST_F(ProcessTelemetryUseCaseTest, ThrowsExceptionWhenDdsNotInitialized) {
    mock_sub->initialized = false;
    ProcessTelemetryRequestDto req{"ROBOT_01"};

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
}

TEST_F(ProcessTelemetryUseCaseTest, ThrowsExceptionWhenTelemetryIsStale) {
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    const uint64_t stale_time_ns = current_time_ns - 200'000'000ULL; // 200ms 전 패킷 (>100ms)

    mock_sub->packet_to_return = TelemetryPacketDto("ROBOT_01", stale_time_ns);
    ProcessTelemetryRequestDto req{"ROBOT_01"};

    EXPECT_THROW(usecase->execute(req), GlobalExceptionHandler);
}

TEST_F(ProcessTelemetryUseCaseTest, SetsWarningFlagWhenVisionObjectDetectedWithinWarningRadius) {
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    mock_sub->packet_to_return = TelemetryPacketDto("ROBOT_01", current_time_ns);

    // 1.0m 거리의 장애물 감지 (경고 반경 1.5m 이내)
    VisionDetectionDto warning_object{"OBSTACLE", 0.95f, 1.0f, {}};
    mock_vision->detections_to_return = {warning_object};

    ProcessTelemetryRequestDto req{"ROBOT_01"};
    const auto result = usecase->execute(req);

    EXPECT_TRUE(result.is_warning());
    EXPECT_EQ(result.device_id(), "ROBOT_01");
}

TEST_F(ProcessTelemetryUseCaseTest, WarningFlagFalseWhenObjectsAreFar) {
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    mock_sub->packet_to_return = TelemetryPacketDto("ROBOT_01", current_time_ns);

    // 2.5m 거리의 장애물 감지 (경고 반경 1.5m 초과)
    VisionDetectionDto safe_object{"OBSTACLE", 0.95f, 2.5f, {}};
    mock_vision->detections_to_return = {safe_object};

    ProcessTelemetryRequestDto req{"ROBOT_01"};
    const auto result = usecase->execute(req);

    EXPECT_FALSE(result.is_warning());
}
