---
title: "「复刻Codex浏览器插件-鉴权篇」"
source: "https://note.mowen.cn/detail/xRi0eRIHvB7YyM26H1mlc"
author:
published: 2026-06-15
created: 2026-06-15
description: "作者复刻Codex浏览器插件，完成核心功能后着手完善鉴权和网络通讯。最初设计了三个端到端鉴权，但意识到本地部署的localhost环境相对安全，跨网络的端点才需鉴权，最终只保留Local-Proxy到Ws-Socket鉴权。作者认为Agentic Coding可快速验证想法，但这要求开发者相信自己的方案优于AI。 "
tags:
  - "Codex浏览器插件"
  - "鉴权"
  - "Agentic Coding"
status: "published"
category: "产品复刻"
---
## 「复刻Codex浏览器插件-鉴权篇」 · 墨问

**「复刻Codex浏览器插件-鉴权篇」**

昨天把 Codex 浏览器插件最关键的功能做出来了，虽然还是有很多瑕疵，但我认为这是 Agentic Coding 带来的好处。它可以让我们快速验证我们的想法，想法验证可行之后再继续做一些工程上的优化，可以最大程度上降低我们的试错成本。

**今天我们完善下鉴权和网络通讯。**

最开始，我认为只要有端到端的通讯就必须要有鉴权，不管是账号密码或者是自定义 Access Key。于是乎，我让 Agent 按照我的思路来设计了 Extension -> Local Proxy、Local Proxy -> Ws-Socket、Ws-Socket -> CLI 三个鉴权。

![](images/复刻codex浏览器插件-鉴权篇/image-1.png) ![](images/复刻codex浏览器插件-鉴权篇/image-2.png) ![](images/复刻codex浏览器插件-鉴权篇/image-3.png)

1/3

但是，在跟 Agent 聊天的过程中（打字的过程中），我突然间意识到，如果两个端部署在一起，走 Localhost 网络，那本身就是一个想当安全的环境。

**真正不安全的端对端通讯，是那些跨网络的端点。**

所以，我让 Agent 去掉了其他的鉴权，只保留了 Local-Proxy -> Ws-Socket 的鉴权。

![](images/复刻codex浏览器插件-鉴权篇/image-4.png)

现在真有点掌控感了~，这个设计完全由自己做，Agent 做实现。

但是，也不得不承认，这也有局限性，就是你一定要相信自己的方案比 Agent 设计的更好。
