-- 事件心跳记录表
CREATE TABLE event_heartbeat (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    event_name VARCHAR(100) NOT NULL COMMENT '事件名称',
    latest_heartbeat TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最新心跳时间',
    UNIQUE INDEX unique_event_name (event_name),
    INDEX idx_event_name (event_name)
) COMMENT='事件心跳记录表';