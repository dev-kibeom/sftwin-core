// core/src/shared/utils/so_plugin_loader.hpp
#pragma once

#include <dlfcn.h>
#include <iostream>
#include <memory>
#include <string>

namespace sftwin::shared::utils {

template <typename InterfaceType>
class SoPluginLoader {
   private:
    void* handle_ = nullptr;
    using CreateInterfaceFunc = InterfaceType* (*)();

   public:
    ~SoPluginLoader() {
        if (handle_) {
            dlclose(handle_);
        }
    }

    std::unique_ptr<InterfaceType> load_plugin(const std::string& so_path, const std::string& factory_func_name) {
        handle_ = dlopen(so_path.c_str(), RTLD_LAZY);
        if (!handle_) {
            std::cerr << "Failed to load SO library: " << dlerror() << std::endl;
            return nullptr;
        }

        dlerror(); // Clear existing errors
        auto create_func = reinterpret_cast<CreateInterfaceFunc>(dlsym(handle_, factory_func_name.c_str()));

        const char* dlsym_error = dlerror();
        if (dlsym_error) {
            std::cerr << "Failed to find symbol: " << dlsym_error << std::endl;
            dlclose(handle_);
            handle_ = nullptr;
            return nullptr;
        }

        return std::unique_ptr<InterfaceType>(create_func());
    }
};

} // namespace sftwin::shared::utils
