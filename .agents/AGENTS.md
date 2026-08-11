# TradingAgents-CN 项目运行与配置指南 (AGENTS.md)

本文档总结 TradingAgents-CN 项目的架构原理、核心依赖以及扩展配置规范，供 Agent 及开发者参考。

---

## 1. 项目架构与运行机制

TradingAgents-CN 是基于 LangGraph 的多智能体（Multi-Agent）股票分析与策略研究平台：
- **智能体协同拓扑**：包含 Market Analyst（技术分析）、Fundamentals Analyst（基本面）、News & Sentiment Analyst（新闻情绪）、Risk Analyst（风控）以及 Bull vs Bear Debate（多空辩论）与 Trader Decision（决策生成）。
- **运行模式**：
  1. **Web 全栈模式**：FastAPI 后端（端口 `8000`）+ Vue 3 前端（端口 `3000`），支持 WebSocket/SSE 实时日志与报告可视化。
  2. **CLI / 脚本模式**：通过 `python -m cli.main` 或直接脚本运行单股分析。

---

## 2. 数据库与基础设施依赖

- **MongoDB（核心必需依赖）**：
  - 用于持久化多智能体对话状态、历史分析报告、系统配置、模型 Catalog、实时行情及自选股信息。
  - **是否可用 MySQL / PostgreSQL 替代？** 否。底层深度使用 PyMongo / Motor 异步驱动及 JSON/BSON 动态文档查询与聚合管道，无法通过简单配置更换数据库。
- **Redis（缓存与队列依赖）**：
  - 用于系统请求限流、数据缓存与任务队列。可连接本地已运行的 Redis 实例。

---

## 3. 大模型 (LLM) 与 API 配置规范

项目支持通过 `CUSTOM_OPENAI` / `OPENAI` 配置第三方中转/聚合服务（如 TenRouter、OneAPI、302.AI 等）。

### `.env` 关键配置模版：
```ini
# 自定义 OpenAI 兼容接口 (如 TenRouter 统一协议入口)
CUSTOM_OPENAI_API_KEY=tr-z6Gf99sdUdECEFq3M_JKlL0ctCtN2ApN7kJ46fIAxD8
CUSTOM_OPENAI_BASE_URL=https://tenrouter.weike.fm/v1

# 基础 OpenAI 映射配置
OPENAI_API_KEY=tr-z6Gf99sdUdECEFq3M_JKlL0ctCtN2ApN7kJ46fIAxD8
OPENAI_BASE_URL=https://tenrouter.weike.fm/v1

# 联网搜索 API Key (Tavily)
TAVILY_API_KEY=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

# 默认数据源
DEFAULT_CHINA_DATA_SOURCE=akshare

# 代理与国内域名绕过配置
NO_PROXY=localhost,127.0.0.1,eastmoney.com,.eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,82.push2.eastmoney.com,83.push2.eastmoney.com,82.push2delay.eastmoney.com,quote.eastmoney.com,datacenter.eastmoney.com,dfcfw.com,.dfcfw.com,gtimg.cn,.gtimg.cn,sinaimg.cn,.sinaimg.cn,sina.com.cn,.sina.com.cn,api.tushare.pro,.tushare.pro,baostock.com,.baostock.com,akshare.xyz,.akshare.xyz

# 股票代码前缀过滤配置（如仅爬取/同步 60、00 开头的沪深主板股票）
STOCK_CODE_PREFIX_FILTER_ENABLED=false
STOCK_CODE_ALLOWED_PREFIXES=60,00
```

### 4. 数据源高可用与过滤规范

- **代理绕过机制**：AKShare 内部请求增加 `ProxyError` / `RemoteDisconnected` 自动拦截，检测到本地代理中断时强行直连国内 API 服务。
- **Tushare 频率超限保护**：Tushare 连通性测试捕获到 `频率超限`（Rate Limit）时，将其认定为 Token 有效（`connected=True`），避免因频次限制误判为连接失败。
- **股票前缀过滤**：开启 `STOCK_CODE_PREFIX_FILTER_ENABLED=true` 后，`DataSourceManager` 及底层 Adapters (`AKShare` / `Tushare` / `BaoStock`) 会自动截取匹配 `STOCK_CODE_ALLOWED_PREFIXES` 的股票列表进行同步。

### Web 界面配置：
在 **系统设置 -> 配置管理 -> 厂家管理** 中添加 `Custom OpenAI` 提供商，填入对应 `Base URL` 与 `API Key`，并注册模型 `gpt-5.6-luna` 设为默认分析模型。
