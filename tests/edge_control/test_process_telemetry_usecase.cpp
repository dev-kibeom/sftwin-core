#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <vector>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"
#include "src/edge_control/realtime_telemetry/application/process_telemetry_usecase.hpp"
#include "telemetry_packet.pb.h"

using ::testing::NiceMock;
using ::testing::Return;

using namespace sftwin::edge_control::realtime_telemetry;

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

    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_001");
    // 공통 TimeProvider 사용
    proto.set_timestamp_ns(sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns());
    dtos::TelemetryPacketDto dummy_dto(proto);

    EXPECT_CALL(*mock_sub, read_latest_packet("DOOSAN_M1013_001")).WillOnce(Return(dummy_dto));

    sftwin::telemetry::DetectedObject obj;
    obj.set_class_name("PERSON");
    EXPECT_CALL(*mock_vision, get_latest_detections())
        .WillOnce(Return(std::vector<sftwin::telemetry::DetectedObject>{obj}));

    EXPECT_NO_THROW({
        auto result = usecase->get_latest_telemetry("DOOSAN_M1013_001");
        EXPECT_EQ(result.device_id(), "DOOSAN_M1013_001");
        EXPECT_TRUE(result.get_proto().is_warning());
        EXPECT_EQ(result.get_proto().detected_objects_size(), 1);
    });
}

TEST_F(ProcessTelemetryUseCaseTest, ErrorCase_CommTimeoutThrowsException) {
    EXPECT_CALL(*mock_sub, is_initialized()).WillOnce(Return(true));

    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id("DOOSAN_M1013_001");
    // [FIX] 통신 지연 타임아웃(150ms) 유도
    uint64_t past_time =
        sftwin::edge_control::common::utils::TimeProvider::get_steady_time_ns() - 150'000'000ULL;
    proto.set_timestamp_ns(past_time);
    dtos::TelemetryPacketDto delayed_dto(proto);

    EXPECT_CALL(*mock_sub, read_latest_packet("DOOSAN_M1013_001")).WillOnce(Return(delayed_dto));

    try {
        usecase->get_latest_telemetry("DOOSAN_M1013_001");
        FAIL() << "Expected EdgeSystemException";
    } catch (const sftwin::edge_control::common::exceptions::EdgeSystemException& e) {
        EXPECT_EQ(e.get_error_code(), "ERR_EDGE_COMM_TIMEOUT");
    }
}