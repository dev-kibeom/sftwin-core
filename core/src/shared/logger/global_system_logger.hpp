#pragma once

#include <spdlog/spdlog.h>
#include <memory>
#include <string>
#include <utility>

namespace sftwin::shared {

class GlobalSystemLogger {
public:
    explicit GlobalSystemLogger(
        std::string component_name = "SharedComponent",
        std::string logger_name = "sftwin.global"
    );

    template <typename FormatString, typename... Args>
    void info(const FormatString &fmt, Args &&...args) const {
        _log(spdlog::level::info, fmt, std::forward<Args>(args)...);
    }

    template <typename FormatString, typename... Args>
    void warn(const FormatString &fmt, Args &&...args) const {
        _log(spdlog::level::warn, fmt, std::forward<Args>(args)...);
    }

    template <typename FormatString, typename... Args>
    void debug(const FormatString &fmt, Args &&...args) const {
        _log(spdlog::level::debug, fmt, std::forward<Args>(args)...);
    }

    template <typename FormatString, typename... Args>
    void error(const FormatString &fmt, Args &&...args) const {
        _log(spdlog::level::err, fmt, std::forward<Args>(args)...);
    }

    static std::shared_ptr<spdlog::logger> get_backend_logger(const std::string& logger_name = "sftwin.global");

private:
    std::string _component_name;
    std::shared_ptr<spdlog::logger> _backend_logger;

    template <typename FormatString, typename... Args>
    void _log(spdlog::level::level_enum level, const FormatString &fmt, Args &&...args) const {
        if (!_backend_logger || !_backend_logger->should_log(level)) {
            return;
        }
        std::string formatted_msg = fmt::format(fmt, std::forward<Args>(args)...);
        _backend_logger->log(level, "[{}] {}", _component_name, formatted_msg);
    }
};

}  // namespace sftwin::shared
