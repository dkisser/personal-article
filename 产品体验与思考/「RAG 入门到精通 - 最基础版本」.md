---
title: "「RAG 入门到精通 - 最基础版本」"
source: "https://note.mowen.cn/detail/uKu2JwSFEWpLgv3Pcub3w"
author:
published: 2026-07-21
created: 2026-07-21
description: "作者因工作焦虑浏览招聘网，发现RAG技术成为Agent工程师的热门要求，于是从零搭建RAG系统。他以手冲咖啡选豆场景为例，从MVP开始：先确定店铺助手场景，再收集咖啡豆及店铺数据，最后用Chroma整合到LLM上下文。系统搭建后，作者指出生产环境需要更成熟的架构和评估优化系统。 "
tags:
  - "RAG入门"
  - "向量数据库"
  - "咖啡助手"
status: "published"
---
## 「RAG 入门到精通 - 最基础版本」 · 墨问

前两天，我觉得工作有些不太稳定。于是打开了 Boss，想看看市面上有什么好的工作机会，给自己找找后路。

这不看还不打紧，看过之后发现，岗位的要求怎么都这么高？

全栈和Agent开发都是要求有2~3年的相关工作经验要求。我想着，这全栈工程师嘛，确实得要求相关工作经验比较多，毕竟工作栈比较多，需要时间沉淀。

可这 Agent 不也才火1年多点儿吗？怎么连 Agent 工程师也要求有2~3年的相关工作经验？这还得要求求职者提前布局是咋滴？

好吧~吐槽归吐槽。我还是发现这些要求的技术栈中有个跟向量数据库相关的技术-RAG ，我没太用过。

趁着最近有空，我开始尝试本地构建。

**MVP**

我认为做RAG也应该从最小的可用系统开始做。毕竟技术的进化本质是一个循序渐进的过程，刚开始的时候从MVP入手，持续得到激励，可以让兴趣保留的时间长久点~

**RAG的第一步**,我感觉不是做技术选型。应该是 **找到一个使用场景** ，然后针对这个场景进行系统设计。

这不，我最近大半年喜欢上了手冲咖啡。很多时候我不太会选豆子，都是看小红书或者淘宝的推荐。但是，推荐的豆子，里面的很多参数我都看不懂。产地、豆种、烘焙程度、风味等等，看的头都是大的。

所以，一开始我想做一款能帮我选豆子的Chat Bot。但是，真实的场景中其实不太会为这个场景单独设计一个 Chat Bot，更多的场景应该是作为一个店铺助手，帮助客户了解店铺以及店铺的场景。

**RAG的第二步，收集数据。** 既然我的目的是设计一个店铺助手，那我应该是找到一款产品以及其背后的店铺相关的信息。我从淘宝上找到了我之前喝过的一款豆子，接着我又把它背后的店铺信息也抓取下来。

然后，考虑到有时候会有冲煮的建议，我让AI生成了一份针对不同烘焙程度的豆子的冲煮技巧。

**RAG的第三步，整合进LLM的上下文里面。**

代码我就不贴了，Chroma + 自定义 Pipline（使用 LangChain也行）。有兴趣的可以看我的git([https://github.com/dkisser/rag\_learn](https://github.com/dkisser/rag_learn)).

这个MVP只是起点。我觉得需要知道面向大规模生产环境使用的话肯定不是这样的架构，毕竟Chroma不适合生产环境去使用。

而且，RAG其实又很多进阶技巧（ [https://milvus.io/docs/zh/how\_to\_enhance\_your\_rag.md](https://milvus.io/docs/zh/how_to_enhance_your_rag.md) ）。一个成熟的RAG，不应该是有系统本身，还应该需要配合一些评估系统去不停地迭代优化。

0

0

0

\\n

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>