-- 001_baseline.sql: 初始表结构（由 sql/ 目录 7 张表合并，幂等设计，表已存在时迁移器自动跳过）

-- UP 主信息表
create table upuser
(
    upid      varchar(100) not null comment 'up的英文id'
        primary key,
    platform  varchar(100) not null comment '所在平台',
    cn_name   varchar(100) null comment '中文名称',
    accountid bigint       not null comment '账号数字id'
)
    comment '视频up信息';

-- UP 主视频信息表
create table upvideo
(
    id        int auto_increment comment '主键'
        primary key,
    cn_name   varchar(300) not null comment '视频中文标题',
    url       varchar(200) not null comment '视频播放地址',
    videodate datetime     not null comment '视频发布时间',
    upid      varchar(100) not null comment '对应的up',
    unique key idx_upvideo_url (url),
    constraint upvideo_upuser_upid_fk
        foreign key (upid) references upuser (upid)
)
    comment 'up视频信息';

-- 主播直播信息表
create table zhibo
(
    roomid         varchar(100) not null comment '直播间id',
    cn_name        varchar(100) not null comment '主播中文名称',
    status         tinyint      not null comment '直播状态',
    address        varchar(100) not null comment '直播地址',
    name           varchar(100) not null comment '英文唯一id'
        primary key,
    last_push_date date         null comment '最后推送日期',
    type           varchar(50)  null comment '类型'
)
    comment '直播信息表';

-- 常用网址信息
create table daohang
(
    id       bigint auto_increment comment 'id'
        primary key,
    cn_name  varchar(200) not null comment '网站中文名称',
    url      varchar(200) not null comment '网站网址',
    icon_url varchar(100) null comment '网站图标地址'
)
    comment '常用网址信息';

-- 事件心跳记录表
CREATE TABLE event_heartbeat (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    event_name VARCHAR(100) NOT NULL COMMENT '事件名称',
    latest_heartbeat TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最新心跳时间',
    UNIQUE INDEX unique_event_name (event_name),
    INDEX idx_event_name (event_name)
) COMMENT='事件心跳记录表';

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