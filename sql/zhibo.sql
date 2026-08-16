-- auto-generated definition
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