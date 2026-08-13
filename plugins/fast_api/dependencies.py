"""
===============================================================================
[File Name] dependencies.py
[Location ] /plugins/fast_api/dependencies.py
[Description]
 - FastAPI Router에서 필요한 core UseCase 및 Facade 객체를 제공하는 Dependency Injector입니다.
===============================================================================
"""

from core.src.asset_twin.asset_library.application.manage_asset.manage_asset_usecase import (
    ManageAssetUseCase,
)
from core.src.asset_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from core.src.asset_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)


# TODO(Global-Container): 최상위 sftwin_project/dependencies.py 연결
# 현재는 점진적 빌드를 위한 Factory Stub 구조
def get_reconstruct_twin_usecase() -> ReconstructTwinUseCase:
    """
    [DI] ReconstructTwinUseCase 객체 생성 및 제공
    """
    # 글로벌 컨테이너 완성 시 container.get_reconstruct_twin_usecase()로 대체
    return ReconstructTwinUseCase(
        sensor_log_parser_port=None,  # type: ignore
        command_repository=None,  # type: ignore
    )


def get_get_layout_usecase() -> GetLayoutUseCase:
    """
    [DI] GetLayoutUseCase 객체 생성 및 제공
    """
    return GetLayoutUseCase(query_repository=None)  # type: ignore


def get_manage_asset_usecase() -> ManageAssetUseCase:
    """
    [DI] ManageAssetUseCase 객체 생성 및 제공
    """
    return ManageAssetUseCase(command_repository=None)  # type: ignore
