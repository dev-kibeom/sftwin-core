#pragma once
#include <cstdint>

namespace sftwin::ipc {

#pragma pack(push, 1)

struct ShmDetectedObject {
    float confidence;
    float bbox[4];       // [x_min, y_min, width, height]
    char class_name[32];
};

struct ShmTelemetryPacket {
    // 동기화 및 무결성 검증을 위한 Sequence Lock 카운터
    uint64_t sequence_number;
    int64_t timestamp_ns;

    // edge_control DTO와 일치하도록 float 배열 정렬
    float joint_positions[12];
    float joint_torques[12];
    float anomaly_score;

    char device_id[64];
    char packml_state[16];

    uint8_t joint_count;
    uint8_t detected_object_count;
    bool is_warning;
    bool has_anomaly_score;

    ShmDetectedObject detected_objects[10];
};

#pragma pack(pop)

} // namespace sftwin::ipc
