# TradingAgents-CN 快速操作笔记

## 1. 复制与编辑配置文件

```bash
cp .env.example .env
```

确保在 `.env` 中添加接口密钥与配置：
```ini
# 十元路由器/TenRouter 统一中转入口
CUSTOM_OPENAI_API_KEY=tr-z6Gf99sdUdECEFq3M_JKlL0ctCtN2ApN7kJ46fIAxD8
CUSTOM_OPENAI_BASE_URL=https://tenrouter.weike.fm/v1

OPENAI_API_KEY=tr-z6Gf99sdUdECEFq3M_JKlL0ctCtN2ApN7kJ46fIAxD8
OPENAI_BASE_URL=https://tenrouter.weike.fm/v1

# Tavily 实时搜索 API
TAVILY_API_KEY=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

# 本地 Redis 配置（若本地已启动 6379 端口）
REDIS_HOST=localhost
REDIS_PORT=6379
# 若本地 Redis 无密码，设为空即可
REDIS_PASSWORD=
```

---

## 2. 数据库与基础设施启动

### 2.1 启动 MongoDB 容器（国内镜像源加速）

底层 PyMongo / Motor 异步驱动强依赖 MongoDB 存储多智能体状态、报告与配置。

```bash
docker run -d \
  --name tradingagents-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=tradingagents123 \
  -e MONGO_INITDB_DATABASE=tradingagentscn \
  -v mongodb_data:/data/db \
  -v $(pwd)/scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro \
  docker.m.daocloud.io/library/mongo:4.4
```

**参数详解与作用：**
- `-d`：后台隐式运行容器 (Detached mode)。
- `--name tradingagents-mongodb`：指定容器名称为 `tradingagents-mongodb`。
- `-p 27017:27017`：将宿主机的 `27017` 端口映射到容器内 MongoDB 默认端口 `27017`。
- `-e MONGO_INITDB_ROOT_USERNAME=admin`：设置 MongoDB 根管理员账号。
- `-e MONGO_INITDB_ROOT_PASSWORD=tradingagents123`：设置 MongoDB 根管理员密码。
- `-e MONGO_INITDB_DATABASE=tradingagentscn`：设置默认初始创建的数据库名称。
- `-v mongodb_data:/data/db`：将 MongoDB 数据目录持久化挂载到 Docker Volume `mongodb_data`。
- `-v $(pwd)/scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro`：将本地初始化脚本只读挂载到容器初始化目录。
- `docker.m.daocloud.io/library/mongo:4.4`：使用 DaoCloud 国内加速镜像源拉取并启动 MongoDB 4.4 镜像。

---

## 3. Web 全栈启动命令 (后端 + 前端)

### 3.1 启动 FastAPI 后端服务

后端运行在 Python 环境中，提供 RESTful API 与 WebSocket / SSE 接口（默认端口 `8000`）。

**常规启动命令：**
```bash
python -m app.__main__
```

**使用 uvicorn 自定义参数启动：**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**参数详解与作用：**
- `python -m app.__main__`：模块化运行后端的入口文件 [app/__main__.py](file:///Users/liupengfei/workplace/github_project/TradingAgents-CN/app/__main__.py)。
- `uvicorn app.main:app`：指定使用 Uvicorn ASGI 服务器运行 [app/main.py](file:///Users/liupengfei/workplace/github_project/TradingAgents-CN/app/main.py) 中的 `app` 实例。
- `--host 0.0.0.0`：绑定所有网络接口，允许外部网络或前端跨机/容器访问。
- `--port 8000`：指定后端 HTTP/WebSocket 监听端口为 `8000`。
- `--reload`：热重载模式，代码更改后自动重启后端服务（推荐开发阶段使用）。

---

### 3.2 启动 Vue 3 前端工程

前端采用 Vue 3 + TypeScript + Vite + Element Plus 架构，源码位于 [frontend](file:///Users/liupengfei/workplace/github_project/TradingAgents-CN/frontend) 目录。

**启动步骤与命令：**
```bash
# 1. 进入前端目录
cd frontend

# 2. 安装前端依赖包
npm install

# 3. 启动 Vite 开发服务器 (默认端口 3000)
npm run dev
```

**自定义端口启动：**
```bash
npm run dev -- --port 3001
```

**前端构建与预览命令：**
```bash
# 打包构建生产环境静态资源 (输出到 frontend/dist)
npm run build

# 本地预览已构建的生产版本产物
npm run preview
```

**参数详解与作用：**
- `cd frontend`：进入前端项目目录 [frontend](file:///Users/liupengfei/workplace/github_project/TradingAgents-CN/frontend)。
- `npm install`：根据 [package.json](file:///Users/liupengfei/workplace/github_project/TradingAgents-CN/frontend/package.json) 和 `yarn.lock` 安装依赖包。
- `npm run dev`：运行 Vite 开发服务器（默认监听 `http://localhost:3000`），配置中已包含 API 代理至后端 `http://localhost:8000`。
- `-- --port 3001`：透传参数给 Vite，将前端服务开发端口指定为 `3001`。
- `npm run build`：运行 `vue-tsc` 类型检查并执行 `vite build` 编译打包。
- `npm run preview`：在本地开启轻量级 HTTP 服务，预览生产打包产物的效果。

---

## 4. CLI 命令行分析工具

命令行工具支持全交互式引导模式和丰富配置子命令。

### 4.1 交互式单股分析

**引导式问答分析模式（推荐）：**
```bash
python -m cli.main
# 或
python -m cli.main analyze
```

**参数详解与作用：**
- 无参数直接运行 `python -m cli.main` 或输入 `analyze` 子命令：触发交互式终端 UI，引导选择市场（A股/美股/港股）、股票代码、分析日期、LLM 提供商、分析师模型等。

---

### 4.2 CLI 配置与辅助命令

```bash
# 1. 检查和显示当前系统 LLM 配置与 API Key 状态
python -m cli.main config

# 2. 数据目录路径查看与配置
python -m cli.main data-config --show
python -m cli.main data-config --set /path/to/custom_data

# 3. 运行系统集成测试
python -m cli.main test

# 4. 查看可用的示例分析脚本列表
python -m cli.main examples

# 5. 显示软件版本和功能特性信息
python -m cli.main version

# 6. 显示中文帮助信息
python -m cli.main help
```

**参数详解与作用：**
- `config`：打印阿里百炼、OpenAI、Anthropic、Google 等 API Key 的设置状态。
- `data-config`：管理数据/缓存/结果持久化目录。
  - `--show` / `-s`：显示当前数据目录配置。
  - `--set /path` / `-d /path`：重新设定数据存储目录路径。
  - `--reset` / `-r`：重置数据目录为默认路径 `~/Documents/TradingAgents/data`。
- `test`：调用自动化测试脚本验证接口集成状态。
- `examples`：罗列 `examples/` 目录下的多语言/多模型使用样例。
- `version`：查看系统版本号（例如 1.0.0-preview）。

---

## 5. 中国市场数据源初始化命令 (A股数据)

若需同步和初始化 A 股的基础数据，可运行对应的初始化脚本：

```bash
# 1. AkShare 数据初始化
python -m cli.akshare_init

# 2. TuShare 数据初始化
python -m cli.tushare_init

# 3. BaoStock 数据初始化
python -m cli.baostock_init
```

---

## 6. Docker Compose 全栈容器化一键启动

如果使用 Docker Compose 镜像方式直接一键编排运行整个 Web 全栈：

```bash
docker-compose up -d
```

**参数详解与作用：**
- `up`：构建、创建并启动服务容器。
- `-d`：在后台（守护进程模式）运行所有容器（包括 Web 前端、FastAPI 后端、MongoDB、Redis 等）。