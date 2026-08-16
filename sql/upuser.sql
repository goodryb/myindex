create table upuser
(
    upid      varchar(100) not null comment 'up的英文id'
        primary key,
    platform  varchar(100) not null comment '所在平台',
    cn_name   varchar(100) null comment '中文名称',
    accountid bigint       not null comment '账号数字id'
)
    comment '视频up信息';