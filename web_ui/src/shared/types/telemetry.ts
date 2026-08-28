export interface TfTransformDto {
    position: [number, number, number]; // [x, y, z]
    rotation: [number, number, number, number]; // [x, y, z, w] Quaternion
}

export interface TelemetryFrame {
    timestamp: number; // 수신 타임스탬프 (ms)
    jointPositions: Record<string, number>; // joint_name -> radian/meter
    tfTransforms: Record<string, TfTransformDto>;
}

export interface RingBufferMemoryLayout {
    capacity: number; // 기본값: 128 슬롯
    buffer: TelemetryFrame[];
    head: number;
    tail: number;
    size: number;
}
