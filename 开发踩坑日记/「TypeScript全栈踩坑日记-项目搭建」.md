---
title: "「TypeScript全栈踩坑日记-项目搭建」"
source: "https://note.mowen.cn/detail/QVYLgUrkRaY47s4GjPogG"
author:
published: 2026-05-25
created: 2026-05-25
description: "本文记录了使用 `create-fullstack-vite` 构建 TypeScript 全栈项目时遇到的坑：若选择默认选项“Yes”，工具会先启动前端并卡住，导致后端未安装。选择“No”则顺利搭建。作者最终选用 React + TypeScript 前端和 NestJS 后端，并分享了其他脚手架参考。 "
tags:
  - "TypeScript"
  - "全栈开发"
  - "踩坑"
status: "published"
---
## 「TypeScript全栈踩坑日记-项目搭建」 · 墨问

「TypeScript全栈踩坑日记-项目搭建」

第一次遇到这么坑的构建工具 -- create-fullstack-vite，构建了好几次才给它整明白。

怎么个事儿呢？我来复盘下~~

首先，当你输入下面指令进行构建的时候，会看到下面的内容

```
npx create-fullstack-vite@latest my-fullstack-demo
```

![](../images/typescript全栈踩坑日记-项目搭建/image-1.png) ![](../images/typescript全栈踩坑日记-项目搭建/image-2.png)

选择完前端和后端的框架之后，接着就来到了最坑的地方~~

![](../images/typescript全栈踩坑日记-项目搭建/image-3.png)

一旦你选了默认的 Yes，那项目会安装前端应用并启动。可前端一启动，控制台就停在了前端启动之后的地方。

等了一分钟，我感觉不对劲儿，怎么卡着不动了，难道安装完了？接着我用IDE打开项目，发现只安装了前端，后端没了~~

我中断前端的运行，又等了两分钟，发现没有任何事情发生。我感觉有点小不对劲儿，于是删掉项目重装。

这次选择 No，就很流畅了~~

![](../images/typescript全栈踩坑日记-项目搭建/image-4.png)

历时10分钟，还是把项目搭起来了，还是有点小开心~~

**关于技术栈。**

前端是React +TypeScript，这个我比较熟悉，而后端 NestJS,我看了下和 Spring 很像，所以用了这个。

其实还有其他全栈的脚手架工具，有兴趣的盆友可以参考下。

![](../images/typescript全栈踩坑日记-项目搭建/image-5.png)
