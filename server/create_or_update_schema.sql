DELIMITER //

CREATE TABLE IF NOT EXISTS settings (
  name VARCHAR(32) PRIMARY KEY,
  value TINYTEXT NOT NULL
);

INSERT IGNORE settings (name, value)
VALUE
  ("log_level", "TRACE");

CREATE TABLE IF NOT EXISTS log_level (
  severity VARCHAR(5) PRIMARY KEY,
  rank TINYINT UNSIGNED NOT NULL
);

INSERT IGNORE log_level (severity, rank)
VALUE
  ('FATAL', 1),
  ('ERROR', 2),
  ('WARN', 3),
  ('INFO', 4),
  ('DEBUG', 5),
  ('TRACE', 6);

CREATE TABLE IF NOT EXISTS builds (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    integration BOOL NOT NULL,
    remote_url TEXT NOT NULL,
    source_branch TEXT NOT NULL,
    target_branch TEXT NOT NULL,
    build_script TEXT NOT NULL,
    work_dir TEXT NOT NULL,
    state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL,
    INDEX (state)
);

CREATE TABLE IF NOT EXISTS logs (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    build_id INT UNSIGNED NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity ENUM ('FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE') NOT NULL,
    message LONGTEXT COMPRESSED NOT NULL,
    INDEX (build_id),
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

//

DELIMITER ;
