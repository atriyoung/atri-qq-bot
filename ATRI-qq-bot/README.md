# QQ AI 女友机器人 — ATRI (亚托莉)

基于 NapCatQQ + OneBot v11 协议的 QQ 机器人，搭载《ATRI -My Dear Moments-》原典级角色扮演引擎。

## 特性

- **原典级角色引擎** — 基于全量剧本蒸馏的 V3 亚托莉角色系统，包括状态机、阻尼转场、口癖控制
- **群聊 + 私聊** — 群聊 @机器人 触发，私聊直接对话
- **情绪系统** — 低电压/高性能/防御态/空洞态，带阻尼感的状态切换
- **好感度系统** — 随互动自然演进，阶段从前期到后期动态变化
- **记忆系统** — 短期环形缓冲 + 长期记忆压缩 + SQLite 持久化
- **定时任务** — 早安/晚安/主动关心
- **Docker 一键部署**

## 技术栈

| 组件 | 说明 |
|------|------|
| QQ 协议 | NapCatQQ + OneBot v11 反向 WebSocket |
| AI 模型 | DeepSeek / 通义千问 (OpenAI 兼容 API) |
| 框架 | Python 3.11+ / aiohttp / asyncio |
| 数据库 | SQLite (aiosqlite) |
| 部署 | Docker + docker-compose |

## 快速开始

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 和 QQ_ACCOUNT
```

### 2. 启动

```bash
docker compose up -d
```

### 3. 扫码登录

打开 `http://服务器IP:6099`，用 token `napcat123` 登录，手机 QQ 扫码。

## 对话方式

| 场景 | 触发方式 |
|------|----------|
| 私聊 | 直接发消息 |
| 群聊 | @机器人 + 消息 |

## 指令

| 指令 | 说明 |
|------|------|
| `/状态` | 查看关系阶段和情绪 |
| `/帮助` | 显示帮助信息 |

## 角色设定

ATRI（亚托莉）出自《ATRI -My Dear Moments-》，山崎制造厂第四代仿生人。

角色引擎基于 [GzSakura1337/ATRI-skills](https://github.com/GzSakura1337/ATRI-skills) 的 V3 原典抛光版进行适配。

核心特性：
- 短句优先，停顿多，不解释
- 四态状态机（低电压/高性能/防御态/空洞态）带阻尼转场
- 严格的口癖和动作触发控制
- 默认前中期阶段，随互动自然演进

## 项目结构

```
qq-ai-girlfriend/
├── bot/                    # 主应用
│   ├── adapter/            # OneBot v11 协议适配
│   ├── llm/                # LLM 网关 (DeepSeek/通义千问)
│   ├── character/          # 角色引擎 (V3 ATRI)
│   ├── memory/             # 记忆系统
│   ├── handler/            # 消息分发
│   ├── service/            # 业务编排
│   ├── scheduler/          # 定时任务
│   └── utils/              # 工具
├── config/                 # 配置文件
│   ├── bot.yaml            # 主配置
│   └── characters/         # 角色卡
├── docker-compose.yml      # 部署
└── Dockerfile
```

## License

MIT
