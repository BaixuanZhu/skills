-- 测试表结构（H2 MySQL 模式）
-- 先 DROP 再 CREATE，确保每次连接初始化时表是干净的（避免 INSERT 累加）
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    status INT,
    gender INT,
    dept_id BIGINT,
    deleted INT DEFAULT 0,
    version INT DEFAULT 0
);

-- 测试数据
INSERT INTO sys_user (name, age, status, gender, dept_id) VALUES
    ('Tom', 25, 1, 1, 100),
    ('Jerry', 30, 1, 1, 100),
    ('Alice', 28, 0, 2, 200),
    ('Bob', 35, 1, 1, 200),
    ('Eve', 22, 1, 2, 200);
