# Wiki

所有已发布的文章，按分类整理。

## 开发踩坑日记

- [[「"精细控制"和"开箱即用"的Agent开发路线"]] — 本文介绍了Agent开发的两种路线：Pi追求极致性能与自由扩展，适合学习；DeepAgents追求开箱即用，适合快速开发。作者建议，一般需求可通过Skill解决，仅在需要自主规划并作为云端服务时才自研Agent。
- [[「管理TypeScript生态中的Monorepo项目"]] — 介绍 TypeScript 生态中 Monorepo 的实践，使用 pnpm、turbo、vite、jest 等工具管理依赖和任务。
- [[「TypeScript全栈踩坑日记-项目搭建"]] — 使用 create-fullstack-vite 搭建 TypeScript 全栈项目的踩坑记录，技术栈 React + TypeScript + NestJS。
- [[「TypeScript全栈踩坑日记-文章管理系统的迭代"]] — 使用 TypeScript 全栈快速构建文章管理系统，AI 辅助下从需求到实现约 40 分钟。
- [[「当你要需要MCP Server时，希望你先了解下FastM..."]] — Python 生态集成 Agent 工具对比，推荐 FastMCP 的 Streamable HTTP 方案，并提醒避开已弃用的 SSE。
- [[「尝试 Node 搭建一个后端」]] — 作者尝试使用Node搭建后端，采用Bun作为开发环境、Fastify和TypeScript构建Web服务，并添加PM2部署脚本。
- [[「尝试 Node 搭建后端-开发框架」]] — 使用Node.js (Fastify + @fastify/awilix) 实现后端开发框架，通过依赖注入容器管理服务，利用Fastify Hooks实现AOP。

- [[「Agent越来越智能，但我发现软件工程仍然很重要"]] — Agent改bug时只改了报错处，却遗漏了重复定义的API响应类型，导致连接不断重连。作者借此反思：消除重复、保持强一致的代码契约，仍是引导Agent高效协作的关键。

## 产品体验与思考

- [[浅浅地试了试 EvoMap，说说我的看法]] — 对 EvoMap 解决方案库的初步体验与思考，讨论 Agent 时代下知识沉淀与悬赏机制的价值。
- [[「省Token利器-Claude-mem」]] — 介绍Claude-mem工具，通过mem-search MCP实现本地文件与向量检索，避免AI重复理解上下文从而节省Token，适合持续迭代的项目。
- [[「Agent在控制你的浏览器会话"]] — 解释AI Agent如何通过Chrome扩展和Native Messaging技术控制浏览器会话，并提供安全开关让用户可见可控。
- [[「云端Agent如何使用你本地机器的浏览器？"]] — 探讨云端Agent通过WebSocket连接使用本地浏览器的方案，核心挑战在于连接管理与安全认证。
- [[「CC-Switch还真是个不错的产品」]] — CC-Switch是一个能让Coding Agent无缝切换底层LLM供应商的工具，支持Claude Code、Codex等。
- [[「K2.7 Code 高速版，yyds」]] — 体验Kimi K2.7 Code高速版，申请快速通过，速度约普通版6倍，但5小时额度约2小时用完。包含在Coding Plan内，优于MiniMax强制套餐。
- [[「Claude-mem 核心原理解读」]] — Claude-mem 用 Observation+Summary 保留记忆，采用渐进式披露（title→summary→原内容）自动注入上下文，避免 RAG 召回开销。
- [[「Kimi Work 的半额 Token消耗突然不香了~」]] — Kimi Work 半额 Token 消耗看似划算，但迁移 Skills 和无法使用 Claude-mem 的隐形成本让迁移决心动摇。作者意识到工具切换不仅是功能比较，社区生态同样重要。
- [[「Run fast, Run first」]] — 从迷恋动态语言的快速构建，到发现 Java 之慢源于内心执念；Agent 时代应先找到用户愿意买单的方向。

## 产品复刻

- [[「复刻Codex浏览器插件-鉴权篇」]] — 复刻 Codex 浏览器插件，保留跨网络端点的鉴权，并讨论 Agentic Coding 的局限。
- [[「复刻Codex浏览器插件-实现篇」]] — 复刻 Codex 插件的实现过程，分享 Monorepo 统一技术栈、Super Power 头脑风暴与 Service Worker 休眠解决方案。
- [[「复刻Codex浏览器插件-核心设计篇」]] — 复刻 Codex 插件的核心架构，说明 WebSocket Server/Local/Extension 分工，以及去掉 Native Host 的原因。
- [[「复刻Codex浏览器插件-终篇」]] — 复刻 Codex 浏览器插件终篇，强调产品生命周期开始，突出无需注册、可定制鉴权、在 Coding Agent 中操作常用浏览器的价值。

## 经验总结

- [[「一个简化AI代码的小技巧」]] — 分享卫句模式和组合方法两种编程技巧，帮助简化AI生成的深层嵌套代码，让主逻辑清晰易读。

## 吐槽

- [[「MiniMax M3，从入坑到头疼」]] — 作者尝试用MiniMax M3模型为Browser-Bridge添加安装脚本和Chrome扩展发布流程，结果模型拆解出19个任务，执行极其缓慢，todo状态更新延迟，浪费大量时间，最终切换到GLM 5.2。

## 技术报告解读

- [[「GLM 5.2 技术报告解读」]] — 本文解读GLM 5.2技术报告，讲述国外模型被限制后智谱发布GLM-5.2，支持1M上下文并开源。重点分析长上下文难题：KV Cache爆炸及通过MLA-256和FP8量化压缩，以及DSA稀疏注意力提升效率。
- [[「GLM5.2技术报告解读-MTP」]] — 解读 GLM5.2 DSA 优化：Indexer Share、KV Share、Rejection Sampling 与 TV Loss。

## 技术思考

- [[「一个 setTimeout 引出了事件循环问题，这个事件循...]] — 从setTimeout泄露bug入手，揭示事件循环本质：单线程死循环处理任务队列。探讨动态语言为何难以多线程，以及事件循环适合前端却不适合大规模后端的原因。
- [[「Browser-Bridge 新版本中关于 MCP 和 C...]] — 从 CLI+SKILL 转向 MCP，Browser-Bridge 新版集成方式背后的上下文窗口考量。

## Browser-Bridge

- [[Browser-Bridge 推广日记（一）]] — 作者完成Browser-Bridge核心功能后，设目标100用户10好评。反思过去项目失败源于对不确定性的害怕，强调产品生命周期取决于用户使用而非设计者意愿，需“干中学”。
- [[「做了个有趣的小工具 Browser Bridge - 让浏...」]] — Browser-Bridge 通过 WebSocket 将本地 Chrome 暴露为任意 Agent 可调用的工具，无需安装新应用，支持 Claude Code、Langchain 和 Python 脚本直接复用登录态浏览器操作。

---

> 这是一个单向索引：wiki 链接到文章，文章本身不反向引用 wiki。
