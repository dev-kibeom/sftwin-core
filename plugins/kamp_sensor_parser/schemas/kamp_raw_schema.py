from pydantic import BaseModel, ConfigDict, Field


class KampRawRecordSchema(BaseModel):
    """KAMP 시계열 원시 센서 레코드 검증 스키마 (Immutability 보장)"""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    sequence_idx: int = Field(..., alias="idx", description="시퀀스 인덱스")
    time_sec: float = Field(..., alias="time", description="시간(초)")
    x_actual_position: float = Field(
        ..., alias="X_ActualPosition", description="X축 실측 위치"
    )
    y_actual_position: float = Field(
        ..., alias="Y_ActualPosition", description="Y축 실측 위치"
    )
    z_actual_position: float = Field(
        ..., alias="Z_ActualPosition", description="Z축 실측 위치"
    )
    s_actual_position: float = Field(
        ..., alias="S_ActualPosition", description="스핀들 실측 위치"
    )
    x_current_feedback: float = Field(
        ..., alias="X_CurrentFeedback", description="X축 전류 피드백"
    )
    y_current_feedback: float = Field(
        ..., alias="Y_CurrentFeedback", description="Y축 전류 피드백"
    )
    z_current_feedback: float = Field(
        ..., alias="Z_CurrentFeedback", description="Z축 전류 피드백"
    )
    s_current_feedback: float = Field(
        ..., alias="S_CurrentFeedback", description="스핀들 전류 피드백"
    )
    s_output_power: float = Field(
        ..., alias="S_OutputPower", description="스핀들 출력 파워"
    )
    feedrate: float = Field(..., alias="ActualFeedrate", description="실제 이송 속도")
