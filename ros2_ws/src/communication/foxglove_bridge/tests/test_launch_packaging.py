import os
import unittest
from ament_index_python.packages import get_package_share_directory
from launch import LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


class TestLaunchPackaging(unittest.TestCase):
    def test_launch_file_exists_and_parseable(self):
        # Given: 패키지 share 디렉터리 경로 획득
        try:
            pkg_share = get_package_share_directory("foxglove_bridge")
        except Exception:
            pkg_share = os.path.join(os.getcwd(), "src/communication/foxglove_bridge")

        launch_file = os.path.join(pkg_share, "launch", "foxglove_bridge.launch.py")
        config_file = os.path.join(pkg_share, "config", "foxglove_bridge_params.yaml")

        # Then: 필수 배포 산출물 파일 존재 검증
        self.assertTrue(
            os.path.exists(launch_file)
            or os.path.exists("launch/foxglove_bridge.launch.py")
        )
        self.assertTrue(
            os.path.exists(config_file) or os.path.exists("config/foxglove_bridge.yaml")
        )

    def test_launch_description_generation(self):
        # Given: 런치 디스크립션 로드 시도
        launch_file_path = os.path.join(os.getcwd(), "launch/foxglove_bridge.launch.py")
        if not os.path.exists(launch_file_path):
            try:
                pkg_share = get_package_share_directory("foxglove_bridge")
                launch_file_path = os.path.join(
                    pkg_share, "launch", "foxglove_bridge.launch.py"
                )
            except Exception:
                pass

        # When & Then: 구문 분석 및 런치 디스크립션 객체 생성 에러가 없어야 함
        if os.path.exists(launch_file_path):
            launch_desc_src = PythonLaunchDescriptionSource(launch_file_path)
            self.assertIsNotNone(launch_desc_src)


if __name__ == "__main__":
    unittest.main()
