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

add_library(${PROJECT_NAME}_mappers
  src/mappers/foxglove_payload_mapper.cpp
)
target_link_libraries(${PROJECT_NAME}_mappers
  nlohmann_json::nlohmann_json
)
if(shared_interfaces_FOUND)
  ament_target_dependencies(${PROJECT_NAME}_mappers shared_interfaces)
endif()

add_library(${PROJECT_NAME}_managers
  src/managers/client_session_manager.cpp
)
target_link_libraries(${PROJECT_NAME}_managers
  rclcpp::rclcpp
)

add_library(${PROJECT_NAME}_server
  src/server/foxglove_server_wrapper.cpp
)
target_link_libraries(${PROJECT_NAME}_server
  rclcpp::rclcpp
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  TARGETS ${PROJECT_NAME}_mappers ${PROJECT_NAME}_managers ${PROJECT_NAME}_server
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_infra_setup tests/test_infra_setup.cpp)
  target_link_libraries(test_infra_setup
    rclcpp::rclcpp
    nlohmann_json::nlohmann_json
  )

  ament_add_gtest(test_domain_models tests/test_domain_models.cpp)
  target_link_libraries(test_domain_models
    rclcpp::rclcpp
    nlohmann_json::nlohmann_json
  )

  ament_add_gtest(test_payload_mapper tests/test_payload_mapper.cpp)
  target_link_libraries(test_payload_mapper
    ${PROJECT_NAME}_mappers
    rclcpp::rclcpp
    nlohmann_json::nlohmann_json
  )
  if(shared_interfaces_FOUND)
    ament_target_dependencies(test_payload_mapper shared_interfaces)
  endif()

  ament_add_gtest(test_client_session_manager tests/test_client_session_manager.cpp)
  target_link_libraries(test_client_session_manager
    ${PROJECT_NAME}_managers
    rclcpp::rclcpp
  )

  ament_add_gtest(test_server_wrapper tests/test_server_wrapper.cpp)
  target_link_libraries(test_server_wrapper
    ${PROJECT_NAME}_server
    rclcpp::rclcpp
  )
endif()

ament_package()
