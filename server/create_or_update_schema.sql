DELIMITER //

CREATE TABLE IF NOT EXISTS settings (
  name VARCHAR(32) PRIMARY KEY,
  value TINYTEXT NOT NULL
);

INSERT IGNORE settings (name, value)
  VALUE ("log_level", "TRACE"),
        ("server_timeout", "10"),
        ("log_retention_days", "10"),
        ("waffle_root", "waffle"),
        ("storage_dir", "storage");

CREATE TABLE IF NOT EXISTS log_level (
  severity VARCHAR(5) PRIMARY KEY,
  rank TINYINT UNSIGNED NOT NULL
);

INSERT IGNORE log_level (severity, rank)
  VALUE ('FATAL', 1),
        ('ERROR', 2),
        ('WARN', 3),
        ('INFO', 4),
        ('DEBUG', 5),
        ('TRACE', 6);

CREATE TABLE IF NOT EXISTS projects (
  id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name TINYTEXT NOT NULL UNIQUE KEY,
  remote_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS build_configs (
  project TINYINT UNSIGNED NOT NULL,
  name TINYTEXT NOT NULL,
  build_script TEXT NOT NULL,
  work_dir TEXT NOT NULL,
  output_file TEXT,
  UNIQUE KEY (project, name),
  FOREIGN KEY (project) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requests (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project TINYINT UNSIGNED NOT NULL,
  integration BOOL NOT NULL,
  source_branch TEXT NOT NULL,
  target_branch TEXT NOT NULL,
  state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (target_branch),
  INDEX (state),
  FOREIGN KEY (project) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS builds (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  request INT UNSIGNED NOT NULL,
  worker_id TINYINT UNSIGNED,
  build_config TINYTEXT NOT NULL,
  remote_url TEXT NOT NULL,
  project_name TINYTEXT NOT NULL,
  source_branch TEXT NOT NULL,
  build_script TEXT NOT NULL,
  work_dir TEXT NOT NULL,
  output_file TEXT,
  state ENUM ('REQUESTED', 'BUILDING', 'SUCCEEDED', 'FAILED', 'ABORTED') NOT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT 0,
  ended_at TIMESTAMP NOT NULL DEFAULT 0,
  duration TEXT AS (TIMESTAMPDIFF(SECOND, started_at, ended_at)),
  INDEX (request),
  INDEX (state),
  FOREIGN KEY (request) REFERENCES requests(id)
);

CREATE TABLE IF NOT EXISTS servers (
  id TINYINT UNSIGNED PRIMARY KEY,
  status ENUM ('IDLE', 'BUSY', 'OFFLINE') NOT NULL,
  heartbeat TIMESTAMP NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS logs (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  server_id TINYINT UNSIGNED NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  severity ENUM ('FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE') NOT NULL,
  message LONGTEXT COMPRESSED NOT NULL,
  INDEX (server_id)
);

--
-- Test data
--

INSERT IGNORE projects (name, remote_url)
  VALUE ("test-project", "/home/auygun/code/proj2/proj.git");

INSERT IGNORE build_configs (project, name, build_script, work_dir, output_file)
  VALUE ((SELECT id FROM projects WHERE name="test-project"), "Debug", "build/build.py", "", "out/debug/demo"),
        ((SELECT id FROM projects WHERE name="test-project"), "Release", "build/build.py", "", "out/release/demo"),
        ((SELECT id FROM projects WHERE name="test-project"), "Final", "build/build.py", "", NULL);



//

DELIMITER ;
