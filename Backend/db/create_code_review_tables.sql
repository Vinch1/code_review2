CREATE DATABASE IF NOT EXISTS code_review2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE code_review2;
-- ============================================
-- Table: code_review_results
-- ============================================
CREATE TABLE IF NOT EXISTS code_review_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pr_number int,
  repo VARCHAR(255),
  branch VARCHAR(255),
  author VARCHAR(255),
  security_result JSON,
  summary_result JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Table: notification_outbox
-- ============================================
CREATE TABLE IF NOT EXISTS notification_outbox (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  aggregate_type VARCHAR(64) NOT NULL,   -- e.g., 'code_review_result'
  aggregate_id BIGINT NOT NULL,          -- references code_review_results.id
  status VARCHAR(16) NOT NULL DEFAULT 'READY', -- READY/SENT/FAILED
  retry_count INT NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_agg (aggregate_type, aggregate_id),
  INDEX idx_status (status),
  CONSTRAINT fk_aggregate_id FOREIGN KEY (aggregate_id)
      REFERENCES code_review_results(id)
      ON DELETE CASCADE
);
