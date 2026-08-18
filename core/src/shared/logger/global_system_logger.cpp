#include "global_system_logger.hpp"

#include <spdlog/sinks/stdout_color_sinks.h>

#include <iostream>

namespace sftwin::shared {

std::shared_ptr<spdlog::logger> GlobalSystemLogger::_async_logger = nullptr;

void GlobalSystemLogger::init() {
    if (_async_logger) return;

    try {
        spdlog::init_thread_pool(8192, 1);

        auto stdout_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        stdout_sink->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [core_system] %v");

        _async_logger = std::make_shared<spdlog::async_logger>(
            "global_async_logger", stdout_sink, spdlog::thread_pool(),
            spdlog::async_overflow_policy::block);

        spdlog::register_logger(_async_logger);
        _async_logger->set_level(spdlog::level::info);
        spdlog::flush_every(std::chrono::seconds(1));
    } catch (const spdlog::spdlog_ex& ex) {
        std::cerr << "Global async logger initialization failed: " << ex.what() << std::endl;
    }
}

std::shared_ptr<spdlog::logger> GlobalSystemLogger::get_logger() {
    if (!_async_logger) {
        init();
    }
    return _async_logger;
}

}  // namespace sftwin::shared
