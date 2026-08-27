cmake_minimum_required(VERSION 3.8)
project(shared_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)

# 1. 인터페이스 코드 생성
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TrajectoryPoint.msg"
  "msg/FailsafeCommand.msg"
  "srv/SimulateScenario.srv"
  DEPENDENCIES
    geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)

# 2. 테스트 설정
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  # 동일 패키지 내 생성된 C++ 타입서포트 타깃 가져오기
  rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")

  # test 또는 tests 폴더의 모든 test_*.cpp 자동 등록
  file(GLOB TEST_SOURCES "tests/test_*.cpp" "test/test_*.cpp")

  foreach(TEST_SOURCE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME_WE)

    ament_add_gtest(${TEST_NAME} ${TEST_SOURCE})

    # 생성된 인터페이스 헤더 include 경로 및 타입서포트 라이브러리 링크
    target_link_libraries(${TEST_NAME} "${cpp_typesupport_target}")
    ament_target_dependencies(${TEST_NAME} geometry_msgs)
  endforeach()
endif()

ament_package()
