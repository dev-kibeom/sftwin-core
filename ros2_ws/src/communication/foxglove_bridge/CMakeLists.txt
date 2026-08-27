cmake_minimum_required(VERSION 3.20)
project(foxglove_bridge)

# C++20 표준 준수
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 20)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nlohmann_json REQUIRED)

# 선택적 의존성: shared_interfaces
find_package(shared_interfaces QUIET)

# 헤더 경로 포함
include_directories(
  include
)

# Core 라이브러리
set(BRIDGE_SRCS
  src/mappers/foxglove_payload_mapper.cpp
  src/managers/client_session_manager.cpp
  src/managers/dynamic_topic_channel_manager.cpp
  src/server/foxglove_server_wrapper.cpp
  src/node/foxglove_bridge_node.cpp
)

add_library(${PROJECT_NAME}_lib STATIC ${BRIDGE_SRCS})
ament_target_dependencies(${PROJECT_NAME}_lib
  rclcpp
  std_msgs
  nlohmann_json
)
if(shared_interfaces_FOUND)
  ament_target_dependencies(${PROJECT_NAME}_lib shared_interfaces)
endif()

# 실행 바이너리 타깃
add_executable(${PROJECT_NAME}_node_exec src/main.cpp)
target_link_libraries(${PROJECT_NAME}_node_exec ${PROJECT_NAME}_lib)
ament_target_dependencies(${PROJECT_NAME}_node_exec rclcpp)

# 배포 설정
install(TARGETS
  ${PROJECT_NAME}_lib
  ${PROJECT_NAME}_node_exec
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include/
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# 테스트 빌드 설정 (TDD)
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)

  # C++ GTest 목록 등록
  ament_add_gtest(test_client_session_manager tests/test_client_session_manager.cpp)
  target_link_libraries(test_client_session_manager ${PROJECT_NAME}_lib)

  ament_add_gtest(test_domain_models tests/test_domain_models.cpp)
  target_link_libraries(test_domain_models ${PROJECT_NAME}_lib)

  ament_add_gtest(test_payload_mapper tests/test_payload_mapper.cpp)
  target_link_libraries(test_payload_mapper ${PROJECT_NAME}_lib)

  ament_add_gtest(test_server_wrapper tests/test_server_wrapper.cpp)
  target_link_libraries(test_server_wrapper ${PROJECT_NAME}_lib)

  ament_add_gtest(test_dynamic_topic_channel_manager tests/test_dynamic_topic_channel_manager.cpp)
  target_link_libraries(test_dynamic_topic_channel_manager ${PROJECT_NAME}_lib)

  ament_add_gtest(test_bridge_node tests/test_bridge_node.cpp)
  target_link_libraries(test_bridge_node ${PROJECT_NAME}_lib)

  ament_add_gtest(test_infra_setup tests/test_infra_setup.cpp)
  target_link_libraries(test_infra_setup ${PROJECT_NAME}_lib)

  # 신규 특화 통합 테스트
  ament_add_gtest(test_dynamic_pipeline_integration tests/test_dynamic_pipeline_integration.cpp)
  target_link_libraries(test_dynamic_pipeline_integration ${PROJECT_NAME}_lib)

  # Launch 패키징 테스트
  ament_add_pytest_test(test_launch_packaging tests/test_launch_packaging.py)
endif()

ament_package()
