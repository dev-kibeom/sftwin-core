#include "edge_logger.hpp"

#include <spdlog/sinks/stdout_color_sinks.h>

#include <iostream>

namespace sftwin::edge_control::common::logging {

std::shared_ptr<spdlog::logger> EdgeLogger::_async_logger = nullptr;

void EdgeLogger::init() {
    if (_async_logger) return;

    try {
        // 8192개의 큐 슬롯을 가진 백그라운드 스레드 1개 생성
        spdlog::init_thread_pool(8192, 1);

        auto stdout_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        // GTS 4.2절 표준 포맷 지정 (TraceID, Timestamp, Level, Component, Message)
        stdout_sink->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [edge_core] %v");

        _async_logger = std::make_shared<spdlog::async_logger>(
            "edge_async_logger", stdout_sink, spdlog::thread_pool(),
            spdlog::async_overflow_policy::block);

        spdlog::register_logger(_async_logger);
        _async_logger->set_level(spdlog::level::info);
        spdlog::flush_every(std::chrono::seconds(1));  // 1초 주기로 잔여 로그 강제 플러시
    } catch (const spdlog::spdlog_ex& ex) {
        std::cerr << "Async logger initialization failed: " << ex.what() << std::endl;
    }
}

std::shared_ptr<spdlog::logger> EdgeLogger::get_logger() {
    if (!_async_logger) {
        init();  // 지연 초기화 (Lazy Initialization)
    }
    return _async_logger;
}

}  // namespace sftwin::edge_control::common::logging