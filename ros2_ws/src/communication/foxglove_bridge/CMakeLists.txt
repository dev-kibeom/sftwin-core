cmake_minimum_required(VERSION 3.20)
project(foxglove_bridge)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ROS 2 & 빌드 패키지
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(websocketpp REQUIRED)
find_package(Boost REQUIRED COMPONENTS system thread)

# 선택적 의존성: shared_interfaces
find_package(shared_interfaces QUIET)

# 1. Core 라이브러리 소스 정의
set(BRIDGE_SRCS
  src/mappers/foxglove_payload_mapper.cpp
  src/managers/client_session_manager.cpp
  src/managers/dynamic_topic_channel_manager.cpp
  src/server/foxglove_server_wrapper.cpp
  src/node/foxglove_bridge_node.cpp
)

# 2. Core 라이브러리 타깃 생성
add_library(${PROJECT_NAME}_lib STATIC ${BRIDGE_SRCS})

# 3. 헤더 인클루드 경로 지정
target_include_directories(${PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${WEBSOCKETPP_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
)

# 4. ament 의존성 먼저 주입
ament_target_dependencies(${PROJECT_NAME}_lib
  rclcpp
  std_msgs
  nlohmann_json
)

if(shared_interfaces_FOUND)
  ament_target_dependencies(${PROJECT_NAME}_lib shared_interfaces)
endif()

# 5. 서드파티 라이브러리 링크 (PUBLIC 키워드 제거 -> Plain Signature 유지)
target_link_libraries(${PROJECT_NAME}_lib
  ${Boost_LIBRARIES}
  pthread
)

# 6. 실행 바이너리 타깃 생성 및 링크
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
