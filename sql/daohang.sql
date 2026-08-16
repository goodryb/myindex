-- auto-generated definition
create table daohang
(
    id       bigint auto_increment comment 'id'
        primary key,
    cn_name  varchar(200) not null comment '网站中文名称',
    url      varchar(200) not null comment '网站网址',
    icon_url varchar(100) null comment '网站图标地址'
)
    comment '常用网址信息';