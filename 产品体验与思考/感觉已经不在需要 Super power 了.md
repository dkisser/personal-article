---
title: "感觉已经不在需要 Super power 了"
source: "https://note.mowen.cn/editor/hS2gdo77Z-0S-qervahuJ"
author:
  - "[[叫我Paul就好]]"
published: 2026-09-09
created: 2026-09-09
description: "作者两周未用 Super power：Grill 已被 mattpock/skills 单独替代；流程冗长使单 feature 从半小时涨到 1–6 小时；Kimi K2.7 等模型已能搞定小功能，返工减少；订阅中可用 K3 后复杂任务也不再依赖它。"
tags:
  - "Super power"
  - "效率工具"
  - "模型升级"
status: "published"
---
不知不觉已经两个星期没有用过 Super power了，为什么我会感觉自己不再需要它了？

## Grill

我使用 Super power时，很大的程度上是想使用它的 Grill。这个讨论的过程，不仅可以让我更加清楚自己在构建什么，而且还能让LLM更清楚地了解构建模糊不清的内容写清楚，让我的理解和模型的理解尽可能的对齐。

但，我最近发现 mattpock/skills 把 grill 这个过程单拎出来了，所以如果只是想用grill，那完全就不需要使用Super power

## 冗长的研发流程

使用Super power就一定要遵守它定好的研发流程。每个拆分出来的任务都得使用 Sub agent 来执行，并且每个任务都会执行完整的 TDD + CR。而当所有任务都完成之后，还会有一个整体的CR。

这套流程在我最开始使用的时候，耗时也不长。大概一个 feature 跑下来，半小时。但，上个月更新之后我发现，每个 feature 的执行时间变成了1小时，重构类功能更是跑了到了6小时。

这个时间已经完全超出我的能忍受的范围。这迫使我必须使用多workspace来开发，但国内的 Coding Plan 又会限制并发数，所以我也最多只能两个workspace同时进行。很多时候，我都在等他跑完。

## 模型智能的提升

我在小的 feature 上也使用 Super power，很大程度上是因为当时的模型还不够聪明。但是，最近我发现，Kimi K2.7 和 Minimax M3等档位的模型也已经足够完成小的功能了，返工的次数相比两个月之前少很多了。

## 可用的顶级模型

K3出来之前，国内的模型很大程度上还是不在第一梯队上。有些复杂的前端动效、项目的重构，在使用 K2.7或者Minimax M3去做的时候，总会有漏的地方，而且实现出来也不太对，总是会返工。

现在，我的订阅套餐里面已经能使用K3了，所以，就更加没场景需要使用 Super power了。

字数 830 / 20000

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>