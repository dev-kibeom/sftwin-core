#include <rclcpp/rclcpp.hpp>
#include "foxglove_bridge/node/foxglove_bridge_node.hpp"

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<sftwin::plugins::foxglove_bridge::FoxgloveBridgeNode>();
    RCLCPP_INFO(node->get_logger(), "Foxglove Bridge Node has been started.");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
