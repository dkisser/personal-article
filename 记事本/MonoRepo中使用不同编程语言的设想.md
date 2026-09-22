---
title: "MonoRepo中使用不同编程语言的设想"
source: "https://note.mowen.cn/editor/eF4YnroB-ESsjhI8yREb2"
author:
published: 2026-09-22
created: 2026-09-22
description: "作者在为 browser-bridge 设计控制面板时，想起 pinchTab 仅 28MB 且零依赖的安装体验，希望实现同样小巧便捷的方案。他推测 Go/Rust 编写的 HTTP 服务器体积极小，可直接托管 JS 前端，因此整体很小。项目目前用 MonoRepo 统一 Node.js 生态，共享协议层能在编译期发现契约变更，效率高。但作者不熟悉 Go/Rust，担心出问题难以排查，且多语言会让共享协议层失效。最终问题变成：跨语言 MonoRepo 如何方便开发。作者此前只用过 Java+JS，现在最喜欢 Node+JS，考虑尝试 Go。 "
tags:
  - "MonoRepo"
  - "Go/Rust"
  - "browser-bridge"
status: "published"
---
## MonoRepo中使用不同编程语言的设想

最近在考虑给 browser-bridge 加控制面板。在思考怎么做这个功能的时候，我想起了 pinchTab。

当时，我感觉它安装起来非常方便。一是安装包小到只有 28 MB，二是零依赖。

所以，我在想怎么样才能和它一样，把控制面板做的体积小且方便安装。

## Go 和 Rust 生态的优势

我第一时间想了解的就是， **为什么 Go 可以做到后端 + 前端 加起来才 28MB？**

按照我过去的开发经验来看，js编译之后虽然只有几MB，但却是需要安装在一个web容器里面。唯一的解释就是 **Go/Rust 编写的Http服务器本身就很小** ，而 js 就通过 Go/Rust 编写的 Http服务器来托管的，所以整体体积就很小。

## Bun的便捷

由于这个项目使用的是 MonoRepo 进行管理，前后端统一使用 Node.js 生态，非常方便。尤其是共享协议层，它可以保证当服务契约发生变更之后在编译期就能及时的发现问题（如果有的话）。

虽然 Go/Rust 非常好，但是我并不熟悉。一旦出现 Agent 也反复改不好的代码，我就只能两眼一抹黑。

而且一旦使用多个编程语言，那原有的共享协议层就失效了，感觉上是开发效率降低了。

所以，最终问题变为跨语言的 MonoRepo，怎么开发会比较方便~

之前只会java + js，现在最喜欢的是 node + js 。没有尝试过其它的组合。感觉可以尝试一下 Go，毕竟这个也是之前云原生盛行的产物，性能肯定是可以的。

字数 631 / 20000

<iframe allow="clipboard-write; web-share" src="chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/side-panel.html?context=iframe"></iframe>