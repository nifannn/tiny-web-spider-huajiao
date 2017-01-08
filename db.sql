create database if not exists `ZhiBo` default character set utf8mb4 collate utf8mb4_general_ci;
use `ZhiBo`;
set names utf8mb4;

create table if not exists `Huajiao_User`(
        `UserId` int unsigned not null,
        `UserName` varchar(255) not null default '' comment '昵称',
        `Level` int unsigned not null default 0 comment '等级',
        `About` varchar(600) not null default '' comment '简介',
        `Follow` int unsigned not null default 0 comment '关注数',
        `Follower` int unsigned not null default 0 comment '粉丝数',
        `Like` int unsigned not null default 0 comment '赞',
        `Experience` int unsigned not null default 0 comment '经验',
        `Avatar` varchar(255) not null default '' comment '头像地址',
        `UpdateTime` timestamp not null default current_timestamp comment '更新时间',
        primary key(`UserId`) 
) Engine=InnoDB default charset=utf8mb4 collate=utf8mb4_general_ci;

