#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <vector>

#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"
#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/vision_detection_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_telemetry_subscriber.hpp"
#include "edge_control/contracts/ports/outbound/i_vision_detector.hpp"
#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_usecase.hpp"

using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::shared;
using namespace sftwin::edge_control;
using namespace sftwin::edge_control::realtime_telemetry;

class MockTelemetrySubscriber : public ITelemetrySubscriber {
   public:
    MOCK_METHOD(bool, is_initialized, (), (const, override));
    MOCK_METHOD(TelemetryPacketDto, read_latest_packet, (const std::string&), (override));
};

class MockVisionDetector : public IVisionDetector {
   public:
    MOCK_METHOD(std::vector<VisionDetectionDto>, get_latest_detections, (), (override));
};

class ProcessTelemetryUseCaseTest : public ::testing::Test {
   protected:
    std::shared_ptr<MockTelemetrySubscriber> mock_sub;
    std::shared_ptr<MockVisionDetector> mock_vision;
    std::unique_ptr<application::ProcessTelemetryUseCase> usecase;

    void SetUp() override {
        mock_sub = std::make_shared<NiceMock<MockTelemetrySubscriber>>();
        mock_vision = std::make_shared<NiceMock<MockVisionDetector>>();
        usecase = std::make_unique<application::ProcessTelemetryUseCase>(mock_sub, mock_vision);
    }
};

TEST_F(ProcessTelemetryUseCaseTest, HappyPath_SuccessWithin100ms) {
    EXPECT_CALL(*mock_sub, is_initialized()).WillOnce(Return(true));

    const uint64_t current_time = GlobalTimeProvider::get_steady_time_ns();
    const TelemetryPacketDto dummy_dto("DOOSAN_M1013_001", current_time, {0.1f, 0.2f}, {10.0f, 20.0f});

    EXPECT_CALL(*mock_sub, read_latest_packet("DOOSAN_M1013_001")).WillOnce(Return(dummy_dto));

    const VisionDetectionDto vision_dto{"PERSON", 0.95f, {0.0f, 0.0f, 1.0f, 1.0f}, current_time};
    EXPECT_CALL(*mock_vision, get_latest_detections())
        .WillOnce(Return(std::vector<VisionDetectionDto>{vision_dto}));

    EXPECT_NO_THROW({
        auto result = usecase->get_latest_telemetry("DOOSAN_M1013_001");
        EXPECT_EQ(result.device_id(), "DOOSAN_M1013_001");
        EXPECT_EQ(result.timestamp_ns(), current_time);
    });
}

TEST_F(ProcessTelemetryUseCaseTest, ErrorCase_CommTimeoutThrowsException) {
    EXPECT_CALL(*mock_sub, is_initialized()).WillOnce(Return(true));

    const uint64_t past_time = GlobalTimeProvider::get_steady_time_ns() - 150'000'000ULL;
    const TelemetryPacketDto delayed_dto("DOOSAN_M1013_001", past_time);

    EXPECT_CALL(*mock_sub, read_latest_packet("DOOSAN_M1013_001")).WillOnce(Return(delayed_dto));

    try {
        usecase->get_latest_telemetry("DOOSAN_M1013_001");
        FAIL() << "Expected GlobalExceptionHandler";
    } catch (const GlobalExceptionHandler& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_COMM_TIMEOUT");
    }
}
