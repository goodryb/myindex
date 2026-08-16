-- auto-generated definition
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