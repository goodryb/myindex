-- 什么值得买商品信息表
CREATE TABLE smzdm_products (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    title       VARCHAR(512) NOT NULL COMMENT '商品标题',
    description TEXT COMMENT '商品描述',
    link        VARCHAR(1024) NOT NULL COMMENT '商品链接',
    pub_date    DATETIME NOT NULL COMMENT '发布时间',
    guid        VARCHAR(255) NOT NULL COMMENT '商品唯一标识',
    keyword_id  INT NOT NULL COMMENT '关联的关键词ID',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_guid (guid),
    KEY idx_keyword_id (keyword_id),
    KEY idx_pub_date (pub_date)
) COMMENT='什么值得买商品信息表';