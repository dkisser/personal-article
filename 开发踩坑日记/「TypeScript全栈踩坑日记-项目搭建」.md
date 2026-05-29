---
title: 「TypeScript全栈踩坑日记-项目搭建」
source: https://note.mowen.cn/detail/QVYLgUrkRaY47s4GjPogG
author:
published: 2026-05-25
created: 2026-05-25
description: "作者使用 create-fullstack-vite 搭建 TypeScript 全栈项目时遇到坑：选择默认 Yes 会只安装前端并卡住，后端丢失；选择 No 则顺利。最终成功搭建，技术栈为 React + TypeScript + NestJS。 "
tags:
  - TypeScript
  - 全栈
  - 踩坑
status: published
---
## 「TypeScript全栈踩坑日记-项目搭建」 · 墨问

「TypeScript全栈踩坑日记-项目搭建」

第一次遇到这么坑的构建工具 -- create-fullstack-vite，构建了好几次才给它整明白。

怎么个事儿呢？我来复盘下~~

首先，当你输入下面指令进行构建的时候，会看到下面的内容

```
npx create-fullstack-vite@latest my-fullstack-demo
```

![](https://priv-sdn-001.mowen.cn/mo/file/meta/77/24/29/2058743937542881281.png?Expires=1779764179&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=6KpclM0biPGVUK655j3MZUtG1Ek%3D&response-expires=Tue%2C%2026%20May%202026%2002%3A56%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200) ![](https://priv-sdn-001.mowen.cn/mo/file/meta/14/99/62/2058743937542881284.png?Expires=1779764179&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=rJOro0AO3SmIELbM2r5EGrP5crc%3D&response-expires=Tue%2C%2026%20May%202026%2002%3A56%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

选择完前端和后端的框架之后，接着就来到了最坑的地方~~

![](https://priv-sdn-001.mowen.cn/mo/file/meta/69/23/52/2058743937542881283.png?Expires=1779764179&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=P5FP6FiRelW%2FL9KGy4NHI936q5c%3D&response-expires=Tue%2C%2026%20May%202026%2002%3A56%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

一旦你选了默认的 Yes，那项目会安装前端应用并启动。可前端一启动，控制台就停在了前端启动之后的地方。

等了一分钟，我感觉不对劲儿，怎么卡着不动了，难道安装完了？接着我用IDE打开项目，发现只安装了前端，后端没了~~

我中断前端的运行，又等了两分钟，发现没有任何事情发生。我感觉有点小不对劲儿，于是删掉项目重装。

这次选择 No，就很流畅了~~

![](https://priv-sdn-001.mowen.cn/mo/file/meta/10/50/55/2058748038779146241.png?Expires=1779765157&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=OqW%2Bh%2BHaRM0%2FNH%2FKP72lzlvE%2BYQ%3D&response-expires=Tue%2C%2026%20May%202026%2003%3A12%3A37%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

历时10分钟，还是把项目搭起来了，还是有点小开心~~

**关于技术栈。**

前端是React +TypeScript，这个我比较熟悉，而后端 NestJS,我看了下和 Spring 很像，所以用了这个。

其实还有其他全栈的脚手架工具，有兴趣的盆友可以参考下。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/14/39/59/2058743937542881282.png?Expires=1779764179&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=aTUTzV8omGXAhjoy2qQsKE7%2FjNc%3D&response-expires=Tue%2C%2026%20May%202026%2002%3A56%3A19%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

0

0

0

\\n

<iframe src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>