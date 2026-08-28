export interface TfTransformDto {
    position: [number, number, number];
    rotation: [number, number, number, number];
}

export interface TelemetryFrame {
    timestamp: number;
    /**
     * 에셋별 관절 회전각 맵
     * key: assetId (예: 'robot_arm_1', 'agv_1')
     * value: { [jointName: string]: angleInRadians }
     */
    jointPositions: Record<string, Record<string, number>>;
    /**
     * 에셋별 루트/베이스 TF 변환 맵
     * key: assetId
     */
    tfTransforms: Record<string, TfTransformDto>;
}

export interface RingBufferMemoryLayout {
    capacity: number; // 기본값: 128 슬롯
    buffer: TelemetryFrame[];
    head: number;
    tail: number;
    size: number;
}
