#pragma once

#include <cstdint>
#include <string>

namespace sftwin::plugins::foxglove_bridge {

struct FoxgloveChannel {
    uint32_t id{0};
    std::string topic;
    std::string encoding{"cdr"};
    std::string schema_name;
    std::string schema;
};

}  // namespace sftwin::plugins::foxglove_bridge
