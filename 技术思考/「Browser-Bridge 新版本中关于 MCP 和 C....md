---
title: "「Browser-Bridge 新版本中关于 MCP 和 C..."
source: "https://note.mowen.cn/detail/gCILAIpuZtWnxlPEZNrzY"
author:
published: 2026-06-30
created: 2026-06-30
description: "作者最初因担心MCP占用上下文窗口，选择CLI+SKILL方式集成Browser-Bridge，但发现模型不会自动调用SKILL。随着上下文窗口扩大至1M，MCP优势凸显，最终新版本拥抱MCP，认为优化不应提前做减法。 "
tags:
  - "Browser-Bridge"
  - "MCP"
  - "工具集成"
status: "published"
---
## 「Browser-Bridge 新版本中关于 MCP 和 C... · 墨问

**「Browser-Bridge 新版本中关于 MCP 和 CLI 取舍」**

新版本的 Browser-Bridge 支持了 MCP ，对于 Agent 来说，集成的方式更加丰富啦。

**为什么最开始我采用的是 CLI 的方式与 Agent 集成？**

这个问题其实是我的一个偏见。

当时，其实是受看过一篇文章的影响才做的这个决定。文章的具体内容，现在已经回想不起来了，只记得大致讲的是 MCP 集成过多，导致系统提示词太长，浪费了很多 token 的问题。

然后，我没想太清楚，就觉得如果我不使用 MCP 的方式，转而使用 CLI 的方式，那 Browser-Bridge 就能真正的做到按需加载。

**为什么 System Prompt 太多了不太好？**

并不是说会浪费很多token。因为一般 System Prompt 都是放在消息的头部，LLM API 都支持前缀匹配的输入缓存，如果命中缓存的话那这点内容基本不会花多少钱。

**真正的原因是上下文窗口很宝贵。**

Agent 在压缩上下文的时候，System Prompt 是不能被压缩的，只能压缩用户消息和工具调用的消息。（一旦 System Prompt 被压缩，那整个缓存就失效了，相当于你所有输入都要重头来计费）

而既然 System Prompt 不能被压缩，那在 System Prompt 中加载的东西越多，用户能使用的上下文就会越小。

正是因为有这样的考量，我才觉得得使用 CLI。

虽然，想法是有了，感觉也更好。但在实践过程中，遇到的问题可不少。

**如何让 Agent 知道现在需要使用这个 CLI 呢？**

我采用的方案是 **SKILL** 。通过写一个 SKILL，在它描述中告诉 Agent 有这样一个 CLI 工具，可以帮你操作浏览器。

这样做，相当于是在 System Prompt 中只保留很简短的一句话。在实际的 tool\_use 调用之后，才把本应该在MCP中暴露的工具描述加载到模型中。而且，这些内容还是以工具调用的结果出现的。

**Agent 无法在适当的时候自己唤起对工具的调用。**

虽然现在通过 SKILL + CLI 的方式可以缓解我上面提到的 System Prompt 过长导致上下文膨胀的问题。

但是，新问题也来了。

这里的 SKILL 描述的是一组功能，它们只能描述有哪些工具，而不能把什么场景用 SKILL 也列举完。

我发现，当我让 Agent 打开某个网页去查数据。它的第一优先级是使用 Chrome DevTools（这可能也跟我集成了 Chrome MCP有关）。如果行不通，就尝试写代码使用 Playwright 等方式去通过 CDP 协议操控浏览器来抓取，最后就直接回退到 WebSearch + WebFetch。

**模型似乎并不能默认就懂得，哪些场景需要去使用我定义的这个包含很多功能的 SKILL。**

所以，为了解释这个问题。我当时的想法是让用户通过 “/browser-bridge-user” 手动触发 SKILL，告诉模型要强制使用这个 Browser-Bridge 来操作 Chrome。

但是，这种需要手动触发的方式显得有些刻意。使用者需要自己判断使用哪种方式来操作chrome，比如：编码时需要使用 Chrome DevTools，搜索、填写表单时又要使用Browser-Bridge。这种不太“智能”的方式，让我心里感到有些不舒服。这种手动触发的方式，就像是在错误的假设上做事情，根本没能让LLM自主调用 Browser-Bridge。

后来，我读了一本书《像高手一样解决问题》，里面提到很多商业失败的案例中都有个隐含的假设（其实现在还没读完~~）。

**我突然发现，似乎之前也有个隐含的假设被我忽略了** —— **上下文现在很稀缺** 。如果上下文窗口是 20K 左右，你安装10多个 MCP 之后，确实就会占用 4K 左右的系统上下文（还不包括 SKILL），这样看上下文确实很稀缺。

但今夕何夕？大模型上下文的限制规则正在被模型厂商们修改。

他们都在大张旗鼓地支持 1M 上下文。当上下文的容量能扩张5倍，那我所做的这些优化其实用处不太大。

我又想了想，那篇文章似乎也是两个月前的。两个月后的今天，上下文容量已经是2个月前的5倍了。此时，MCP 的集成方式能更好的让模型理解工具的功能。

**然而，我又仔细回忆了下。发现每次 Agent 都会优先使用 Chrome MCP 来操作浏览器，那这会不会就是因为 MCP 的集成方式的优先级会高于 SKILL？**

所以，新版本中我支持了 MCP 来调用 Browser-Bridge。

（我彻头彻尾地推翻了之前的设计，打脸了~~。不过感觉这也是认知被刷新（加深）的一个过程。）

从怕浪费上下文，到拥抱 MCP，这个'打脸'的过程，本质上是我对'什么是真正的优化'的理解变了——优化不应该提前做减法，只要留足够大的空间就好，也许我预设的这个问题本就不是问题。

\--附录

Browser-Bridge:

[https://github.com/dkisser/browser-bridge](https://github.com/dkisser/browser-bridge)

![](../images/browser-bridge-xin-ban-ben-zhong-guan-yu-mcp-he-c/image-1.png)

