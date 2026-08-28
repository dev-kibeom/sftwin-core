# File: plugins/fast_api/dependencies/facades.py
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)


def get_digital_twin_command_facade() -> IDigitalTwinCommandFacade:
    """IDigitalTwinCommandFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")


def get_digital_twin_query_facade() -> IDigitalTwinQueryFacade:
    """IDigitalTwinQueryFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")
