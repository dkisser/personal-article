---
status: draft
tags: [Browser-Bridge, 开源, Agent, 浏览器自动化, HackerNews]
created: 2026-06-23
published:
category: Browser-Bridge
channels: [HackerNews-CN]
---

# Show HN：Browser-Bridge —— 把你真实的 Chrome 变成任何 Agent 都能调用的工具

## 背景

HN 风格的中文版。基调更克制——直接抛问题、给架构、讲安全模型、明确边界。如果要发到 HN 中文社区（如 ITSocial、HackerNews 翻译站、即刻 / 少数派的"硬派"专栏），用这个版本。

## 正文

各位好，

我做了 [Browser-Bridge](https://github.com/dkisser/browser-bridge)，原因是过去一年里"让 AI 开浏览器"——大概是 Agent 领域最实用的能力——一直在以"和某个 App 深度绑定"的方式发布：OpenAI 的 Codex 桌面浏览器、Kimi 的独立浏览器、Dia、Arc Search……都是。

我不想再装一个新 App。我想让我**已经在用的** Claude Code、Cursor、Dify 工作流、或者一段三十行的 Python 脚本，能直接驱动**我已经登录好的那个 Chrome**。

Browser-Bridge 就只做这一层：一个协议中立的桥梁，通过 WebSocket 把你本地真实的 Chrome 暴露成任何 Agent 都能调用的工具。

<!-- GIF 占位：30 秒 demo —— Claude Code 通过 Browser-Bridge 在我已登录的内网仪表盘里取数据 -->

## 为什么不直接用 Playwright / Playwright MCP / Browser-Use

合理的问题——我动手写代码之前自己问过。

| | Browser-Bridge | Playwright MCP | Browser-Use | Codex / Kimi 浏览器 |
|---|---|---|---|---|
| 驱动**你正在用的** Chrome（带登录态） | 是 | 否，新开 headless | 否，新开实例 | 是，但绑死自家 App |
| 协议中立，任何 Agent 可接 | 是 | 仅 MCP | 框架绑定 | 否 |
| 不开本地入站端口，仅出站 WebSocket | 是 | 否 | 否 | — |
| 安装 | 一条 curl + 加载扩展 | 较重 | 中等 | 装 App |

第一行就是全部重点。Playwright 系方案都是新开一个干净浏览器——你的 Gmail、Notion、内部 SSO、公司 VPN cookie 一个都不在里面。Browser-Bridge 驱动的就是你屏幕上正在用的 Chrome 窗口。这正是 Codex/Kimi 浏览器体验"魔法感"的来源，也是开源替代方案一直缺的那块拼图。

## 架构

```
[ Agent / CLI / 脚本 ]
       │ WebSocket（出站）
[ 云端中转 ]
       │ WebSocket（出站）
[ 本地代理（你电脑上） ]
       │
[ Chrome 扩展（MV3） ]
       │
[ 你正在用的那个 Chrome 标签页 ]
```

四跳 WebSocket，**全程仅出站连接**：

- 不开任何本地入站端口
- Cookie / Session / 凭据**永不离开本机**——中转服务只转发指令，看不到数据
- 扩展必须认证后注册；指令必须经中转服务

威胁模型大致是："我信任自己的机器和 Chrome profile；不希望暴露任何本地端口；即使中转服务被攻破，攻击者也读不到我的会话。" 这是我花时间最多的部分，欢迎在评论里继续撕。

## 30 秒上手

```bash
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# 在 Chrome 中加载生成的扩展目录，启动服务

bridge browser:list
bridge navigate https://github.com --browser <browser-id>
```

<!-- GIF 占位：从安装到第一次 navigate -->

## 它解锁了什么

- **Claude Code 变成真正的编码助手**：让它去你已经登录的公司 Wiki、Jira、内部 API 文档里取信息，因为它操作的就是登录态的 Chrome。仓库里自带 Claude Code skill。
- **Dify / n8n / Coze 工作流能碰到本地状态**：云端工作流节点终于可以"伸手"到你的本地浏览器（打开认证后的仪表盘、截图、推 Slack）。
- **Langchain / 任意脚本**：WebSocket 协议中立，~30 行 Python 就够。
- **MCP**：可以无缝包成 MCP server，给 Cursor / Cline / Claude Desktop 用。

## 它刻意不做的事

- **不替代 Browser-Use 的 DOM 推理。** Browser-Bridge 是传输和控制层。要做"看页面再决定点哪"，自己接 LLM。
- **不是云端浏览器。** 就是你笔记本上的 Chrome——电脑关了就没了。
- **API 表面还很薄。** navigate 和基础动作可用，更丰富的 DOM 操作根据真实需求逐步加。

宁可如实说边界，不愿过度承诺。

## 现状

- MIT，全栈 Bun + TypeScript
- 个人项目，刚开始推广；目标 100 用户 + 10 个真实反馈
- Roadmap 由真实工作负载驱动

仓库：**https://github.com/dkisser/browser-bridge**

最有价值的反馈是："我想用它做 X，但缺 Y。" 也欢迎挑战威胁模型——那是我最不确定、最希望被挑战的部分。

谢谢！

## 总结

Codex 和 Kimi 证明了"AI 操控浏览器"是杀手级体验，但他们做成了封闭 App。Browser-Bridge 把这一层抽出来，做成中立基础设施，让任何 Agent ——Claude Code、Cursor、Dify、Langchain，乃至一条 curl 命令——都能驱动你真实的、已登录的 Chrome。

## 相关链接

- 仓库：https://github.com/dkisser/browser-bridge
