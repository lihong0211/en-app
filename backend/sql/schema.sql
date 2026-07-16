-- 记单词 - 阿里云数据库建表语句
-- 数据库名跟 backend/.env 里的 DB_NAME 保持一致（默认 english_new）
-- 用法：mysql -h <host> -u <user> -p <DB_NAME> < schema.sql

CREATE TABLE IF NOT EXISTS users (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username     VARCHAR(20)  UNIQUE COMMENT '账号密码登录用户名，微信登录用户可为空',
  password     VARCHAR(255) COMMENT 'bcrypt 哈希，微信登录用户可为空',
  wx           VARCHAR(64)  UNIQUE COMMENT '微信 openid，账号密码登录用户可为空',
  nickname     VARCHAR(50)  COMMENT '昵称，微信登录时同步微信昵称',
  avatar       VARCHAR(255) COMMENT '头像 URL，微信登录时同步微信头像',
  phone        VARCHAR(11),
  description  VARCHAR(255),
  active       TINYINT      NOT NULL DEFAULT 1 COMMENT '1激活 0禁用',
  token        VARCHAR(64)  UNIQUE COMMENT '登录令牌，随机字符串，新登录会覆盖旧的（单设备在线）',
  token_expires_at DATETIME COMMENT '令牌过期时间',
  created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at   DATETIME     NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户';

CREATE TABLE IF NOT EXISTS words (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  word              VARCHAR(30) NOT NULL UNIQUE,
  en_pronunciation  VARCHAR(30),
  us_pronunciation  VARCHAR(30),
  created_at        DATETIME    DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at        DATETIME    NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='单词';

CREATE TABLE IF NOT EXISTS word_meanings (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  word_id     INT UNSIGNED NOT NULL COMMENT '单词ID',
  type        VARCHAR(20)  NOT NULL COMMENT '词性',
  content     TEXT         NOT NULL COMMENT '释义内容',
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at  DATETIME     NULL COMMENT '软删除时间',
  CONSTRAINT fk_word_meanings_word_id FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='单词释义';
