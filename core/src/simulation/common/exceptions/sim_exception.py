class SimulationException(Exception):
    """simulation 서브도메인 전용 도메인 예외"""

    def __init__(self, error_code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
