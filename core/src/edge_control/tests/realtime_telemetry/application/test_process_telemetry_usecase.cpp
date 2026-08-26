#include <gtest/gtest.h>
#include <memory>
#include <vector>

#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/vision_detection_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_telemetry_subscriber.hpp"
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

class ProcessTelemetryUseCaseTest : public ::testing::Test {
protected:
    std::shared_ptr<MockTelemetrySubscriber> mock_sub;
    std::unique_ptr<ProcessTelemetryUseCase> usecase;

    void SetUp() override {
        mock_sub = std::make_shared<MockTelemetrySubscriber>();
        usecase = std::make_unique<ProcessTelemetryUseCase>(mock_sub);
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
