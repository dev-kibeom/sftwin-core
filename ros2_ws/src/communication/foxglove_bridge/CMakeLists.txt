cmake_minimum_required(VERSION 3.20)
project(foxglove_bridge)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(shared_interfaces QUIET)

include_directories(
  include
)

# Configuration & Parameter Files Install
install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

# Unit Testing Targets
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_infra_setup tests/test_infra_setup.cpp)
  target_link_libraries(test_infra_setup
    rclcpp::rclcpp
    nlohmann_json::nlohmann_json
  )
  if(shared_interfaces_FOUND)
    ament_target_dependencies(test_infra_setup shared_interfaces)
  endif()
endif()

ament_package()
