// core/shared/ipc/shm_telemetry_dto.hpp
#pragma once
#include <cstdint>

namespace sftwin::ipc {

#pragma pack(push, 1) // Memory Alignment 오버헤드 차단

struct ShmDetectedObject {
    char class_name[32]; // 동적 string 대신 고정 char 배열
    float confidence;
    float bbox[4];       // [x_min, y_min, width, height]
};

struct ShmTelemetryPacket {
    char device_id[64];
    int64_t timestamp_ns;

    uint8_t joint_count;
    double joint_positions[12]; // 로봇 arm + AMR 휠 최대 12축 고정
    double joint_torques[12];

    char packml_state[16];
    bool is_warning;

    uint8_t detected_object_count;
    ShmDetectedObject detected_objects[10]; // 최대 10개 제한으로 Memory Leak 차단

    float anomaly_score;
    bool has_anomaly_score;
};

#pragma pack(pop)

} // namespace sftwin::ipc
