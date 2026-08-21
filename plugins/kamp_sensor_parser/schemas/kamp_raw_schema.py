from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class KampRawRecordSchema(BaseModel):
    """KAMP 시계열 원시 센서 레코드 검증 스키마 (표준 헤더 및 KAMP 실측 헤더 완벽 호환)"""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    sequence_idx: int = Field(
        default=0,
        validation_alias=AliasChoices("idx", "M_sequence_number"),
        description="시퀀스 인덱스",
    )
    time_sec: float = Field(
        default=0.0,
        validation_alias=AliasChoices("time", "Time"),
        description="시간(초)",
    )
    x_actual_position: float = Field(
        ...,
        validation_alias=AliasChoices("X_ActualPosition", "x_actual_position"),
        description="X축 실측 위치",
    )
    y_actual_position: float = Field(
        ...,
        validation_alias=AliasChoices("Y_ActualPosition", "y_actual_position"),
        description="Y축 실측 위치",
    )
    z_actual_position: float = Field(
        ...,
        validation_alias=AliasChoices("Z_ActualPosition", "z_actual_position"),
        description="Z축 실측 위치",
    )
    s_actual_position: float = Field(
        ...,
        validation_alias=AliasChoices("S_ActualPosition", "s_actual_position"),
        description="스핀들 실측 위치",
    )
    x_current_feedback: float = Field(
        ...,
        validation_alias=AliasChoices("X_CurrentFeedback", "x_current_feedback"),
        description="X축 전류 피드백",
    )
    y_current_feedback: float = Field(
        ...,
        validation_alias=AliasChoices("Y_CurrentFeedback", "y_current_feedback"),
        description="Y축 전류 피드백",
    )
    z_current_feedback: float = Field(
        ...,
        validation_alias=AliasChoices("Z_CurrentFeedback", "z_current_feedback"),
        description="Z축 전류 피드백",
    )
    s_current_feedback: float = Field(
        ...,
        validation_alias=AliasChoices("S_CurrentFeedback", "s_current_feedback"),
        description="스핀들 전류 피드백",
    )
    s_output_power: float = Field(
        ...,
        validation_alias=AliasChoices("S_OutputPower", "s_output_power"),
        description="스핀들 출력 파워",
    )
    feedrate: float = Field(
        ...,
        validation_alias=AliasChoices(
            "ActualFeedrate", "M_CURRENT_FEEDRATE", "feedrate"
        ),
        description="실제 이송 속도",
    )
