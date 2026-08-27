#include <gtest/gtest.h>
#include <nlohmann/json.hpp>
#include <stdexcept>

#include "foxglove_bridge/domain/foxglove_enums.hpp"
#include "foxglove_bridge/mappers/foxglove_payload_mapper.hpp"

using namespace sftwin::plugins::foxglove_bridge;

class FoxglovePayloadMapperTest : public ::testing::Test {
protected:
    FoxglovePayloadMapper mapper;
};

// 시나리오 1: ROS 2 메시지 타입의 Foxglove 채널 스키마 변환 검증 (Happy Path)
TEST_F(FoxglovePayloadMapperTest, ConvertTopicTypeToChannelSchemaSuccessfully) {
    std::string topic_type = "sensor_msgs/msg/JointState";

    auto schema_info = mapper.to_channel_schema(topic_type);

    EXPECT_EQ(schema_info.schema_name, "sensor_msgs/msg/JointState");
    EXPECT_EQ(schema_info.encoding, "cdr");
}

// 시나리오 2: 웹 클라이언트 E-Stop JSON 명령의 FailsafeCommand 변환 검증 (Happy Path)
TEST_F(FoxglovePayloadMapperTest, ConvertValidEstopJsonToFailsafeCommand) {
    std::string client_json = R"({
        "action": "ESTOP",
        "target": "ROBOT_ARM_01",
        "reason": "WEB_UI_BUTTON"
    })";

    auto failsafe_cmd = mapper.to_failsafe_command(client_json);

    EXPECT_EQ(failsafe_cmd.action_type, "ESTOP");
    EXPECT_EQ(failsafe_cmd.target_device_id, "ROBOT_ARM_01");
    EXPECT_EQ(failsafe_cmd.trigger_reason, "WEB_UI_BUTTON");
    EXPECT_GT(failsafe_cmd.issued_timestamp_ns, 0ULL);
}

// 시나리오 3: 비정상 JSON 명령 인입 시 예외 발생 검증 (Edge Case)
TEST_F(FoxglovePayloadMapperTest, ThrowExceptionOnInvalidJsonPayload) {
    std::string malformed_json = "{ action: ESTOP ";

    EXPECT_THROW({
        mapper.to_failsafe_command(malformed_json);
    }, std::invalid_argument);

    std::string missing_field_json = R"({
        "reason": "NO_ACTION_SPECIFIED"
    })";

    EXPECT_THROW({
        mapper.to_failsafe_command(missing_field_json);
    }, std::invalid_argument);
}
