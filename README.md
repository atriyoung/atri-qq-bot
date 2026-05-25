# QQ AI 女友机器人 — ATRI（亚托莉）

一个基于 NapCatQQ + DeepSeek 的 QQ 机器人，搭载《ATRI -My Dear Moments-》原典级角色扮演引擎。

**不需要写一行代码，跟着文档走就能搭好。**

---

## 目录

- [项目简介](#项目简介)
- [你需要准备什么](#你需要准备什么)
- [方式一：Linux 服务器部署（推荐）](#方式一linux-服务器部署推荐)
- [方式二：Windows 本地运行](#方式二windows-本地运行)
- [配置说明](#配置说明)
- [如何对话](#如何对话)
- [如何改角色](#如何改角色)
- [指令列表](#指令列表)
- [常见问题](#常见问题)

---

## 项目简介

### 功能

| 功能 | 说明 |
|------|------|
| 群聊对话 | 在 QQ 群里 **@机器人** 说话，它会以 ATRI 的身份回复 |
| 私聊对话 | 直接加机器人好友，一对一聊天 |
| 情绪系统 | 低电压（犯困）/ 高性能（得意）/ 防御态（被骂）/ 空洞态（被戳穿）——带真实过渡感 |
| 好感度 | 随互动自然增长，从"前期"慢慢过渡到"后期"的亲密感 |
| 记忆 | 记住聊过什么，旧对话会压缩保存 |
| 定时互动 | 早安、晚安、主动关心 |

### 角色

ATRI（亚托莉）出自视觉小说《ATRI -My Dear Moments-》，山崎制造厂第四代仿生人。

她的标志性特征：
- 自称「高性能机器人」，但做家务笨手笨脚
- 看到螃蟹会兴奋到逻辑短路
- 被叫「萝卜子」会搬《反歧视法》反击——但必然忘词卡壳
- 口头禅：「毕竟我是高性能的嘛！」
- 核心矛盾：「我到底有没有真正的心？」

角色引擎基于 [GzSakura1337/ATRI-skills](https://github.com/GzSakura1337/ATRI-skills) V3 原典抛光版适配。

### 技术栈

| 组件 | 用途 |
|------|------|
| NapCatQQ | 让程序能收发 QQ 消息 |
| OneBot v11 | QQ 和程序之间通信的协议 |
| DeepSeek API | AI 对话引擎（也支持通义千问） |
| SQLite | 存储对话记录和记忆 |
| Docker | 一键部署，不需要手动装环境 |

---

## 你需要准备什么

### 必需

| 项目 | 说明 | 去哪弄 |
|------|------|--------|
| **QQ 小号** | 用来跑机器人的 QQ，不要用大号 | 注册一个新 QQ 号 |
| **DeepSeek API Key** | AI 对话的费用，很便宜 | [platform.deepseek.com](https://platform.deepseek.com) 注册，充值 10 块能用很久 |
| **一台服务器**（方式一）或 **自己的电脑**（方式二） | 运行程序的机器 | 腾讯云 / 阿里云 轻量服务器 2核2G 够用 |

### 可选

| 项目 | 说明 |
|------|------|
| GitHub 账号 | 下载代码用（也可以用本项目压缩包） |

---

## 方式一：Linux 服务器部署（推荐）

服务器 24 小时在线，关掉电脑机器人也在跑。以 Debian 12 为例。

### 第一步：登录服务器

1. 买好服务器后，在云服务商控制台找到 **「远程连接」** 或 **「登录」**
2. 选 **「标准登录」**，会打开一个网页版的命令行窗口
3. 后面所有命令都粘贴到这个窗口里执行

### 第二步：安装 Docker

```bash
curl -fsSL https://get.docker.com | bash
```

安装完确认一下：

```bash
docker --version
```

应该显示版本号（例如 `Docker version 29.3.0`）。

### 第三步：下载项目

```bash
apt install -y git
git clone https://github.com/atriyoung/atri-qq-bot.git
cd atri-qq-bot
```

> 如果服务器连不上 GitHub，可以先把项目下载到你自己的电脑，然后用网页终端自带的 **「上传文件」** 按钮传到 `/root/` 目录，再执行：
> ```bash
> mkdir -p /root/atri-qq-bot
> tar xzf /root/atri-qq-bot.tar.gz -C /root/atri-qq-bot
> cd /root/atri-qq-bot
> ```

### 第四步：配置

创建配置文件：

```bash
cat > .env << 'EOF'
DEEPSEEK_API_KEY=把你申请的key填这里
QWEN_API_KEY=sk-optional
QQ_ACCOUNT=把机器人的QQ号填这里
NAPACAT_TOKEN=napcat123
EOF
```

> **DEEPSEEK_API_KEY**：去 [platform.deepseek.com](https://platform.deepseek.com) → API Keys → 复制 `sk-` 开头的那串。
>
> **QQ_ACCOUNT**：机器人的 QQ 号，纯数字。

确认配置正确：

```bash
cat .env
```

你应该看到四个等号右边都有值。

### 第五步：启动

```bash
docker compose up -d
```

第一次运行会下载镜像和构建，等 2-3 分钟。完成后确认：

```bash
docker compose ps
```

两个容器都显示 `Up` 就说明成功了：
```
NAME               STATUS
qq-ai-girlfriend   Up (healthy)
qq-napcat          Up
```

### 第六步：扫码登录

1. 打开浏览器，访问 `http://你的服务器IP:6099`
2. Token 填 `napcat123`，登录
3. 左侧找 **「WebSocket Client」**，添加一条：
   ```
   ws://bot:8765/onebot/v11/ws
   ```
4. 页面会显示一个二维码，用 **机器人的 QQ 号** 扫码
5. 扫码成功后，机器人就上线了

> **安全提示**：如果 6099 端口打不开，去云服务商控制台的 **安全组/防火墙** 添加 TCP 6099 入站规则。扫码完成后建议**删掉这条规则**，避免别人访问。

### 第七步：测试

用你的**大号 QQ**：
- **加机器人好友**，发一句「你好」
- 或者把机器人**拉进群**，@它 说话

机器人应该会以 ATRI 的身份回复你。

### 更新项目

以后代码有更新，这样更新：

```bash
cd /root/atri-qq-bot
git pull
docker compose up -d --build bot
```

### 查看日志

```bash
# 看 bot 日志
docker compose logs bot --tail 30

# 看 NapCat 日志
docker compose logs napcat --tail 30

# 实时看（按 Ctrl+C 退出）
docker compose logs bot -f
```

### 停止/重启

```bash
# 停止
docker compose down

# 重启
docker compose up -d
```

---

## 方式二：Windows 本地运行

适合在自己电脑上测试、开发。缺点是电脑关机机器人就下线了。

### 第一步：安装必要软件

| 软件 | 下载地址 | 说明 |
|------|----------|------|
| Python | [python.org](https://www.python.org/downloads/) | 装 **3.11 或更高**，安装时勾选「Add Python to PATH」 |
| Git | [git-scm.com](https://git-scm.com/download/win) | 下载代码用 |
| NapCatQQ | [napcat.win](https://napcat.win) | QQ 客户端 + NapCat 插件 |

都装好后，按 `Win + R`，输入 `cmd`，回车。在弹出的黑色窗口里执行后面的命令。

### 第二步：下载项目

```cmd
git clone https://github.com/atriyoung/atri-qq-bot.git
cd atri-qq-bot
```

> 或者直接在本网页点绿色的 **Code → Download ZIP**，解压到任意文件夹，然后 `cd` 进去。

### 第三步：安装依赖

```cmd
pip install -r requirements.txt
```

如果 `pip` 报错说找不到，试试 `pip3` 或 `python -m pip`。

### 第四步：配置

在项目文件夹里新建一个 `.env` 文件（注意名字就一个点开头），内容：

```
DEEPSEEK_API_KEY=把你申请的key填这里
QWEN_API_KEY=sk-optional
QQ_ACCOUNT=把机器人的QQ号填这里
```

> 创建一个文本文件，写完内容后「另存为」，文件名填 `.env`，编码选 UTF-8。

### 第五步：启动 NapCatQQ

1. 打开你安装的 NapCatQQ
2. 用**机器人 QQ 号**登录
3. 在 NapCat 设置里，找到 **「网络设置」→「WebSocket Client」**
4. 添加一条：`ws://127.0.0.1:8765/onebot/v11/ws`
5. 保存

### 第六步：启动 Bot

回到命令行窗口，确保在项目目录里，执行：

```cmd
python -m bot
```

看到 `QQ AI Girlfriend Bot started!` 就说明成功了。

### 第七步：测试

同服务器部署的第七步——加大号好友/拉群，开始聊天。

### 停止

在命令行窗口按 `Ctrl + C` 就能停下。

---

## 配置说明

### `.env` 文件

这是最核心的配置文件，里面是你的密钥和账号信息。

| 变量 | 说明 | 必填 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 的 API Key（`sk-` 开头） | ✅ |
| `QWEN_API_KEY` | 通义千问的 Key（如果不用千问可以不填） | ❌ |
| `QQ_ACCOUNT` | 机器人 QQ 号，纯数字 | ✅ |
| `NAPACAT_TOKEN` | NapCat WebUI 的登录密码 | 服务器部署必填 |

### `config/bot.yaml`

这个文件控制机器人的行为，一般不需要改。如果你想换模型或者调整参数，改这里。

```yaml
llm:
  provider: "deepseek"    # 改成 "qwen" 可以切换通义千问
  deepseek:
    model: "deepseek-chat"
    temperature: 0.8       # 越高越活泼，越低越严谨
    max_tokens: 512        # 回复最大长度
```

### 费用参考

DeepSeek 的 API 非常便宜。闲聊场景下，**10 块钱能用好几周**。

---

## 如何对话

### 私聊

直接给机器人发消息就行。

### 群聊

必须 **@机器人** 才能触发回复，避免误触。

### 第一次聊天是什么样的

ATRI 默认处于**前中期**状态：
- 她会先努力证明自己「有用」
- 叫用户「夏生先生」
- 会得意、会笨拙、有小脾气
- 不会一上来就表白或深度撒娇

随着聊天次数增多，好感度会自然上升，亲密度也会慢慢变化。

---

## 如何改角色

角色定义在两个地方：

### 1. 角色卡：`config/characters/waifu.yaml`

这里面定义了角色的名字、外貌、性格、说话风格、背景故事等。

你可以自己写一个新的 YAML 文件，然后修改 `config/bot.yaml` 里的：

```yaml
character:
  card_path: "config/characters/你的角色.yaml"
```

### 2. 系统提示词：`bot/character/engine.py`

`build_system_prompt()` 方法里是发给 AI 的完整角色指令。如果你想深度定制角色的行为逻辑，改这里。

---

## 指令列表

在 QQ 里给机器人发以下指令：

| 指令 | 效果 |
|------|------|
| `/状态` | 查看当前关系阶段和情绪状态 |
| `/帮助` | 显示帮助信息 |

---

## 常见问题

### Q: 机器人不理我？

1. 确认 Docker 容器在运行：`docker compose ps`
2. 确认 WebSocket 连接成功——看日志里有没有 `NapCat connected`
3. 在 NapCat WebUI (`http://IP:6099`) 检查 WebSocket Client 地址对不对
4. 群聊的话确认你 **@了机器人**

### Q: DeepSeek API 返回错误？

打开 [platform.deepseek.com](https://platform.deepseek.com) → 用量管理，确认：
- API Key 没复制错
- 账户里有余额

### Q: 机器人被腾讯封了？

NapCatQQ 是逆向协议，有极小概率被风控。**一定要用 QQ 小号**，封了就换号。

### Q: 怎么换 AI 模型？

编辑 `config/bot.yaml`，把 `llm.provider` 从 `deepseek` 改成 `qwen`，然后重启：

```bash
docker compose down && docker compose up -d
```

### Q: 服务器内存不够用？

2 核 2G 足够跑这个项目。如果真的不够，可以在 `docker-compose.yml` 里限制：

```yaml
bot:
  deploy:
    resources:
      limits:
        memory: 512M
```

### Q: 想换端口？

编辑 `config/bot.yaml`：

```yaml
onebot:
  ws_port: 你想要的端口
```

然后 `docker compose down && docker compose up -d`。

### Q: 日志文件在哪里？

- Bot 日志：`docker compose logs bot`
- 服务器上文件：`data/logs/bot.log`
- QQ 消息在 Docker 容器外看不到——保护隐私

---

## 许可证

MIT License

## 致谢

- [GzSakura1337/ATRI-skills](https://github.com/GzSakura1337/ATRI-skills) — ATRI V3 角色引擎的原典研究
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ) — QQ 机器人协议支持
- 《ATRI -My Dear Moments-》— ANIPLEX.EXE / Frontwing / 枕
