---
title: "「做了个有趣的小工具 Browser Bridge - 让浏..."
source: "https://note.mowen.cn/detail/SW8Wn8V2J8CIcy2FJ7gol"
author:
published: 2026-06-26
created: 2026-06-26
description: "Browser Bridge开源工具让AI代理通过WebSocket操控本地Chrome，利用登录态查看内网文档、抓取数据。无需新安装，支持Langchain、Python脚本。支持本地部署，MCP开发中。 "
tags:
  - "Chrome浏览器操控"
  - "AI代理集成"
  - "WebSocket桥梁"
status: "published"
category: "Browser-Bridge"

---
## 「做了个有趣的小工具 Browser Bridge - 让浏... · 墨问

**「做了个有趣的小工具 Browser Bridge - 让浏览器变成任意 Agent 都能调用的工具」**

最近几个月，"Agent 能操控浏览器"突然变成了大厂新功能的标配——Codex 桌面版能开浏览器替你点东西，Kimi 也做了 Kimi Work来做这件事儿，Dia、Arc Search 也都在卷这个方向。

体验是真的爽。但用着用着我就有点烦：

1\. 想让 **Claude Code** 写代码时顺手帮我去某个内网文档里查个登录态页面 → 它没这个能力

2\. 想在 **Dify / Coze** 工作流里加一步"打开淘宝订单页拿数据" → 没办法，工作流跑在云上，碰不到我本地的 Chrome

3\. 自己写个 **Langchain / Python 脚本** 想复用我已登录的 Chrome → 又得重新折腾 Playwright + 处理登录态。

说白了：我不想再装一个新的桌面 App。我想让我 **已经在用的** Claude Code、Cursor、Dify 工作流、或者一段三十行的 Python 脚本，能直接驱动 **我已经登录好的那个 Chrome** 。

于是我做了 [Browser-Bridge](https://github.com/dkisser/browser-bridge) ， **一个协议中立的桥梁** 。通过 WebSocket 把你本地真实的 Chrome 暴露成任何 Agent 都能调用的工具。

**架构**

```
[ Agent / CLI / 脚本 ]
       │ WebSocket（出站）
[ WS-Server 中转(目前仅支持本地部署，后续支持云端部署) ]
       │ WebSocket（出站）
[ 本地代理（你电脑上） ]
       │
[ Chrome 扩展（MV3） ]
       │
[ 你正在用的那个 Chrome 标签页 ]
```

**安装**

```
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# step1. 启动服务
bridge up

# step2. 安装chrome extension

# step3. 测试
bridge browser:list
bridge navigate https://github.com --browser <browser-id>

# Agent 集成（默认已经安装到cc的skill目录，使用 /browser-bridge-user即可唤起）
```

**使用Demo**

（下面的两张图点击才能查看）

![](https://priv-sdn-001.mowen.cn/mo/file/meta/22/69/67/2070391181018984450.gif?Expires=1782541099&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=YOywcQXA3goOHhBIabquJ4jjkcQ%3D&response-expires=Sat%2C%2027%20Jun%202026%2006%3A18%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

操作gmail

![](https://priv-sdn-001.mowen.cn/mo/file/meta/96/45/88/2070391181018984449.gif?Expires=1782541099&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=Hse6Jw18E1CZpN8O2wnjX%2FC9Ge8%3D&response-expires=Sat%2C%2027%20Jun%202026%2006%3A18%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

查资料

**Claude Code 变成真正的编码助手。** 可以让它去你已经登录的公司 Wiki、Jira、内部 API 文档里取信息，因为它操作的就是登录态的 Chrome。（仓库里自带 Claude Code skill）

**支持Langchain / 任意脚本。** WebSocket 协议中立，~30 行 Python 就够唤起。

**不替代 Browser-Use 的 DOM 推理。** Browser-Bridge 是传输和控制层。要做"看页面再决定点哪"，得自己接 Agent。

**不是云端浏览器。** 就是你笔记本上的 Chrome——电脑关了就没了。

**MCP支持。** 目前还在开发中，MCP可以更改的和 Agent 来集成。但目前通过SKILL其实也可以调用它，只是需要明显感知。（我在思考怎么才能让默认的浏览器操作能自动路由到 Browser Bridge，而不是 CDP 模式下的 Chrome。）

**Dify / n8n / Coze 工作流能碰到本地状态** 。目前这块儿我也没实现，理论上只要控制好鉴权即可让云端工作流节点"伸手"到你的本地浏览器（打开认证后的仪表盘、截图、推 Slack）。

仓库： [https://github.com/dkisser/browser-bridge](https://github.com/dkisser/browser-bridge)

![](../images/做了个有趣的小工具-browser-bridge-让浏/image-1.png)

1

0

0

\\n

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>