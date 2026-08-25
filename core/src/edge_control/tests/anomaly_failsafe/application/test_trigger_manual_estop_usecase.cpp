#include <gtest/gtest.h>
#include <memory>
#include "edge_control/anomaly_failsafe/application/trigger_manual_estop/trigger_manual_estop_usecase.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

using namespace sftwin::edge_control;
using namespace sftwin::edge_control::anomaly_failsafe::application;
using namespace sftwin::edge_control::anomaly_failsafe::domain;
using namespace sftwin::shared;

class MockFailsafePublisher : public IFailsafePublisher {
public:
    int publish_count{0};
    void publish(const std::string&, const FailsafeCommandDto&) override { publish_count++; }
};

class MockHardwareInterlock : public IHardwareInterlock {
public:
    int trigger_count{0};
    int release_count{0};
    InterlockState current_state{InterlockState::RELEASED};

    void trigger_physical_relay() override {
        trigger_count++;
        current_state = InterlockState::ENGAGED;
    }

    void release_interlock(const std::string& /* operator_approval_token */) override {
        release_count++;
        current_state = InterlockState::RELEASED;
    }

    [[nodiscard]] InterlockState get_state() const override {
        return current_state;
    }
};

TEST(TriggerManualEstopUseCaseTest, ManualEstopSuccess) {
    auto interlock_mgr = std::make_shared<InterlockManager>();
    auto mock_hw = std::make_shared<MockHardwareInterlock>();
    auto mock_pub = std::make_shared<MockFailsafePublisher>();

    TriggerManualEstopUseCase usecase{interlock_mgr, mock_hw, mock_pub};
    usecase.execute(TriggerManualEstopRequestDto{"Emergency Button Pressed", "ROBOT_01"});

    EXPECT_EQ(interlock_mgr->state(), InterlockState::ENGAGED);
    EXPECT_EQ(mock_hw->trigger_count, 1);
    EXPECT_EQ(mock_pub->publish_count, 1);
}

TEST(TriggerManualEstopUseCaseTest, ThrowsExceptionIfAlreadyEngaged) {
    auto interlock_mgr = std::make_shared<InterlockManager>(InterlockState::ENGAGED);
    auto mock_hw = std::make_shared<MockHardwareInterlock>();
    auto mock_pub = std::make_shared<MockFailsafePublisher>();

    TriggerManualEstopUseCase usecase{interlock_mgr, mock_hw, mock_pub};
    EXPECT_THROW(usecase.execute(TriggerManualEstopRequestDto{"Button"}), GlobalExceptionHandler);
}
