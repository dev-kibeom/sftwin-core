-- Database Initialization Script (GTS v2.0 Section 5)
CREATE DATABASE IF NOT EXISTS sftwin_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sftwin_db;

-- 1. Global Roles Table
CREATE TABLE IF NOT EXISTS global_roles (
    role_code VARCHAR(32) PRIMARY KEY,
    role_name VARCHAR(64) NOT NULL,
    description VARCHAR(255),
    company_id VARCHAR(36) NOT NULL DEFAULT 'SYSTEM',
    created_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    is_deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. System Configurations Table
CREATE TABLE IF NOT EXISTS system_configs (
    config_key VARCHAR(64) PRIMARY KEY,
    config_value VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    company_id VARCHAR(36) NOT NULL DEFAULT 'SYSTEM',
    created_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    is_deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Audit Logs Table (CDS-Shared v3.0 3.2절)
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR(36) PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(36),
    company_id VARCHAR(36) NOT NULL DEFAULT 'SYSTEM',
    component_name VARCHAR(64) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'INFO',
    target_resource VARCHAR(128),
    details JSON,
    ip_address VARCHAR(45),
    created_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_by VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_audit_logs_trace (trace_id),
    INDEX idx_audit_logs_company (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Seed Global Roles (GTS v2.0 5.2절)
INSERT INTO global_roles (role_code, role_name, description) VALUES
('SYSTEM_ADMIN', 'Platform System Administrator', 'Full system management and configuration rights'),
('FACTORY_MANAGER', 'Factory Manager', 'Access to 3D layouts, KPI reports, and B2B procurement'),
('FIELD_ENGINEER', 'Field OT Engineer', 'Real-time edge control, telemetry, and manual Failsafe authorization'),
('SI_PARTNER', 'SI Integration Partner', 'Access to simulation verification and hardware matching'),
('CREATOR', 'Individual Creator / Startup', 'Access to 3D layout canvas and remote expert consulting')
ON DUPLICATE KEY UPDATE role_name=VALUES(role_name), description=VALUES(description);

-- 5. Seed System Configs (GTS v2.0 5.2절)
INSERT INTO system_configs (config_key, config_value, description) VALUES
('EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS', '100', 'Maximum allowable heartbeat delay before triggering E-Stop'),
('MAX_SIM_CONCURRENT_USERS', '50', 'Maximum concurrent users for 60fps WebGL simulation engine'),
('REALTIME_TELEMETRY_INTERVAL_MS', '100', 'Interval for sending telemetry updates from edge to dashboard')
ON DUPLICATE KEY UPDATE config_value=VALUES(config_value), description=VALUES(description);
