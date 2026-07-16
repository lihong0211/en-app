# 中心化后端 + 登录功能 设计文档

日期：2026-07-16
分支：`feature/centralized-backend-auth`
状态：已确认，待转入实施计划

## 背景

用户提出的完整需求分 4 点：

1. 微信登录功能
2. 不同用户不同词库功能
3. 主界面功能（管理单词、个人词库，现有悬浮轮播作为词库播放的辅助功能）
4. 可以播放/浏览别人分享的词库

这 4 点之间有依赖关系：2 依赖 1（要先有"当前用户是谁"）、3 依赖 2（要先有数据模型才能管理）、4 依赖 2+3（还需要额外的公开/私有语义）。一次性设计全部会做成夹生饭，因此拆成多个独立阶段分别 brainstorm+实施。

**本文档只覆盖第 1 阶段：中心化后端部署 + 登录（微信扫码 + 账号密码）。** 第 2 阶段（多用户词库数据模型 + 主界面）、第 3 阶段（浏览他人词库）留待本阶段完成后单独设计。

## 现状（本阶段开始前）

- Electron 应用生产环境下会在用户本机 spawn 一个 PyInstaller 打包的 Python 后端子进程，连本机 MySQL（`127.0.0.1:8000` / `127.0.0.1:3306`），完全是单机架构
- 没有任何登录/鉴权机制：所有 `/words/*`、`/users/*` 接口任何人都能直接调
- `UserModel` 已有 `username`/`password`/`wx` 字段，但密码是明文存储，且没有实际的登录接口（只有增删改查）
- 用户已具备：阿里云服务器 + 已备案域名 + HTTPS 证书（就绪，只缺应用代码）、微信开放平台"网站应用" AppID/AppSecret（已注册）

## 架构调整

- 后端从"Electron 启动时的本地子进程"改为**常驻在阿里云服务器上的中心化 FastAPI 服务**，通过已配置好的域名 + HTTPS 对外提供服务
- MySQL 同步迁移到阿里云（用户自行准备好的实例），生产环境的 Electron 客户端所有 API 请求改为请求远程域名
- 因为不再需要打包分发 Python 后端可执行文件，以下内容可以整个移除：
  - `electron-builder` 的 `extraResources` 里 `backend/python-backend` 和 `backend/.env` 两项
  - `main.js` 生产分支里 `startPythonBackend()` 整套 spawn/环境变量注入/stdout监听/退出kill逻辑
  - `backend/python-backend.spec`（PyInstaller 打包配置）不再用于分发，如果开发者本地仍需要它可以保留，但生产打包流程不再依赖它
- **开发环境**（`npm run dev`）的后端启动方式维持现状：继续 spawn 本地 venv 跑的后端 + 本地 MySQL，不改成连远程。但登录界面/登录流程是 Electron 客户端代码的一部分，dev 和生产共用同一份前端代码，因此 dev 环境下也会要求登录，只是请求打的是本地后端——本地 MySQL 也需要执行一遍 `schema.sql` 加上 `token` 相关字段，否则本地登录会失败

## 登录设计

### 微信扫码登录

采用 Electron 内嵌 `BrowserWindow` + 拦截跳转的标准做法，不用轮询：

1. 主进程弹出登录子窗口，加载：
   `https://open.weixin.qq.com/connect/qrconnect?appid=<AppID>&redirect_uri=<后端回调地址>&response_type=code&scope=snsapi_login&state=<随机值>`
2. 用户用手机微信扫码确认
3. 微信将该窗口导航到 `redirect_uri?code=xxx&state=xxx`；主进程监听该窗口的导航事件，一旦目标地址匹配回调路径前缀，立即取出 `code` 并关闭窗口（不等页面渲染完成，用户体验是扫码后窗口即时消失）
4. 主进程将 `code` 提交给后端 `POST /auth/wechat/login`
5. 后端用 AppSecret 向微信换取 `access_token` + `openid`（AppSecret 全程只存在于后端，Electron 与前端都不接触），按 `openid` 查找/创建用户，首次登录顺便拉取微信昵称/头像存入 `users.nickname` / `users.avatar`
6. 后端生成随机 token（`secrets.token_hex(32)`），写入该用户的 `users.token` + `users.token_expires_at`（有效期 30 天），返回给客户端
7. Electron 本地存下 token，后续请求带 `Authorization: Bearer <token>`，进入主界面

### 账号密码登录

- `UserModel.password` 改为 `bcrypt` 哈希存储，字段长度扩到 `VARCHAR(255)`
- 新增 `POST /auth/register`（用户名 + 密码注册）、`POST /auth/login`（校验哈希，成功后同上一套逻辑生成/写入 token）
- 现有 `/users/add` 接口目前明文存密码，需要同步改为走哈希，避免留下不安全的创建用户口子

### Token 机制（不用 JWT，简化方案）

- 登录令牌直接作为字段存在 `users` 表上（`token` + `token_expires_at`），不引入 JWT、不单独建 session 表
- 校验方式：`SELECT * FROM users WHERE token = ? AND deleted_at IS NULL AND (token_expires_at IS NULL OR token_expires_at > NOW())`
- 代价：同一账号新登录会覆盖旧 token（旧登录失效），即单设备在线。对个人小工具场景可接受
- FastAPI 提供一个 `get_current_user` 依赖用于后续接口鉴权（本阶段不给 `/words/*` 加鉴权，留给下一阶段引入 `user_id` 归属时一并处理）

### Electron 客户端登录流程

- App 启动先读取本地存的 token（存一个本地 JSON 文件，不引入 `keytar` 等原生模块——避免重蹈这次 PyInstaller 原生打包的坑；安全性上比系统钥匙串弱，个人工具场景可接受）
- 有 token 则调 `/auth/me` 校验是否仍有效；无 token 或校验失败，弹登录窗口（微信扫码 / 账号密码两个入口）
- 登录成功后才挂载悬浮词卡主界面
- 统一的 axios 实例：`baseURL` 指向阿里云域名，所有请求自动带上 `Authorization` 头；收到 401 时统一清空本地 token 并弹回登录窗口

## 数据库改动

完整建表语句见 [`backend/sql/schema.sql`](../../../backend/sql/schema.sql)（阿里云数据库目前为空库，此文件包含 `users`、`words`、`word_meanings` 三张表的完整 DDL，可直接 `mysql -h <host> -u <user> -p <db> < schema.sql` 执行）。

`users` 表关键字段：

| 字段 | 说明 |
|---|---|
| `username` / `password` | 账号密码登录用，均可为空（纯微信登录用户没有这两个） |
| `wx` | 微信 `openid`，唯一索引，可为空 |
| `nickname` / `avatar` | 微信登录时同步 |
| `token` / `token_expires_at` | 登录令牌及过期时间 |

`words`、`word_meanings` 两张表结构与现有 SQLAlchemy 模型一致，本阶段不改动（不加 `user_id`，留给下一阶段）。

## 数据迁移

**不迁移。** 本地 MySQL 中已有的 362 条单词数据保留在本地，阿里云数据库从空表开始积累，不做导入。

## 错误处理

- 微信 `code` 换取失败（二维码过期、用户拒绝授权）：后端返回明确错误信息，登录窗口原地提示重新扫码，不重开窗口
- 账号密码错误：统一返回"用户名或密码错误"，不区分具体是哪个错误，避免账号枚举
- token 失效/过期：接口返回 401，Electron 的 axios 响应拦截器统一处理——清空本地 token、弹回登录窗口，不需要每个调用点各自判断
- 后端不可达（断网/服务异常）：提示"网络异常，请检查连接"，不做自动重试轮询

## 测试思路

- 微信扫码登录无法自动化测试（依赖真实扫码），人工验证：完整扫码登录一次、故意用过期二维码验证报错提示
- 账号密码登录：FastAPI 接口层测试覆盖注册成功、重复用户名、密码错误、token 过期几个分支
- Token 生成用 `secrets.token_hex(32)`，随机性由标准库保证，不需要额外测试

## 本阶段范围之外（留给后续阶段）

- 多用户词库数据模型：`words`/`word_meanings` 保持全局共享词典表不变（不加 `user_id`），新增 `word_libraries`（词库，归属某个 `user_id`，类似歌单）和 `word_library_items`（词库与单词的多对多关联）两张表承载"个人词库"
- 主界面重做：管理单词、管理个人词库，现有悬浮轮播变为"播放某个词库"的辅助功能
- 浏览/播放他人分享词库的发现功能，依赖 `word_libraries` 的公开/私有语义
- `/words/*` 等现有接口是否需要鉴权/过滤，取决于上面数据模型的具体设计，留到第 2 阶段一并定
