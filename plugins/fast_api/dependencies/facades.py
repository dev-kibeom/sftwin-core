from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)
from simulation.contracts.ports.inbound.i_simulation_command_facade import (
    ISimulationCommandFacade,
)
from simulation.contracts.ports.inbound.i_simulation_query_facade import (
    ISimulationQueryFacade,
)


def get_digital_twin_command_facade() -> IDigitalTwinCommandFacade:
    """IDigitalTwinCommandFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")


def get_digital_twin_query_facade() -> IDigitalTwinQueryFacade:
    """IDigitalTwinQueryFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")


def get_simulation_command_facade() -> ISimulationCommandFacade:
    """ISimulationCommandFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")


def get_simulation_query_facade() -> ISimulationQueryFacade:
    """ISimulationQueryFacade 인스턴스 주입 팩토리"""
    raise NotImplementedError("Facade instance will be wired at composition root.")
