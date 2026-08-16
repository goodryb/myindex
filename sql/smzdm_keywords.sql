-- 什么值得买关键词管理表
CREATE TABLE smzdm_keywords (
    id         INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    keyword    VARCHAR(255) NOT NULL COMMENT '搜索关键词',
    site_type  VARCHAR(50) NOT NULL DEFAULT 'smzdm' COMMENT '网站类型，如smzdm(什么值得买)、jd(京东)等',
    enabled    TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用，1-启用，0-禁用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_keyword_site (keyword, site_type)
) COMMENT='什么值得买关键词管理表';