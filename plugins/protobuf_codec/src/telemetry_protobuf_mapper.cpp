#include "plugins/protobuf_codec/include/telemetry_protobuf_mapper.hpp"

namespace sftwin::plugins::protobuf_codec {

sftwin::edge_control::TelemetryPacketDto TelemetryProtobufMapper::to_core_dto(
    const sftwin::telemetry::TelemetryPacketProto& proto) {

    std::vector<float> positions(proto.joint_positions().begin(), proto.joint_positions().end());
    std::vector<float> torques(proto.joint_torques().begin(), proto.joint_torques().end());

    sftwin::edge_control::TelemetryPacketDto dto(
        proto.device_id(),
        static_cast<uint64_t>(proto.timestamp_ns()),
        std::move(positions),
        std::move(torques),
        proto.has_anomaly_score() ? proto.anomaly_score() : 0.0f
    );
    dto.set_warning(proto.is_warning());
    return dto;
}

sftwin::telemetry::TelemetryPacketProto TelemetryProtobufMapper::to_protobuf(
    const sftwin::edge_control::TelemetryPacketDto& dto) {

    sftwin::telemetry::TelemetryPacketProto proto;
    proto.set_device_id(dto.device_id());
    proto.set_timestamp_ns(static_cast<int64_t>(dto.timestamp_ns()));
    proto.set_is_warning(dto.is_warning());
    proto.set_anomaly_score(dto.anomaly_score());

    for (const float pos : dto.joint_positions()) {
        proto.add_joint_positions(pos);
    }
    for (const float torque : dto.joint_torques()) {
        proto.add_joint_torques(torque);
    }

    return proto;
}

}  // namespace sftwin::plugins::protobuf_codec
