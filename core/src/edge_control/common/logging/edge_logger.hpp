#pragma once
#include <spdlog/async.h>
#include <spdlog/spdlog.h>

#include <memory>

namespace sftwin::edge_control::common::logging {

/**
 * @brief 100ms 결정론적 제어를 보장하기 위한 비동기(Async) 로거 싱글톤 래퍼
 * 메인 제어 스레드를 블로킹하지 않고 백그라운드 스레드 풀에 로깅을 위임합니다.
 */
class EdgeLogger {
   private:
    static std::shared_ptr<spdlog::logger> _async_logger;

   public:
    static void init();
    static std::shared_ptr<spdlog::logger> get_logger();
};

}  // namespace sftwin::edge_control::common::logging

// 사용 편의성을 위한 전역 매크로 정의 (컴파일 타임에 소스코드 위치까지 확장 가능)
#define EDGE_LOG_INFO(...) \
    SPDLOG_LOGGER_INFO(sftwin::edge_control::common::logging::EdgeLogger::get_logger(), __VA_ARGS__)
#define EDGE_LOG_WARN(...) \
    SPDLOG_LOGGER_WARN(sftwin::edge_control::common::logging::EdgeLogger::get_logger(), __VA_ARGS__)
#define EDGE_LOG_ERROR(...)                                                              \
    SPDLOG_LOGGER_ERROR(sftwin::edge_control::common::logging::EdgeLogger::get_logger(), \
                        __VA_ARGS__)
