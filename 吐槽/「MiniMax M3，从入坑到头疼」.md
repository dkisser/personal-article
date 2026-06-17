---
title: "「MiniMax M3，从入坑到头疼」"
source: "https://note.mowen.cn/detail/CM0AwYjiHfEsnTQxT4WW2"
author:
published: 2026-06-17
created: 2026-06-17
description: "作者尝试用MiniMax M3模型为Browser-Bridge添加安装脚本和Chrome扩展发布流程，结果模型拆解出19个任务，执行极其缓慢，todo状态更新延迟，浪费大量时间，最终切换到GLM 5.2。 "
tags:
  - "MiniMax M3"
  - "模型体验"
  - "效率吐槽"
category: "吐槽"
status: "published"
---
## 「MiniMax M3，从入坑到头疼」 · 墨问

不知道是不是昨晚睡得比较好，今早起来感觉特别精神，心情也特别好。

正好赶上公司给发的 Qoder 额度刷新了，想着今天来用用 MiniMax M3，看看这家的模型到底怎么个事儿。

**事实证明，好奇不仅仅是害死了猫，它还浪费了我大量的时间。**

我让他给我的 Browser-Bridge 添加一个安装脚本以及 Chrome Extension 的发布流程。这事儿本身听着很简单，在用 Super Power 对齐了想法之后，发现大概有 github pipline、调整代码、编写shell 这三块儿。

我也没仔细看设计,就开干了。过了一小时，发现居然给我拆了19个task出来。

![](images/minimax-m3-从入坑到头疼/image-1.png)

拆就拆吧，按我的经验，一小时怎么只有3个任务完成了？这任务这么难吗？我网上翻了翻，发现已经进入第5个任务了，但是todo的状态没及时更新。。。

![](images/minimax-m3-从入坑到头疼/image-2.png)

好吧，我想着，有点小毛病也正常，不更新todo而已啦。接着我又去给龙虾写定时任务的 Prompt，等我写完，差不多也是午饭时间了，我打开终端一看，我人都傻了~~

![](images/minimax-m3-从入坑到头疼/image-3.png)

搞了半天，还有这么多任务要做！这慢的太离谱了吧，我用 Qoder 的其他模型，也没这样啊？

我是啊啊啊！痛，痛，痛，急的头痛。

我果断切到了刚上线的 GLM 5.2

![](images/minimax-m3-从入坑到头疼/image-4.png)

先跑着看看吧，虽然 thinking 模式目前没让开，但是有 1M 上下文用也不错。
