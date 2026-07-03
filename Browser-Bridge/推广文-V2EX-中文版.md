---
status: draft
tags: [Browser-Bridge, 开源, Agent, 浏览器自动化, V2EX]
created: 2026-06-23
published:
category: Browser-Bridge
channels: [V2EX]
---

# 做了一个浏览器插件，让你本地跑的任何 Agent 都能像人一样操控浏览器，告别 Kimi/Codex 的 App 绑定

## 背景

> 起因很简单：我想要 Codex / Kimi 浏览器那种"AI 帮我操作页面"的体验，但我不想被它们的 App 绑死。

最近几个月，"Agent 能操控浏览器"突然变成了大厂新功能的标配——Codex 桌面版能开浏览器替你点东西，Kimi 浏览器更是直接做成了一个独立 App，Dia、Arc Search 也都在卷这个方向。

体验是真的爽。但用着用着我就有点烦：

- 想让 **Claude Code** 写代码时顺手帮我去某个内网文档里查个登录态页面 → 它没这个能力
- 想在 **Dify / Coze** 工作流里加一步"打开淘宝订单页拿数据" → 没办法，工作流跑在云上，碰不到我本地的 Chrome
- 自己写个 **Langchain / Python 脚本** 想复用我已登录的 Chrome → 又得重新折腾 Playwright + 处理登录态

说白了：**"操控浏览器"这个能力，不应该是某个 App 的专属体验，它应该是所有 Agent 共享的一层基础设施。**

于是我做了 [Browser-Bridge](https://github.com/dkisser/browser-bridge)。

## 它是什么

一句话：**把你正在用的本地 Chrome，变成任何 Agent 都能调用的工具。**

<!-- GIF 占位：30 秒 demo —— Claude Code 通过 Browser-Bridge 操作我登录态的内网页面 -->

不是又造一个 Agent，是给所有 Agent 用的"浏览器手脚"。一处接入，全家通用。

## 为什么不用 Playwright / Browser-Use / Playwright MCP

这是我做之前自己问过的问题。简单对比一下：

| 维度 | Browser-Bridge | Playwright MCP | Browser-Use | Codex / Kimi 浏览器 |
|---|---|---|---|---|
| 用你**真实的** Chrome（带登录态） | ✅ | ❌ 新开 headless | ❌ 新开实例 | ✅ 但锁在自家 App |
| 协议中立，任何 Agent 可接 | ✅ | ✅（仅 MCP） | ❌ 框架绑定 | ❌ |
| 不开本地端口，仅出站连接 | ✅ | ❌ | ❌ | — |
| 安装复杂度 | 一条 curl + 装扩展 | 较高 | 中 | 装 App |

**核心差异在第一行**：Playwright 系方案都是"新开一个干净浏览器"，你的 Gmail、飞书、内部系统 cookie 它一个都没有。而 Browser-Bridge 操作的就是你现在这个屏幕上的 Chrome。

这意味着——**任何需要登录态的页面，Agent 都能直接帮你操作**。这是 Codex 和 Kimi 的浏览器最让人上瘾的点，也是 Playwright MCP 这类方案目前缺的那块拼图。

## 架构（30 秒看懂）

```
[ Agent / CLI / 脚本 ]
        ↓ WebSocket
[ 云端中转服务 ]
        ↓ WebSocket
[ 本地代理（你电脑上） ]
        ↓
[ Chrome 扩展（MV3）]
        ↓
[ 你正在用的那个 Chrome 标签页 ]
```

四层 WebSocket 链路，**全程仅出站连接**：
- 不开本地端口、不暴露内网
- Cookie / Session / 凭据**永远留在本地**，云端只转发指令，不碰数据
- 扩展强制认证注册，命令必须经服务器中转

对安全比较敏感的同学可以重点看下这一段，这是我设计时最纠结的地方。

## 30 秒上手

```bash
# 一键安装
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# 在 Chrome 里加载生成的扩展目录，启动后端

# 列出当前在线的浏览器
bridge browser:list

# 让它打开一个页面
bridge navigate https://github.com --browser <browser-id>
```

<!-- GIF 占位：安装到第一次 navigate 跑通 -->

## 几个真实用法

**1. 配 Claude Code 当编码助手**

我自己用得最多的场景。写代码时让 Claude Code 顺手去公司 Wiki / Jira / 内部 API 文档里查东西，因为它操作的是我登录过的 Chrome，权限完全没问题。仓库里自带了一个 Claude Code skill，开箱即用。

**2. 接 Dify / Coze 工作流**

工作流里加一个 HTTP / WebSocket 节点，就能让你云上的工作流"碰到"你本地的浏览器。比如让工作流每天早上自动打开几个内网仪表盘截图发钉钉。

**3. Langchain / 自己写脚本**

WebSocket 协议中立，任何语言任何框架都能接。三十行 Python 就能让你的脚本"借用"你的 Chrome。

**4. 当 MCP server 用**

社区已经有同学在我基础上桥了 MCP，理论上 Cursor / Cline / Claude Desktop 都能直接调。

## 我没做什么（说在前面）

- **不替代 Browser-Use 的 DOM 推理能力**。Browser-Bridge 是底层桥梁，要做"看懂页面再决定点哪"这类高级解析，得自己接 LLM。
- **不是云端浏览器**，它就是你本地的 Chrome，关电脑就没了。
- **目前 API 还比较薄**，navigate / 基础动作够用，复杂操作还在加。

诚实说边界，不画饼。

## 现状 & 求反馈

- MIT License，全栈 Bun + TypeScript
- 项目刚开始推广，目标是 100 用户 / 10 个真实反馈
- Roadmap、API 扩展完全跟着大家用得起来的真实场景走

仓库地址：**https://github.com/dkisser/browser-bridge**

如果你也觉得"浏览器操控不该被某个 App 锁住"，欢迎来踩两脚。Issue / PR / 吐槽都欢迎，**最希望听到的是"我想用它干 XX，但是缺 YY"** 这种具体场景反馈。

## 总结

Codex 和 Kimi 证明了"AI 操控浏览器"是杀手级体验，但他们把这个能力锁在了自家 App 里。Browser-Bridge 想把这层能力剥离出来，做成所有 Agent 都能用的中立基础设施——你已有的 Claude Code、Cursor、Dify、Langchain，甚至一个 curl 命令，都能直接接。

## 相关链接

- 项目仓库：https://github.com/dkisser/browser-bridge
- [[Browser-Bridge 推广日记（一）]]
