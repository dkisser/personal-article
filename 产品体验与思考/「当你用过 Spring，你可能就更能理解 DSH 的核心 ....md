---
title: "「当你用过 Spring，你可能就更能理解 DSH 的核心 ..."
source: "https://note.mowen.cn/detail/7Qp9SaEk3livcHqp03_LG"
author:
published: 2026-08-20
created: 2026-08-20
description: "作者体验 DSH：核心 Cordis 类似 Spring IoC 容器，用插件依赖管理替代硬编码。当前 API 不稳定、门槛高，若社区保持活跃，有望成为统一的 Agent 编程框架。"
tags:
  - "DeepSeek Harness"
  - "Cordis"
  - "插件"
  - "Spring"
  - "IoC"
status: "published"
---
## 「当你用过 Spring，你可能就更能理解 DSH 的核心... · 墨问

**「当你用过 Spring，你可能就更能理解 DSH 的核心 Cordis」**

上周末 DeepSeek Harness 刚出来的时候，我发现即刻上都是吐槽的。

“这明显是个玩具，准入门槛太高了”

“这么一个灵活的玩意儿，注定是技术人的自嗨”

然而到今天，我发现 github 上的 Star 数已经超过 16w+ 。也就是说，大家开始正视它了，我好奇，这样一个“技术人的玩具”怎么就逆转了口碑呢？

怀着好奇的心理，我使用源码部署的方式在本地安装了一个 DSH。

（本身在安装之前，我也看过很多公众号的介绍。我最感兴趣的其实就是 DSH 的插件体系，所以在这里我就不装了，摊牌了——我就是奔着了解 Cordis 去的。）

**动态装载插件**

既然 DSH 的理念是“一切皆插件”，那我就试试它能不能把我之前做的小工具 Browser-Bridge 给安装上来。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/73/13/69/2090099167844741126.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=rjV%2BPOqRvWggoIk7fWzW88Vm8bg%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

（这里补充下，Browser-Bridge 有 server 和 local-proxy 两个进程。server 负责管理浏览器, local-proxy 是作为本地机器的后台进程常驻的，主要为了保活和server的连接。）

我就这一句话，然后傻等10多分钟。我感觉是因为没有提前说明整个项目的结构的问题，最后我放弃了，主动告诉了它该怎么做。在我循循善诱下，最终还是搞出来了我第一个plugin。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/13/91/99/2090099167844741121.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=hLvvPKT0s%2BvDrtuwqyVJuXyQCiU%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

（经过一小时，终于注册成功了一个MCP...）

如果只是简单的 MCP，那我可能潜意识里把 MCP 和 DSH 的 plugin 花了等号，事实是这样吗？我在想，我是不是走错方向了？

随后，我到处点了点，发现 DSH 自己定义的插件有这么些。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/10/11/26/2090099167844741122.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=8BeHBIY7NIfMO0YPeG4TZ5udiS0%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

这里应该就是官网说的“一切都是插件”，如果这些地方都是可以替换的，那这个 Harness 确实也挺难得的。毕竟像 Claude Code、Codex 这种，你是只能通过 Hooks，或者事件来扩展功能，而不能替换原有的功能。

**Pi 和 DSH**

讲到灵活，这让我想起了 Pi。它不也是足够灵活吗？Pi 除了 Agent Loop 是固定之外，其他的地方都是可以通过事件回调来自定义的。如果 DSH 也提供了一套编程框架，那从这个角度来看，DSH 似乎和 Pi 的差别不大，所不同的只是编码风格以及编排流程的方式不一样。

难道真是这样？

**社区的 Plugin**

怀着疑问，我点开了 dsh-plugin 下面的项目。

我只找了几个之前在公众号看到过的，比较有名的项目，dsh-tui、dsh-web-ui、dsh-desktop。我发现他们都有类似的使用方式。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/10/33/79/2090099167844741125.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=qo7MZUcUsvclgntET3GD%2B3puAzk%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200) ![](https://priv-sdn-001.mowen.cn/mo/file/meta/15/19/60/2090099167844741124.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=48zmbT2ljEZK0rB3gsIYSucZpnM%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

每个子模块都有一个 cordis.patch.yml。同时，package.json 里面会有 dsh 相关的配置（bundle、client等）

具体代码在使用时又会有 effect、inject等。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/76/46/25/2090099167844741123.png?Expires=1787830381&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=8OrN4emxmyl8bMQwxP8Fn%2FhAwGM%3D&response-expires=Thu%2C%2027%20Aug%202026%2011%3A33%3A01%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

看到这里，我猜测整个 Cordis 做的就是加载 plugin。plugin 之间的依赖关系需要通过配置文件先声明，然后再在代码中 inject。 **DSH 把所有的抽象组件，通过 plugin 这个概念来组合，Cordis 可以看做管理 plugin 的 Ioc 容器。**

等等，这里好熟悉。Java 中 Spring 早期的版本中不也是这样吗？只不过 Spring 是通过 xml 来约定对象之间的依赖关系，然后进行对象的生命周期管理。

而 Cordis 面向的是一个个功能模块，所以它只提供一个 Context, 把整个容器的引用（如果了解 Spring 的朋友，可以把这里理解成 ApplicationContext）提供给开发者，由开发者自己决定 inject/provide 的具体内容（可能是某个plugin中的部分共享对象）。

如果把 Agent\_Loop、Context、Session、tool等都看做作抽象的 plugin，plugin 自己选择依赖谁以及如何加载、何时加载，那这一切就都说得通了。

我想起在构建 Spring 应用时，我需要按部就班地集成 web、logger、test、mybatis。但仔细回想，发现其实这些功能模块也不一定都需要，完全都是按需集成。只是因为后端的需求常常和这些模块绑定，并不是 Spring 只能这样使用。

感觉 Cordis 似乎想做和 Spring 一样的事情。提供一个统一的开源 Agent编程框架，降低 Agent 的构建门槛。

**但就目前的状况来说，DSH 的灵活性和降低 Agent构建门槛似乎完全不沾边。** 项目还在很早期，底层 API 未必稳定，而且各种层出不穷的扩展实现，很容易让人摸不着头脑。

**社区的力量**

不过，当你使用 Spring 作为应用底座去集成时，你会发现你几乎不太需要了解底层的实现细节。比如：web 模块的实现到底使用 Tomcat 还是 Jetty ，或者是 Undertow？logger 模块到底使用了 logback，还是 log4j？

换到 Agent 构建中来看，也是如此。比如：我想解决上下文压缩的问题，但是现在上下文压缩的策略几乎都是各家各自实现，没有专门解决上下文压缩的一个包。记忆也是，各种记忆系统的使用都有各自的API，集成到Agent后，就很难替换。如果，在此之后有层抽象的中间包，能屏蔽底层的具体实现细节，那就真正地做到了可拔插。

按照这个思路来看，如果 DSH 的社区能保持活跃，这个还是很有机会的。毕竟现在做 Agent开发 的时候，几乎都是自己从头定制到尾，从来没有想到过能有一个类似中间件的模块。

0

0

0

\\n

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>