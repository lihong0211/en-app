# 部署说明（阿里云）

## 前提

- 阿里云 ECS（或等价服务器），已配置好域名 + HTTPS 证书 + 反向代理（nginx 或其它）
- MySQL 实例可用，已执行 `backend/sql/schema.sql` 建表

## 部署 FastAPI 后端

1. 把 `backend/` 目录（不含 `.venv`、`__pycache__`、`dist`、`build`）上传到服务器
2. 服务器上装 Python 3.12，建虚拟环境并装依赖：

   ```bash
   cd backend
   python3 -m venv .venv
   ./.venv/bin/pip install -r requirements.txt
   ```

3. 服务器上的 `backend/.env` 需要指向真实的生产数据库和微信配置（不要把开发机的 `.env` 直接传上去，密码、AppSecret 都要换成生产环境的）
4. 用 `systemd` 常驻运行（避免 SSH 断开进程就没了），创建 `/etc/systemd/system/jidanci-backend.service`：

   ```ini
   [Unit]
   Description=jidanci FastAPI backend
   After=network.target

   [Service]
   WorkingDirectory=/path/to/backend
   ExecStart=/path/to/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
   Restart=always
   User=your_linux_user

   [Install]
   WantedBy=multi-user.target
   ```

5. 启动并设置开机自启：

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now jidanci-backend
   sudo systemctl status jidanci-backend
   ```

6. nginx 反向代理把 `https://你的域名/` 转发到 `127.0.0.1:8000`（HTTPS 终止在 nginx，uvicorn 本身跑 HTTP 就行）：

   ```nginx
   server {
     listen 443 ssl;
     server_name 你的域名;
     # ssl_certificate / ssl_certificate_key 用你已有的证书配置

     location / {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
     }
   }
   ```

7. 微信开放平台"网站应用"的授权回调域配置成 `你的域名`（不含协议和路径），并把 `backend/.env` 里的 `WECHAT_APP_ID`/`WECHAT_APP_SECRET` 换成真实值

## Electron 客户端

生产打包前，以下 4 处占位值都要换成真实值，缺一个都会导致登录在生产环境静默失败（`/auth/me` 请求假域名、微信授权 URL 里带的是假 AppID）：

1. `src/main/main.js` 顶部"微信开放平台配置"注释处的 `WECHAT_APP_ID`，换成真实的微信开放平台 AppID（AppID 不是密钥，可以放在客户端）
2. 同一处的 `WECHAT_REDIRECT_URI`，换成跟微信开放平台后台配置的"授权回调域"匹配的具体回调路径（如 `https://你的域名/auth/wechat/callback`）
3. 同一处 `API_BASE_URL` 三元表达式里生产分支（`NODE_ENV !== 'development'` 时）的值，换成 `https://你的域名`
4. `src/render/.env.production` 里的 `VUE_APP_API_BASE_URL`，同样换成 `https://你的域名`

前 3 处在代码里，第 4 处在环境变量文件里，两边都要改，缺一不可。
