#pragma once

#include <spdlog/async.h>
#include <spdlog/spdlog.h>

#include <memory>

namespace sftwin::shared {

class GlobalSystemLogger {
   public:
    static void init();
    static std::shared_ptr<spdlog::logger> get_logger();

   private:
    static std::shared_ptr<spdlog::logger> _async_logger;
};

}  // namespace sftwin::shared

#define GLOBAL_LOG_INFO(...) \
    SPDLOG_LOGGER_INFO(sftwin::shared::GlobalSystemLogger::get_logger(), __VA_ARGS__)
#define GLOBAL_LOG_WARN(...) \
    SPDLOG_LOGGER_WARN(sftwin::shared::GlobalSystemLogger::get_logger(), __VA_ARGS__)
#define GLOBAL_LOG_DEBUG(...) \
    SPDLOG_LOGGER_DEBUG(sftwin::shared::GlobalSystemLogger::get_logger(), __VA_ARGS__)
#define GLOBAL_LOG_ERROR(...) \
    SPDLOG_LOGGER_ERROR(sftwin::shared::GlobalSystemLogger::get_logger(), __VA_ARGS__)
