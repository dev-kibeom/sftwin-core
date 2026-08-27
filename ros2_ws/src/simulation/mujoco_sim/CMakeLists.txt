cmake_minimum_required(VERSION 3.8)
project(mujoco_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(shared_interfaces REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)

# core/src 경로 설정
set(CORE_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../../core/src")

# 1. 라이브러리 빌드
file(GLOB SOURCES "src/*.cpp")
add_library(mujoco_sim_lib ${SOURCES})

target_include_directories(mujoco_sim_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<BUILD_INTERFACE:${CORE_SRC_DIR}>
  $<BUILD_INTERFACE:/usr/local/include>
  $<INSTALL_INTERFACE:include>
)

target_link_libraries(mujoco_sim_lib
  /usr/local/lib/libmujoco.so
)

# shared_interfaces를 의존성에 등록 (rosidl_get_typesupport_target 대체)
ament_target_dependencies(mujoco_sim_lib
  rclcpp
  sensor_msgs
  shared_interfaces
  tf2
  tf2_ros
)

# 2. 설치 설정
install(TARGETS mujoco_sim_lib
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

# 3. GTest 테스트 타깃 자동 등록
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  file(GLOB TEST_SOURCES "test/test_*.cpp")

  foreach(TEST_SOURCE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME_WE)

    ament_add_gtest(${TEST_NAME} ${TEST_SOURCE})
    target_include_directories(${TEST_NAME} PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/include
      ${CORE_SRC_DIR}
      /usr/local/include
    )
    target_link_libraries(${TEST_NAME}
      mujoco_sim_lib
      /usr/local/lib/libmujoco.so
    )
    ament_target_dependencies(${TEST_NAME}
      rclcpp
      sensor_msgs
      shared_interfaces
      tf2
      tf2_ros
    )
  endforeach()
endif()

ament_package()
