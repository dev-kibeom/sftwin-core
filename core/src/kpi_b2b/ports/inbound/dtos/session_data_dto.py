from dataclasses import dataclass


@dataclass(frozen=True)
class SessionDataDto:
    session_id: str
    session_token: str
    status: str
    expires_in_seconds: int
