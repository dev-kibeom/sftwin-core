# core/edge_control/CMakeLists.txt

# 1. edge_control 내부 소스 및 테스트 탐지
file(GLOB_RECURSE EDGE_SRCS
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
)
list(FILTER EDGE_SRCS EXCLUDE REGEX ".*/tests/.*") # 테스트 소스 제외

file(GLOB_RECURSE EDGE_TEST_SRCS
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp"
)

# 2. edge_control 전용 테스트 바이너리
add_executable(edge_control_tests
    ${EDGE_TEST_SRCS}
    ${EDGE_SRCS}
)

# 3. 인클루드 경로 지정 (프로젝트 루트 기준)
target_include_directories(edge_control_tests PRIVATE
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/src
)

# 4. 링킹
target_link_libraries(edge_control_tests PRIVATE
    GTest::gtest
    GTest::gtest_main
    GMock::gmock
    spdlog::spdlog
    fmt::fmt
)

gtest_discover_tests(edge_control_tests)
