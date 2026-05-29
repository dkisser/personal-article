---
title: "「TypeScript全栈踩坑日记-文章管理系统的迭代」"
source: "https://note.mowen.cn/detail/l-UnhkyGUgX2KRhpMnqTa"
author:
published: 2026-05-26
created: 2026-05-26
description: "作者使用TypeScript全栈快速构建文章管理系统，基于AI辅助从需求到实现仅约40分钟。后续微调配色、图标，解决Markdown渲染等问题，整体迭代约1.5小时。项目主要满足个人习惯，情绪价值大于经济价值。 "
tags:
  - "TypeScript"
  - "全栈开发"
  - "文章管理"
status: "published"
---
## 「TypeScript全栈踩坑日记-文章管理系统的迭代」 · 墨问

「TypeScript全栈踩坑日记-文章管理系统的迭代」

既然是练手，那我肯定找个简单的。

之前 Karpathy 的个人知识库还比较火的时候，我自己弄了个。最开始感觉不错，但是我发现之前剪藏之后，没有把图片下载并替换里面的图片，现在就弄个可视化的地方来管。

（可能是个人习惯。虽然 Obsidian 好用，但是我仍然习惯打开网页~。我嫌打开 Obsidian比较麻烦，但是打开浏览器时就没这个感觉）

**Run fast and Run first**

我习惯先把先后端的功能构建出来，然后再去边看边调。

（用 brainstorming 阐明需求，然后 /bg，接着就可以划水去啦）

![](https://priv-sdn-001.mowen.cn/mo/file/meta/16/21/12/2059114914768461827.jpeg?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=D%2Bi2dbzhRYP3uvDXPXrxMBEaQ5Y%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

**并不是说不需要设计，而是说要保持设计的简单。** 最近我越来越发现，很多事情做着做着到后面要么发现行不通，要么发现之前的假设就是错的。分享下之前我收藏的一句话。

AI 并没有增加了我们成功的机率。而且，它产生了更多的垃圾。但是，它让我们失败的速度变快了，我们能更快的验证自己不成熟的想法。

**修改最不能忍受的点** 。

我发现生成的页面没有任何颜色，纯黑白，极致的复古（ugly）~

![](https://priv-sdn-001.mowen.cn/mo/file/meta/11/16/59/2059114914768461825.jpg?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=ynWNAmtRE6fQxhoHcNkjin7yd60%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

这里的优化也比较简单，找一个 design prompts 丢进去就好啦。我选择的是 Organic/Natural 风格。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/16/94/43/2059114914768461828.png?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=1j%2BXNqV%2B%2B8HYBsOHeI4tuymalv8%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

页面看着有模有样的~，可是查看文章的时候，发现我剪藏的markdown文章的样式没有渲染、图片没有渲染。（我选择让AI自己去修复，去改，就不赘述了）

我感觉这页面好像能用，但是有感觉整体不平衡，这时我考虑是不是需要一些 Icon。

![](https://priv-sdn-001.mowen.cn/mo/file/meta/82/95/97/2059114914768461829.jpg?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=94mm2kw4czxx0RHKuvkdhXykJPY%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

优化过后，顺手能改的地方基本已经改掉了，现在再看看？

![](https://priv-sdn-001.mowen.cn/mo/file/meta/51/78/75/2059114914768461824.png?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=mpmjwi6pPXL6UbFFSmQg9Xf7b3Y%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

看着人模狗样的~~，不过能解决自己的需求就好。

整个项目大概也就一个半小时左右。最开始的构建花了40分钟（阐明需求10多分钟，实现花了27分钟），后面这些小地方的微调，每次也就几分钟（反正肯定在10分钟之内）

![](https://priv-sdn-001.mowen.cn/mo/file/meta/12/87/97/2059114914768461826.jpg?Expires=1779852627&OSSAccessKeyId=LTAI5tE16jzdfWCPVBmyB5Nn&Signature=axvtB8v5SEfsjtgIV1Xj%2BSqhMuo%3D&response-expires=Wed%2C%2027%20May%202026%2003%3A30%3A27%20GMT&x-oss-process=image%2Fresize%2Cw_1200)

今天的失败案例就这样啦~（本身Obsidian其实已经有可视化而且做的双向链接以及可视化都很好，我只是习惯打开网页所以做这个项目。并不是项目本身有经济价值，更多的是情绪价值）

\---附录

Design Prompts: [https://www.designprompts.dev/](https://www.designprompts.dev/)

Lucide: [https://lucide.dev/](https://lucide.dev/)

0

0

0

\\n

<iframe src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>