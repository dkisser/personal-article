---
title: "「一个 setTimeout 引出了事件循环问题，这个事件循..."
source: "https://note.mowen.cn/detail/YLrfr7kXUAyDQJWQfWv6D"
author:
published: 2026-06-24
created: 2026-06-24
description: "从setTimeout泄露bug入手，揭示事件循环本质：单线程死循环处理任务队列。探讨动态语言为何难以多线程，以及事件循环适合前端却不适合大规模后端的原因。"
tags:
  - "事件循环"
  - "JavaScript"
  - "动态语言"
status: "published"
---
## 「一个 setTimeout 引出了事件循环问题，这个事件循... · 墨问

**「一个 setTimeout 引出了事件循环问题，这个事件循环到底是个啥？」**

昨天，在使用 Browser-Bridge 的时候，我发现每次执行浏览器指令时都是数据返回后还会等几秒才结束命令行。我就奇怪了，为什么别的 shell 命令执行时都是数据返回之后立马结束，而 bridge 命令会有明显的延迟？

好吧，让 Coding Agent 先看看，修复然后给我一个结论。

输入之后，我就去活动活动，舒展筋骨，喝了口水。

等我回到工位，我发现问题修复了。仔细一看，代码就改了一行，但总结却说了一大堆什么的，唯一让我印象深的是“事件循环”。

```
function waitForOpen () => {

  // 每 50ms 轮询一次 readyState
  const check = setInterval(() => {
    if (readyState === OPEN) {
      clearInterval(check);
      clearTimeout(timeout);   // 修复后才有
      resolve();
    }
  }, 50);
  // 5 秒后认为连接失败
  const timeout = setTimeout(() => {
    clearInterval(check);
    reject(new Error('Connection timeout'));
  }, 5000);

}

  using client = new ManagedClient(options.server);  // ← 块作用域开始
  await client.waitForOpen();
```

我想着“这是啥？之前 python 项目里面似乎也有”看来这个概念是逃不掉的，得学~~

**神秘的事件循环就是一个死循环**

开始还以为是什么特别复杂的概念。一搜，发现这个的意思是在说执行代码的时候是单线程死循环，不停地执行任务队列中的任务。

拆成两部分就好理解了。事件指代的是待处理的任务（定时器、I/O、交互事件等等几乎所有方法调用都可以认为是事件），循环就是死循环~

**或者，你把它理解为一个生产-消费者模型。** 事件循环指的就是用 while(true) 这样的方式不停地处理所有的消费者事件。

那回到刚刚的问题，这代码怎么就导致事件循环不能正常处理了呢？或者，为什么会延迟几秒呢？

```
// 每 50ms 轮询一次 readyState
const check = setInterval(() => {
  if (readyState === OPEN) {
    clearInterval(check);
    clearTimeout(timeout);   // 修复后才有
    resolve();
  }
}, 50);
```

setInterval 里面在修复之前时没有 clearTimeout 的，所以主循环就会等待5s，超时之后才会继续执行，所以 Agent 跟我是事件循环导致有5s延迟，实际上是因为 setTimeout 泄露了。

这 Agent 把这理解的高度整的也太高了，直接整到了底层线程执行模型了！

但这，气氛都烘到这儿了，我突然又开始好奇了。 **为什么 Java 可以多线程执行？我在 JavaScript 和 Python 中能看到这样的语法，但底层都是事件循环，并不是多并发？**

点击链接查看和 Kimi 的对话 [https://www.kimi.com/share/19ef8a09-74c2-822a-8000-00005616b379](https://www.kimi.com/share/19ef8a09-74c2-822a-8000-00005616b379)

有兴趣的看看我和Kimi的对话，这里我简短点儿讲就是因为动态类型的语言， **动态语言没法确定内存里面每个引用其后对象的大小** 。因为这一秒这个对象是 int，下一秒变 dict，内存不能预测，这导致无法做精确的逃逸分析、锁省略、无锁数据结构——编译器不知道指针会逃向何方，所以，只能放弃多线程。

**难道经常说后端不能使用动态类型的语言是因为这个性能问题？**

单纯从事件循环的CPU利用效率来看，其实它是高于多线程的。为什么很少人拿它做一些大规模的后端（基础设施）服务？

关键问题我觉得有两个。

一是响应不稳定。遇到高并发之后，如果某任务中需要使用较多的CPU，那后续任务就会被阻塞。

二是硬件资源浪费。现在的CPU都是多核，如果一个64核的CPU只能用一个核，那这相当于在花钱打水漂。

**那为什么又适合前端呢？**

我能想到的一种合理的解释就是，DOM并发操作的问题。最初的设计者也许是发现并发操作（渲染）DOM会有大量的锁冲突，还不如单线程提升对单核CPU的利用率。

\--附录

点击链接查看和 Kimi 的对话 [https://www.kimi.com/share/19ef8a09-74c2-822a-8000-00005616b379](https://www.kimi.com/share/19ef8a09-74c2-822a-8000-00005616b379)

Browser-Bridge: [https://github.com/dkisser/browser-bridge](https://github.com/dkisser/browser-bridge)
