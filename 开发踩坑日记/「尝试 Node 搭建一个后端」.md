---
title: "「尝试 Node 搭建一个后端」"
source: "https://note.mowen.cn/detail/QUfWEaMw3RGZ9rMgsbNsf"
author:
published: 2026-06-25
created: 2026-06-25
description: "作者尝试使用Node搭建后端，采用Bun作为开发环境、Fastify和TypeScript构建Web服务，并添加PM2部署脚本。项目结构简单，旨在降低认知负担，提升代码可维护性和类型安全。 "
tags:
  - "Node.js"
  - "Bun"
  - "Fastify"
status: "published"
category: "开发踩坑日记"
---
## 「尝试 Node 搭建一个后端」 · 墨问

**「尝试 Node 搭建一个后端」**

昨天，前脚花了“大力气”去了解事件循环、动态语言的内存管理难题，后脚立马来活儿了。

这活儿也不难，就是一个简单的后端服务。包一个 Azure 的文件上传接口，以及调用 Lark 多维表格的 WebHook。

我：“需要考虑下后面的维护与集成吗？还是说简单弄弄？”

老板：“先简单弄弄吧”

我一想，这不就正正好好嘛~

花了一小时，弄除了个 Node 后端。为了让以后搭建这种项目能更方便点儿，我就把这个项目的依赖和结构简单整理了一下。

**运行时的环境和开发时环境配置**

运行时的环境肯定是用 Node。不过考虑到还需要部署，我又添加了一个 PM2 相关的部署脚本。

开发时的环境我使用的 Bun。之前调研过，发现JS生态中的 包管理、formatter、linter、tester、构建等过程都是分散的，每个环节都是一个单独的模块，认知量比较大。为了降低认知量，我直接使用 Bun。

bun 本身可以解决 包管理、构建、测试，再搭配一个 Biome 解决 formatter、linter ，即可满足我的需求。

**Web框架和类型安全**

我这里采用的 Fastify、TypeScript。同样是为了减轻认知负担，Fastify 比 Express 更轻量，更新，社区比较活跃。TypeScript 比较好的一点是可以设置强制的类型校验，如果设置好了linter，基本上写出的代码还是比较好懂（AI更容易懂）,后面也可以通过静态代码走读找到基础的字段缺失、类型错误等问题，而不一定必须要运行才能找到错误。

![](../images/尝试node搭建一个后端/image-1.jpg)

0

0

0

\\n

发布成功

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>