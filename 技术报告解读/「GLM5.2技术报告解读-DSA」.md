---
title: "「GLM5.2技术报告解读-DSA」"
source: "https://note.mowen.cn/detail/8zstv0ZhrGQwqef8YxCw2"
author:
published: 2026-06-29
created: 2026-06-29
description: "本文详细解读了GLM5.2技术报告，重点介绍了DSA（DeepSeek Sparse Attention）及其相关优化，包括MTP（多token预测）、Indexer Share、KV Share、Rejection Sampling和端到端TV Loss。这些技术降低了计算成本，并将MTP接受长度从4.56提升至5.47，实现了20%的提升。 "
tags:
  - "DSA"
  - "GLM5.2"
  - "稀疏注意力"
status: "published"
---
## 「GLM5.2技术报告解读-DSA」 · 墨问

**「GLM5.2技术报告解读-DSA」**

之前发布的解读报告虽然没有深入，但是也大致抛出一些概念，今天就花点力气来试图和大家一起理解这些概念。 **全文大概10分钟左右的阅读时间，如果不太想看这些长篇大论可以直接跳到结论部分。**

在智普最近的5、5.1、5.2等报告中可以看到，智普一直在尝试落地DSA，这是在 1M 上下文中节省成本的最重要环节重要。

所以我们就从DSA开始讲起。

**DSA 核心原理**

DSA（DeepSeek Sparse Attention）的核心机制是一个轻量级的 **索引器（Indexer）** ，它对每个新生成的query token，扫描整个前缀中的所有token， **给每个token打相关性分数，然后只选取得分最高的token执行精细的注意力计算** 。

**MTP**

MTP（Multi-Token Prediction），核心机制是在主干网络之上附加一组轻量的 Transformer Block 和输出头，用来 **并行预测** 未来多个 token（智谱报告中是3个）。这些预测出的 token 作为草稿，送给主干网络（目标模型）逐个验证。验证通过的 token 被接受，未通过的从第一个拒绝位置截断，然后以验证后的结果作为下一轮输入，重复上述过程直到生成结束。

这里需要特殊说明下。

**MTP 整个"预测多个草稿token → 拿去给目标模型验证"的过程，不是一个物理架构，更贴切的描述应该是一个工作流。**

**Indexer Share（或者说 Indexer Cache）**

我们看到 Share，一定会想这里的 Share 指代的是什么？为什么一定要有这个组件？它做作用于主干网络的哪里？

要想理解这个概念，我们得先了解在有这个组件之前的 Indexer 怎么部署的。

标准的 DSA层 中 Indexer 是存在于 DSA 中的所有 Transformer 模块。之所以这样设计，是因为不同 Transformer 层处于不同的处理阶段：浅层主要捕捉局部语法和短距离依赖，中层构建语义表示，深层进行高层次推理和决策。这种 **功能分化** 导致各层的注意力焦点自然不同。

而 Index Share 做的就是把每4层Transformer的Indexer **合并成一个** ——保留第1层的Indexer，让它计算top-k索引，后面3层直接复用这个结果，不再运行自己的Indexer。

智谱能这样做的原因是，DSA论文中通过实验验证了相邻层的 **top-k索引重叠率高达70%-100%** ——即相邻层选出的"最相关token集合"基本相同。

[https://arxiv.org/pdf/2603.12201](https://arxiv.org/pdf/2603.12201)

We empirically verify this for DSA by computing the

pairwise top-k index overlap across all layers (Appendix A): adjacent layers share 70-100%

of their selected tokens, and the heatmap reveals distinct layer clusters with mutually high

overlap, suggesting that most indexer computations are redundant. This leaves a simple

but impactful opportunity: can we remove the majority of indexers in DSA and let most layers

reuse top-k indices from a small number of retained indexer layers, without degrading quality?

说明：GLM 5 报告里的 Indexer Cache 其实就是5.2里的 Indexer Share。

**Indexer Share 在 MTP 层的作用**

除了上面说的，在主干网络中降低重复的索引查询。在 5.2 中，MTP 层也引入了它（两边都是独立的，不共享数据）。

衡量 MTP 好不好，主要是看接受率，接受率越高表示MTP的预测约准 **。**

假设，假设输入是"今天天气"，MTP Step 1预测下一个token t5（比如"很好"），Step 2预测t6（比如"啊"）的时候会参考前面的内容来生成，这就导致了当前的草稿是基于输入+前一个草稿的内容来生成，越到后面 MTP 的接受率就会越低。

MTP Step 2 在生成草稿时，需要基于 Step 1 的输出 h5' 作为输入——这是物理上无法避免的，Step 2 天然依赖 Step 1 的结果。问题在于：Step 2 做 **自注意力计算** 时，会看到 h1, h2, h3, h4（来自目标模型，高质量）和 h5'（来自 MTP 层，低质量）。h5' 的低质量 KV 会"污染"注意力计算结果，导致第二步草稿的接受率下降。

Indexer Share 在这里起到的是 **限制注意力范围** 的作用：复用 Step 1 的 mask，而这个 mask 里 **不包含 h5'** （Step 1 时 h5' 还不存在）。所以 Step 2 做注意力时只能看到 h1-h4，h5' 自己的 KV 被 mask=0挡住。注意力计算只受高质量 KV 影响，第二步草稿的接受率因此提升（从 4.56 提升到 5.10）。

代价是 Step 2 看不到 h5' 自己的信息（少了一个信息源），但实验表明这个代价值得。

注意力计算质量更接近训练时的水平，接受率从4.56提升到5.10

**KV Share**

KV Share 作用在 MTP 层，解决的是 **KV Cache 重复计算** 问题。

MTP 层做自注意力时，需要前面所有 token 的 Key（K）和 Value（V）向量。这些 KV 值在主干网络 forward 时 **已经计算过了** 。如果没有 KV Share，MTP 层需要重新计算一遍这些 KV，造成大量的冗余计算和内存开销。

KV Share 的做法是：让 MTP 层 **直接复用** 主干网络已经算好的 KV Cache。只有在处理 MTP 新预测出的 token 时，才需要计算新的 KV 值。

这与 IndexShare 形成互补：IndexShare 决定"看哪些 token"（通过复用 top-k 索引），KVShare 决定"如何高效获取这些 token 的 KV 值"（通过共享 KV Cache）。

**Rejection Sampling**

这是个算法层面的优化。在介绍之前，需要先了解它的前任， **Target-Only。**

**Target-Only：只看大模型脸色**

假设我们现在要让模型生成一个词，模型面前有3个候选词： **"苹果"** 、 **"香蕉"** 、 **"西瓜"** 。目标模型对这3个词的"偏好程度"如下：

| 候选词 | 目标模型给出的概率 |

| --- | --------- |

| 苹果 | 50% |

| 香蕉 | 30% |

| 西瓜 | 20% |

这个概率分布就是 **目标分布** ——它代表了大模型"真正想说什么"。

现在，草稿模型（比如MTP头）先快速猜了一个词，猜的是 **"香蕉"** 。

Target-Only的验证逻辑很简单： **大模型觉得"香蕉"是不是它最想要的那个？**

大模型最想要的是"苹果"（50%），而草稿给的是"香蕉"（30%），不是最好的那个。

**结果：拒绝。**

哪怕"香蕉"在大模型看来其实也不错（有30%的概率），但因为不是第一名，就被打回去了。

这就是Target-Only的问题—— **它的接受标准太苛刻了** ：只有草稿词恰好是大模型的"首选"时才接受。如果大模型分布比较"平坦"（ **比如三个词分别是35%、33%、32%，没有明显赢家），那Target-Only的接受率就会很低，因为很难恰好命中第一名。**

**Rejection Sampling：看两个模型的"默契程度"**

Rejection Sampling的思路完全不同。它不只是看大模型的分布，还 **同时看草稿模型的分布** ，然后问： **这两个模型"想的是不是一回事"？**

假设草稿模型自己的预测分布是这样的：

| 候选词 | 草稿模型的概率 |

| --- | ------- |

| 苹果 | 45% |

| 香蕉 | 35% |

| 西瓜 | 20% |

Rejection Sampling的逻辑是： **如果草稿模型和目标模型都"挺看好"某个词，那这个词就应该被接受。**

具体来说，它对每个词都取两个概率中的较小值：

"苹果"：min(50%, 45%) = 45%

"香蕉"：min(30%, 35%) = 30%

"西瓜"：min(20%, 20%) = 20%

然后把这三个值加起来：45% + 30% + 20% = **95%** 。这就是 **接受率** ——有95%的概率，Rejection Sampling会接受草稿模型生成的这个词。

**为什么Rejection Sampling更好？**

回到刚才的例子，草稿猜的是"香蕉"。

**Target-Only** ：大模型首选是"苹果"，"香蕉"不是首选 → **拒绝**

**Rejection Sampling** ：大模型给"香蕉"30%，草稿也给"香蕉"35%，两者意见一致 → **以很高的概率接受**

关键区别在于：

**1\. Target-Only** 只问一个问题： **"这个词是不是大模型的最爱？"** ——如果大模型分布很分散（没有明显最爱），接受率就很惨。

**2\. Rejection Sampling** 问的是： **"草稿模型和大模型是不是在唱同一首歌？"** ——即使都不是很确定，但只要两个模型的"口味"一致，接受率依然可以很高。

这也是为什么GLM-5.2要用Rejection Sampling替代Target-Only：在RL训练过程中，模型的输出分布会不断变化，有时候很"确定"（某个词概率90%），有时候很"犹豫"（几个词概率差不多）。Target-Only在模型"犹豫"的时候接受率会暴跌，而Rejection Sampling保持稳定，因为它看的是 **两个模型的默契，而不是某个词的绝对排名** 。

**End-to-End TV Loss**

Rejection Sampling 说的是主干模型怎么验证草稿模型的生成内容。这里讲的就是在训练草稿模型时， **训练目标** 也调整了：从传统的"猜对下一个词"（交叉熵损失），改为 **直接优化"分布重叠面积"** ——也就是 Rejection Sampling 计算接受率时用的那个量（Σ min(p, q)）。这样训练出来的草稿模型，其输出分布形状与目标模型更接近，Rejection Sampling 的接受率自然更高。

**结论**

这四个概念可以分成两类。

**一类是架构层面的优化：KV Share 与 Index Share。**

Index Share 的核心作用是 **降低稀疏注意力中索引计算的开销** ：在主干网络中，通过合并相邻层的Indexer节省75%的计算量；在MTP层中，通过复用前一步的mask **限制注意力范围** ，阻止MTP自产的低质量KV参与后续草稿的注意力计算，从而提升第二步草稿的接受率。KV Share 则解决 **KV Cache的重复计算问题** ，让MTP层直接复用主干网络已经算好的KV，只在处理新预测出的token时才计算新的KV。

**另一类是算法层面的优化：Rejection Sampling 和 End-to-End TV Loss。**

Rejection Sampling 改变了验证机制：不再要求草稿token是目标模型的"首选"（Target-Only），而是比较草稿分布与目标分布的 **重叠程度** ——只要两个模型"口味一致"，接受率就高。这使得验证过程对模型熵波动具有鲁棒性，在RL训练中保持稳定。End-to-End TV Loss 则从训练端发力：将草稿模型的优化目标从"猜对下一个词"改为 **直接最大化分布重叠面积** ，让训练目标与Rejection Sampling的验证逻辑对齐，从根本上提升接受率。

两项架构优化（IndexShare + KVShare）解决的是" **推理时计算质量和效率** "的问题，两项算法优化（Rejection Sampling + TV Loss）解决的是" **验证和训练目标不匹配** "的问题。四者叠加，将GLM-5.2的MTP接受长度从4.56提升到5.47，增幅达20%。

\--附录

[https://arxiv.org/pdf/2603.12201](https://arxiv.org/pdf/2603.12201)

GLM-5技术报告:[https://arxiv.org/html/2602.15763v1](https://arxiv.org/html/2602.15763v1)

GLM-5.2技术报告： [https://z.ai/blog/glm-5.2](https://z.ai/blog/glm-5.2)

