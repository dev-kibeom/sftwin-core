cmake_minimum_required(VERSION 3.14)
project(sftwin_protobuf_codec CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ------------------------------------------------------------------------------
# 1. Protobuf 패키지 검색
# ------------------------------------------------------------------------------
find_package(Protobuf REQUIRED)

# ------------------------------------------------------------------------------
# 2. Proto 파일 탐지 및 C++ / Python 스텁 생성
# ------------------------------------------------------------------------------
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_SOURCE_DIR}/proto/*.proto")

set(PROTO_SRCS)
set(PROTO_HDRS)

# C++ 생성 파일 출력 디렉터리
set(PROTO_CPP_OUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cpp_gen")
# Python 생성 파일 출력 디렉터리
set(PROTO_PY_OUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python_gen")

file(MAKE_DIRECTORY ${PROTO_CPP_OUT_DIR})
file(MAKE_DIRECTORY ${PROTO_PY_OUT_DIR})

foreach(PROTO_FILE ${PROTO_FILES})
    get_filename_component(PROTO_NAME ${PROTO_FILE} NAME_WE)

    set(PROTO_SRC "${PROTO_CPP_OUT_DIR}/${PROTO_NAME}.pb.cc")
    set(PROTO_HDR "${PROTO_CPP_OUT_DIR}/${PROTO_NAME}.pb.h")

    add_custom_command(
        OUTPUT ${PROTO_SRC} ${PROTO_HDR}
        COMMAND ${Protobuf_PROTOC_EXECUTABLE}
        ARGS --experimental_allow_proto3_optional
             --cpp_out=${PROTO_CPP_OUT_DIR}
             --python_out=${PROTO_PY_OUT_DIR}
             -I${CMAKE_CURRENT_SOURCE_DIR}/proto
             ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Generating Protobuf C++ & Python stubs for ${PROTO_NAME}.proto"
        VERBATIM
    )

    list(APPEND PROTO_SRCS ${PROTO_SRC})
    list(APPEND PROTO_HDRS ${PROTO_HDR})
endforeach()

# ------------------------------------------------------------------------------
# 3. Protobuf Codec 플러그인 타겟 라이브러리 빌드
# ------------------------------------------------------------------------------
# Mapper 구현체 소스 스캔 (src 디렉토리 한정)
file(GLOB MAPPER_SRCS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

add_library(sftwin_protobuf_codec STATIC
    ${PROTO_SRCS}
    ${PROTO_HDRS}
    ${MAPPER_SRCS}
)

# .so(pybind) 모듈에 정적 링크를 위한 PIC 속성 활성화
set_target_properties(sftwin_protobuf_codec PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

target_include_directories(sftwin_protobuf_codec PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROTO_CPP_OUT_DIR}
    ${CMAKE_SOURCE_DIR}/core
    ${CMAKE_SOURCE_DIR}/core/src  # core DTO 및 shared 헤더 참조용
)

target_link_libraries(sftwin_protobuf_codec PUBLIC
    ${PROTOBUF_LIBRARIES}
)
