#include "global_system_logger.hpp"

#include <spdlog/sinks/stdout_color_sinks.h>
#include <mutex>
#include <iostream>

namespace sftwin::shared {

static std::once_flag init_flag;
static std::shared_ptr<spdlog::logger> g_global_logger = nullptr;

std::shared_ptr<spdlog::logger> GlobalSystemLogger::get_backend_logger(const std::string& logger_name) {
    std::call_once(init_flag, [&]() {
        try {
            auto stdout_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
            stdout_sink->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v");

            // async_logger 대신 일반 동기 logger 생성 (thread pool 제거)
            g_global_logger = std::make_shared<spdlog::logger>(logger_name, stdout_sink);

            spdlog::register_logger(g_global_logger);
            g_global_logger->set_level(spdlog::level::info);
        } catch (const spdlog::spdlog_ex& ex) {
            std::cerr << "Global logger initialization failed: " << ex.what() << std::endl;
        }
    });

    return g_global_logger;
}

GlobalSystemLogger::GlobalSystemLogger(std::string component_name, std::string logger_name)
    : _component_name(std::move(component_name)),
      _backend_logger(get_backend_logger(logger_name)) {}

}  // namespace sftwin::shared
