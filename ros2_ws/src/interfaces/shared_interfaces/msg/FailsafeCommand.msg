# 대상 설비/로봇 식별자 (예: "ROBOT_ARM_01", "AMR_01", "ALL")
string target_device_id

# 안전 조치 유형 ("ESTOP", "PAUSE", "BYPASS", "RESUME")
string action_type

# 비상 정지 및 조치 유발 사유 (예: "CORE_FAILSAFE_TRIGGERED", "CRITICAL_INTRUSION", "TORQUE_EXCEEDED")
string trigger_reason

# 발행 시점 타임스탬프 (Nanoseconds)
uint64 issued_timestamp_ns
