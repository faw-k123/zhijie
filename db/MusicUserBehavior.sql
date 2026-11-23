-- -- 创建用户行为数据库
-- CREATE DATABASE MusicUserBehavior;
-- GO
-- USE MusicUserBehavior;
-- GO
CREATE SCHEMA user_behave;
GO

--创建海外用户表 user_info
CREATE TABLE user_info (
    user_id VARCHAR(50) PRIMARY KEY,        -- 用户ID 主键
    username NVARCHAR(50) NOT NULL,         -- 用户名 非空
    country NVARCHAR(50),                   -- 用户所在国家/地区
    register_date DATETIME,                 -- 注册时间
    password NVARCHAR(100)                 -- 密码（加长存储加密后的密文）
);
GO

--创建听歌记录表 play_record
CREATE TABLE play_record (
    record_id BIGINT IDENTITY(1,1) PRIMARY KEY, -- 记录ID 自增主键
    user_id VARCHAR(50) NOT NULL,               -- 用户ID 外键
    song_id VARCHAR(20) NOT NULL,               -- 歌曲ID 外键
    play_duration INT,                          -- 播放时长(秒)
    play_time DATETIME,                         -- 播放时间
    -- 外键关联用户表
    FOREIGN KEY (user_id) REFERENCES user_info(user_id)
);
GO

--创建浏览记录表 view_record
CREATE TABLE view_record (
    view_id BIGINT IDENTITY(1,1) PRIMARY KEY,    -- 浏览ID 自增主键
    user_id VARCHAR(50) NOT NULL,               -- 用户ID 外键
    target_type NVARCHAR(20),                    -- 浏览内容类型
    target_id VARCHAR(50),                       -- 浏览对象ID
    view_time DATETIME,                          -- 浏览时间
    -- 外键关联用户表
    FOREIGN KEY (user_id) REFERENCES user_info(user_id)
);
GO

--创建人格测试表 personality_test
CREATE TABLE personality_test (
    test_id BIGINT IDENTITY(1,1) PRIMARY KEY,    -- 测试ID 自增主键
    user_id VARCHAR(50) NOT NULL,               -- 用户ID 外键
    personality_type NVARCHAR(20),              -- 人格类型
    result_detail NVARCHAR(MAX),                -- 测试详细结果
    test_date DATETIME,                         -- 测试完成时间
    -- 外键关联用户表
    FOREIGN KEY (user_id) REFERENCES user_info(user_id)
);
GO