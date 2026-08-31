# MyIndex 项目

这是一个基于 Flask 的内容导航网站，支持显示优惠商品信息、UP 主视频更新和常用网站链接。

## 功能特性

1. 展示最近 24 小时优惠商品信息
2. 展示 UP 主当日最新视频
3. 提供常用网站链接导航
4. 事件心跳监控
5. **自动夜间模式**：支持根据系统设置自动切换深色/浅色主题

## 技术栈

- Flask (Web 框架)
- MySQL (关系型数据库)
- HTML/CSS (前端展示，支持响应式布局与夜间模式)

## 配置说明

### 环境变量配置

项目使用 `.env` 文件来配置环境变量，请参考 `.env.example` 文件创建您的 `.env` 文件：

> 数据库连接完全由 `.env` 中的配置决定（不再区分生产/测试环境），缺一不可。

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=myindex
```

### 数据库表结构

项目需要以下六张表：

1. `upuser` - UP 主信息表
2. `upvideo` - UP 主视频信息表
3. `daohang` - 常用网站导航表
4. `event_heartbeat` - 事件心跳记录表
5. `smzdm_keywords` - 商品搜索关键词表
6. `smzdm_products` - 商品信息表

表结构定义请参考 `sql/` 目录下的 SQL 文件。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行项目

```bash
python app.py
```

项目将在 `http://localhost:5000` 上运行。

## 数据库迁移

容器启动时会先自动执行数据库迁移（`python tool/migrate.py`），迁移成功后才启动应用：

1. 按文件名升序扫描 `migrations/` 目录下的 `.sql` 文件
2. 已应用的版本记录在 `schema_migrations` 表中，不会重复执行
3. 表结构变更时：**新增** `migrations/002_xxx.sql` 等增量文件（不要修改已发布的文件）
4. 首次部署到已有数据的库时，已存在的表会自动跳过（幂等），不会破坏现有数据
5. 数据库未就绪时会自动重试（最多 10 次，间隔 3 秒）

手动执行迁移：

```bash
python tool/migrate.py
```

## 镜像构建（GitHub Actions 多架构）

本地无需 Docker 环境，推送代码到 GitHub 后由 Actions 自动完成多架构构建（`linux/amd64` + `linux/arm64`，arm64 适配 OpenWrt 等设备）并推送 Docker Hub。

触发方式：打版本 tag

```bash
git tag v1.2.0
git push origin v1.2.0
```

前置配置（GitHub 仓库 Settings → Secrets and variables → Actions）：

- `DOCKERHUB_USERNAME`：Docker Hub 用户名
- `DOCKERHUB_TOKEN`：Docker Hub Access Token（Docker Hub 账号 Settings → Security 中创建）

构建产物：`<用户名>/myindex:latest` 与 `<用户名>/myindex:<tag>`。

启动（群晖 / OpenWrt 通用）：

```bash
docker run -d --name myindex -p 8888:5000 \
  -e DB_HOST=192.168.1.15 -e DB_PORT=3307 -e DB_USER=root \
  -e DB_PASSWORD=<密码> -e DB_NAME=mohua \
  -e TZ=Asia/Shanghai <用户名>/myindex:latest
```

> OpenWrt 拉取前请确认架构为 arm64（aarch64）；容器首次启动会自动执行数据库迁移。

## API 接口

### 1. UP 主信息查询
**接口**: `GET /up/<up_id>`

**描述**: 根据 UP 主 ID 获取其详细信息和当日发布的视频列表。

**请求示例**:
```
GET /up/bilibili_123456
```

**响应格式**:
```json
{
  "name": "UP主名称",
  "videolist": [
    {
      "videoname": "视频标题",
      "videourl": "视频链接"
    }
  ]
}
```
*注意：如果未找到 UP 主，返回 404 错误。*

### 2. 事件心跳上报
**接口**: `GET /api/event_heartbeat`

**描述**: 用于上报事件心跳，记录事件的最新活动时间。

**请求参数**:
- `event_name` (必需): 事件名称，字符串类型，最大长度100字符。
- `timestamp` (可选): 心跳时间戳，ISO 8601 格式（如 `2025-12-27T10:30:00Z`）。如果不提供，则使用服务器当前时间。

**请求示例**:
```
GET /api/event_heartbeat?event_name=service_health_check
GET /api/event_heartbeat?event_name=backup_job&timestamp=2025-12-27T10:30:00Z
```

**响应格式**:

成功：
```json
{
  "success": true,
  "message": "Event heartbeat updated successfully",
  "event_name": "backup_job",
  "timestamp": "2025-12-27T10:30:00+00:00"
}
```

失败：
```json
{
  "success": false,
  "error": "Missing event_name parameter",
  "message": "..."
}
```

## 数据访问策略

项目采用单一数据源访问策略：
1. 从 MySQL 数据库获取数据（保证数据持久化）

## 文件结构

```
myindex/
├── app.py              # 主应用入口
├── api.py              # API 接口模块
├── db.py               # 数据库操作封装
├── .env.example        # 环境变量示例文件
├── .env                # 环境变量配置文件
├── requirements.txt    # 依赖包列表
├── Dockerfile          # Docker 镜像构建文件 (GitHub Actions 使用)
├── sql/                # 数据库表结构定义
│   ├── upuser.sql
│   ├── upvideo.sql
│   ├── daohang.sql
│   ├── event_heartbeat.sql
│   ├── smzdm_keywords.sql
│   └── smzdm_products.sql
├── migrations/         # 数据库迁移脚本（容器启动自动执行）
│   └── 001_baseline.sql
├── templates/          # HTML 模板文件
│   ├── index.html      # 首页展示
│   └── admin.html      # 后台管理页面
├── tool/               # 工具脚本
│   └── migrate.py       # 数据库版本化迁移工具
└── README.md           # 项目说明文件
```
## 版本信息

- 版本: 1.1.5
