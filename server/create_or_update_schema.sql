CREATE TABLE IF NOT EXISTS builds (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    branch TEXT NOT NULL,
    state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL,
    INDEX idx1 (state)
);
CREATE TABLE IF NOT EXISTS logs (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    build_id INT UNSIGNED NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity ENUM ('FATAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE') NOT NULL,
    message LONGTEXT COMPRESSED NOT NULL,
    INDEX (build_id),
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);