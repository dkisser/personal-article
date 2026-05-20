# Pi vs DeepAgents: 脚手架级 Agent 框架深度对比研究报告

> 研究日期: 2026/05/15
> 研究对象: [pi](https://github.com/earendil-works/pi-mono) (TypeScript) vs [deepagents](https://github.com/langchain-ai/deepagents) (Python)
> 关联可视化: [架构对比](./visualizations/architecture-comparison.html) | [抽象层级雷达图](./visualizations/abstraction-radar.html) | [扩展机制对比](./visualizations/extension-comparison.html) | [设计理念对比](./visualizations/philosophy-comparison.html)

---

## 一、执行摘要

Pi 和 DeepAgents 是当前开源社区两个最具代表性的脚手架级 Agent 框架。两者都旨在降低构建 AI Agent 的门槛，但采用了截然不同的设计哲学和抽象策略。

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **核心哲学** | 自研核心，精细控制 | 站在巨人肩膀上，开箱即用 |
| **运行时** | 自研 AgentLoop (无状态纯函数) | LangGraph CompiledStateGraph |
| **语言** | TypeScript | Python |
| **架构风格** | 分层事件驱动 | Middleware 堆栈 + 图编排 |
| **扩展方式** | 事件订阅 + 注册式 API | Middleware 插入 + Profile 覆盖 |
| **上手门槛** | 需要理解事件系统和类型 | `pip install` 即可运行 |
| **定制深度** | 极高 (可拦截任意生命周期) | 高 (Middleware 可插入任意位置) |

**一句话总结差异**: Pi 选择自底向上构建一切以换取最大控制权；DeepAgents 选择嫁接成熟的 LangGraph/LangChain 生态以换取最快上手速度和最大生态兼容性。

---

## 二、项目概览

### 2.1 Pi

Pi 是由 earendil-works 维护的 TypeScript monorepo，定位为 "Agent Harness"。

**包结构:**

```
packages/
  ai/          — 统一多 Provider LLM API (OpenAI, Anthropic, Google, Mistral, Bedrock 等)
  agent/       — Agent runtime: AgentLoop (无状态循环) + Agent (有状态包装器)
  coding-agent/ — 交互式 CLI Agent，含扩展系统、会话管理、TUI
  tui/         — 终端 UI 库 (差分渲染、编辑器组件、overlay 系统)
  web-ui/      — Web 组件 (AI 聊天界面)
```

**关键特点:**
- 自研 Agent runtime，不依赖外部 Agent 框架
- 事件驱动的扩展系统 (ExtensionAPI)
- 精细的 token 计算和上下文压缩 (compaction)
- 多 provider 的 lazy registration 机制
- 分支式会话树 (session tree) 支持 fork/navigate

### 2.2 DeepAgents

DeepAgents 是由 LangChain 团队维护的 Python monorepo，定位为 "batteries-included agent harness"。

**包结构:**

```
libs/
  deepagents/  — SDK: create_deep_agent, middleware 系统, profiles
  cli/         — 交互式 CLI (基于 Textual TUI)
  acp/         — Agent Context Protocol 支持
  evals/       — 评估框架 + Harbor 集成
  partners/    — 第三方集成 (Daytona 等)
```

**关键特点:**
- 原生基于 LangGraph (CompiledStateGraph)
- Middleware 堆栈架构 (可插入、可排除)
- 开箱即用的工具集 (filesystem, shell, todos, subagents)
- HarnessProfile 系统 (按模型调优行为)
- BackendProtocol (可插拔存储后端)

---

## 三、设计理念对比

### 3.1 Pi: "掌控每一字节"

**一句话设计哲学**: *从流式事件到 token 计数，每一层都暴露给你，因为 Agent 的行为值得被精确控制。*

**设计哲学阐述:**

1. **自研优于依赖**: Pi 选择自己实现 Agent runtime 而非使用 LangGraph/LangChain 等现有框架。这带来了完全可控的调用链和零抽象泄漏。

2. **事件即契约**: 整个系统基于事件流构建。AgentLoop 是纯函数，通过 `emit(event)` 与外部通信。事件类型精细到 `text_delta`、`toolcall_delta`、`tool_execution_update` 等级别。

3. **状态显式化**: AgentState 是核心数据结构，包含 systemPrompt、model、tools、messages、pendingToolCalls 等所有状态。没有隐藏状态。

4. **延迟加载即策略**: Provider 采用 lazy registration 模式，只有在实际调用时才加载对应模块，最大限度减少启动开销和内存占用。

5. **工具执行精细化**: 工具调用支持 sequential/parallel 模式，每个工具经历 prepare → execute → finalize 三阶段，beforeToolCall 和 afterToolCall 钩子可拦截任意阶段。

### 3.2 DeepAgents: "默认即正确"

**一句话设计哲学**: *你不需要成为一个 Agent 专家才能使用 Agent — 我们把最合理的默认都打包好了。*

**设计哲学阐述:**

1. **生态嫁接**: DeepAgents 不重新发明轮子，而是嫁接 LangGraph/LangChain 成熟生态。`create_deep_agent()` 返回的是 CompiledStateGraph，天然支持 streaming、checkpointer、persistence。

2. **Middleware 即策略**: 所有行为通过 Middleware 堆栈表达。Base stack (TodoList + Filesystem + SubAgent + Summarization) + User middleware + Tail stack (Prompt Caching + Memory + HITL)。这种设计让行为的组合变得声明式。

3. **Profile 驱动调优**: HarnessProfile 按模型提供商/具体模型来调优 Agent 行为 (prompt assembly、tool descriptions、middleware 配置)。内置了 Anthropic、OpenAI、Google 等 profile。

4. **信任 LLM**: 安全边界在工具/沙箱层面强制执行，而非期望模型自律。`FilesystemPermission` 是显式的访问控制规则。

5. **SubAgent 即一等公民**: 子代理不是事后补充的功能，而是核心架构的一部分。支持同步 SubAgent、预编译 CompiledSubAgent 和异步 AsyncSubAgent 三种形态。

### 3.3 理念差异的根源

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **目标用户** | 需要精细控制的 Agent 开发者 | 需要快速落地的应用开发者 |
| **信任假设** | 开发者知道自己要什么 | 框架知道什么是最好的默认 |
| **学习曲线** | 陡峭 (需要理解事件系统、类型体系) | 平缓 (pip install 即可用) |
| **生态依赖** | 最小化 (仅依赖 LLM API 客户端) | 最大化 (LangChain 完整生态) |
| **定制自由度** | 极高 (可重写任意生命周期) | 高 (Middleware 可插入/排除) |

---

## 四、架构对比

### 4.1 Pi 的 5 层架构

Pi 的架构是严格分层的，上层依赖下层，下层不感知上层。

```
L1: User Interface
    └── prompt() / steer() / followUp() / continue()

L2: Agent (有状态包装器)
    └── AgentState { systemPrompt, model, tools, messages, ... }
    └── 队列管理: steeringQueue, followUpQueue, pendingMessageQueue
    └── 事件分发: processEvents → 更新状态 + 通知监听器

L3: AgentLoop (无状态循环)
    └── 纯函数: runAgentLoop(prompts, context, config, emit, signal)
    └── 核心流程: check steering → inject messages → stream assistant → execute tools → check stop

L4: LLM Stream
    └── transformContext → convertToLlm → build context → getApiKey → streamSimple
    └── 流式事件: start → text_delta/thinking_delta/toolcall_delta → done/error

L5: Tool Execution
    └── parse tool calls → prepare arguments → beforeToolCall hook → execute → afterToolCall hook → emit result
```

**核心调用链:**
```
User.prompt() → Agent.runPromptMessages() → Agent.createContextSnapshot() → Agent.createLoopConfig()
  → runAgentLoop() → streamAssistantResponse() → executeToolCalls() → emit(event)
  → Agent.processEvents() → 更新状态 + 通知监听器
```

### 4.2 DeepAgents 的图架构

DeepAgents 的架构核心是 LangGraph 的 CompiledStateGraph，行为通过 Middleware 堆栈注入。

```
create_deep_agent() → create_agent() [from langchain.agents]
  → CompiledStateGraph [from langgraph]
    → State: _DeepAgentState { messages (DeltaChannel), ... }
    → Node: agent (LLM call + tool routing)
    → Middleware Stack (按顺序执行):
        Base Stack:
        - TodoListMiddleware        (write_todos)
        - SkillsMiddleware          (skills 加载)
        - FilesystemMiddleware      (ls, read_file, write_file, edit_file, glob, grep)
        - SubAgentMiddleware        (task 工具)
        - AsyncSubAgentMiddleware   (异步子代理)
        - SummarizationMiddleware   (上下文自动摘要)
        - PatchToolCallsMiddleware  (工具调用修复)
        User Middleware (插入位置)
        - 用户自定义 middleware
        Tail Stack:
        - HarnessProfile.extra_middleware
        - _ToolExclusionMiddleware  (工具排除)
        - AnthropicPromptCachingMiddleware
        - MemoryMiddleware          (AGENTS.md 记忆)
        - HumanInTheLoopMiddleware  (interrupt_on)
```

**核心数据流:**
```
User input → _DeepAgentState → Middleware 堆栈处理 → LLM call → Tool calls → Middleware 拦截/处理 → Tool execution → 更新 State → 循环
```

### 4.3 架构差异分析

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **核心抽象** | 分层函数调用 (Agent → AgentLoop) | 编译状态图 (CompiledStateGraph) |
| **状态管理** | 显式 AgentState (mutable getter/setter) | LangGraph State + DeltaChannel (O(N²)→O(N)) |
| **事件系统** | 精细事件流 (10+ 事件类型) | Middleware 拦截 (ModelRequest/ModelResponse) |
| **并发模型** | Promise + AbortSignal | LangGraph Runtime + asyncio |
| **流式处理** | 原生 EventStream (push-based) | LangGraph streaming (pull-based) |
| **错误处理** | 流内 error 事件 (stopReason: "error") | Middleware 拦截 + 异常传播 |
| **上下文压缩** | 显式 compaction (branch summarization) | SummarizationMiddleware (自动触发) |

---

## 五、抽象层级对比

### 5.1 Agent Runtime

**Pi — 自研 AgentLoop:**

```typescript
// 最简使用
const agent = new Agent({
  initialState: { systemPrompt: "You are a coding assistant.", model }
});
await agent.prompt("Write a function");
```

Pi 的 AgentLoop 是一个无状态纯函数，接收 context + config，返回 EventStream。Agent 是有状态包装器，负责队列管理和事件分发。

**DeepAgents — LangGraph Native:**

```python
# 最简使用
agent = create_deep_agent()
agent.invoke({"messages": [{"role": "user", "content": "Write a function"}]})
```

DeepAgents 的 Agent 是一个 CompiledStateGraph，由 LangGraph 运行时驱动。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **抽象层级** | 中 (自研 runtime，暴露事件) | 高 (嫁接 LangGraph，隐藏细节) |
| **控制力** | 高 (可拦截每个事件) | 中 (通过 Middleware 拦截) |
| **调试难度** | 中 (事件流可追踪) | 低 (LangGraph Studio 可视化) |
| **性能开销** | 低 (无框架 overhead) | 中 (LangGraph runtime 开销) |

### 5.2 工具系统

**Pi — 注册式工具:**

```typescript
interface AgentTool<TParameters, TDetails> extends Tool<TParameters> {
  label: string;
  prepareArguments?: (args: unknown) => Static<TParameters>;
  execute: (toolCallId, params, signal?, onUpdate?) => Promise<AgentToolResult<TDetails>>;
  executionMode?: "sequential" | "parallel";
}
```

工具是带 schema 的函数，支持 prepareArguments 参数转换、executionMode 执行模式覆盖、onUpdate 流式更新。

**DeepAgents — LangChain Tools:**

```python
# 内置工具
- write_todos: 管理待办列表
- ls, read_file, write_file, edit_file, glob, grep: 文件操作
- execute: 执行 shell 命令
- task: 调用子代理

# 自定义工具
agent = create_deep_agent(tools=[my_custom_tool])
```

工具基于 LangChain 的 BaseTool/StructuredTool，通过 Middleware 注入。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **工具定义** | 接口 + TypeBox schema | BaseTool/StructuredTool (Pydantic) |
| **自定义工具** | registerTool() | tools=[...] 参数 |
| **工具执行模式** | sequential / parallel (per-tool 覆盖) | 由 LangGraph 调度 |
| **流式更新** | onUpdate callback | 通过 Middleware 拦截 |
| **MCP 支持** | 未明确 | langchain-mcp-adapters |

### 5.3 LLM 抽象

**Pi — pi-ai 统一层:**

```typescript
// 统一的 stream/streamSimple API
streamSimple(model, context, options) → AssistantMessageEventStream

// Provider 通过 lazy registration 注册
registerApiProvider({ api: "anthropic-messages", stream, streamSimple })
```

Pi 的 AI 层提供统一的流式 API，将不同 provider 的差异封装在 provider 模块内部。对外暴露标准化的事件流 (text, tool_call, thinking, usage, stop)。

**DeepAgents — init_chat_model:**

```python
# 支持 provider:model 字符串
agent = create_deep_agent(model="openai:gpt-4o")

# 或预初始化模型
from langchain.chat_models import init_chat_model
model = init_chat_model("anthropic:claude-sonnet-4-6")
agent = create_deep_agent(model=model)
```

DeepAgents 依赖 LangChain 的模型抽象，支持任意 BaseChatModel。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **模型切换** | Model 对象切换 | init_chat_model + 字符串/provider 对象 |
| **Provider 扩展** | 需修改 6+ 文件 (AGENTS.md 有详细指南) | 安装对应 langchain-provider 包 |
| **流式标准化** | 内部标准化 (AssistantMessageEvent) | LangChain 标准化 (AIMessageChunk) |
| **Lazy 加载** | 是 (动态 import provider 模块) | 否 (依赖 Python import 系统) |
| **多模态** | 支持 (ImageContent in tool results) | 支持 (LangChain content blocks) |

### 5.4 状态管理

**Pi:**

```typescript
interface AgentState {
  systemPrompt: string;
  model: Model;
  thinkingLevel: ThinkingLevel;
  tools: AgentTool[];
  messages: AgentMessage[];
  isStreaming: boolean;
  streamingMessage?: AgentMessage;
  pendingToolCalls: ReadonlySet<string>;
  errorMessage?: string;
}
```

状态是显式的、可变的 (通过 getter/setter)，Agent 持有完整状态。

**DeepAgents:**

```python
class _DeepAgentState(AgentState):
    messages: Annotated[list[AnyMessage], DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]
```

状态使用 LangGraph 的 DeltaChannel 优化 checkpoint 增长 (从 O(N²) 降到 O(N))。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **状态可见性** | 完全可见 (AgentState 接口) | 通过 StateSchema 定义 |
| **状态持久化** | 会话树持久化 (JSONL) | Checkpointer (LangGraph 原生) |
| **状态变更追踪** | 手动 (事件驱动) | DeltaChannel (自动) |
| **历史导航** | 分支树 (fork/navigate) | LangGraph checkpoint |

### 5.5 CLI / TUI

**Pi — 自研 TUI:**

```
packages/tui/ — 差分渲染终端 UI 库
packages/coding-agent/src/modes/interactive/ — 交互模式
```

Pi 自研了完整的 TUI 库，包括编辑器组件、overlay 系统、差分渲染、主题系统。

**DeepAgents — Textual:**

```
libs/cli/ — 基于 Textual 框架的 CLI
```

DeepAgents CLI 使用成熟的 Textual Python TUI 框架。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **TUI 框架** | 自研 | Textual (第三方) |
| **渲染方式** | 差分渲染 (减少闪烁) | Textual 原生渲染 |
| **组件生态** | 有限 (自研组件) | 丰富 (Textual Widget Gallery) |
| **slash commands** | 内置 + 扩展注册 | 内置 + 扩展注册 |
| **启动性能** | 快 (Bun 编译二进制) | 需优化 (Python import 开销大) |

### 5.6 上下文管理

**Pi:**

- 显式 token 计算 (`estimateTokens`, `calculateContextTokens`)
- 分支式压缩 (`compact`, `branch-summarization`)
- 会话树 (`SessionManager` 支持 fork/navigate)

**DeepAgents:**

- SummarizationMiddleware (自动触发)
- 大输出自动保存到文件
- MemoryMiddleware (AGENTS.md 加载)

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **压缩触发** | 显式 (自动阈值 + 手动 /trigger-compact) | 自动 (SummarizationMiddleware) |
| **压缩可定制** | 高 (before_compact 事件可完全替换逻辑) | 中 (通过 profile 配置) |
| **会话历史** | 分支树 (多分支导航) | 线性 checkpoint |
| **记忆注入** | systemPrompt 拼接 | MemoryMiddleware |

### 5.7 Sub-agents

**Pi:**

Pi 的 coding-agent 支持子代理通过 `task` 工具或扩展系统中的 `registerCommand` 实现。但没有内置的子代理运行时 — 子代理是通过工具调用实现的。

**DeepAgents:**

```python
# 三种子代理形态
SubAgent         # 声明式同步子代理 (name, description, system_prompt)
CompiledSubAgent # 预编译子代理 (runnable)
AsyncSubAgent    # 异步/远程子代理 (graph_id, url, headers)
```

子代理是核心架构的一部分，通过 SubAgentMiddleware 注入 `task` 工具。

**对比:**

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **子代理支持** | 间接 (通过工具/扩展) | 原生 (三种形态) |
| **隔离性** | 扩展级隔离 | 子图级隔离 |
| **权限继承** | 无明确机制 | 显式继承/覆盖 |

---

## 六、扩展设计对比

### 6.1 扩展哲学

**Pi: "事件驱动 + 注册式 API + 可拦截的生命周期钩子"**

扩展不是继承或修改核心代码，而是通过事件订阅和行为注入来扩展能力。

**DeepAgents: "Middleware 插入 + Profile 覆盖 + 协议实现"**

扩展通过插入 Middleware 到堆栈、注册 Profile 调优行为、实现协议接口来扩展能力。

### 6.2 Pi 的扩展机制

#### 6.2.1 事件系统

Pi 提供 20+ 生命周期事件，分为 7 大类:

| 类别 | 事件示例 | 可拦截 |
|------|---------|--------|
| Session 生命周期 | session_start, session_before_switch, session_before_fork, session_before_compact | 是 (可 cancel) |
| Agent 运行时 | before_agent_start, context, before_provider_request, after_provider_response | 是 (可修改 payload) |
| Turn | turn_start, turn_end | 否 |
| Message | message_start, message_update, message_end | 否 |
| Tool | tool_call, tool_result | 是 (可 block/修改) |
| Input | input | 是 (可 transform) |
| Resource | resources_discover | 否 |

#### 6.2.2 注册式 API

```typescript
// ExtensionAPI 提供以下注册方法:
pi.registerTool(tool: ToolDefinition)           // 注册 LLM 可调用的工具
pi.registerCommand(name, options)               // 注册 /command 命令
pi.registerShortcut(keys, handler)              // 注册键盘快捷键
pi.registerFlag(flag: ExtensionFlag)            // 注册 CLI flag
pi.registerMessageRenderer(renderer)            // 注册自定义消息渲染器
pi.registerProvider(config: ProviderConfig)     // 注册自定义模型 Provider
```

#### 6.2.3 ExtensionContext

扩展通过 ExtensionContext 访问运行时环境:

```typescript
interface ExtensionContext {
  // 状态访问
  cwd: string;
  sessionManager: ReadonlySessionManager;
  modelRegistry: ModelRegistry;
  model?: Model;
  signal: AbortSignal;

  // 控制方法
  isIdle(): boolean;
  abort(): void;
  compact(options?): void;
  shutdown(): void;

  // UI 交互
  ui: ExtensionUIContext;
}
```

#### 6.2.4 扩展加载机制

扩展是 TypeScript 模块，通过 jiti 在运行时加载:

```
1. 扫描扩展目录 (~/.config/pi/extensions/)
2. 用 jiti 编译加载 TypeScript 模块
3. 调用 export default function(pi: ExtensionAPI) {}
4. 绑定事件监听器和注册项
5. 虚拟模块提供核心包访问 (@earendil-works/pi-*)
```

### 6.3 DeepAgents 的扩展机制

#### 6.3.1 Middleware 系统

Middleware 是 DeepAgents 的核心扩展点。每个 Middleware 实现 AgentMiddleware 接口，在 ModelRequest/ModelResponse 时介入:

```python
class MyMiddleware(AgentMiddleware):
    def on_model_request(self, request: ModelRequest) -> ModelRequest:
        # 修改请求
        return request

    def on_model_response(self, response: ModelResponse) -> ModelResponse:
        # 修改响应
        return response
```

Middleware 堆栈顺序决定了介入时机:

```
Base Stack → User Middleware → Tail Stack
```

#### 6.3.2 Profile 系统

HarnessProfile 按模型调优 Agent 行为:

```python
@dataclass
class HarnessProfile:
    base_system_prompt: str | None = None      # 替换默认 prompt
    system_prompt_suffix: str | None = None    # 追加到 prompt
    tool_description_overrides: dict = None    # 覆盖工具描述
    excluded_tools: list = None                # 排除工具
    excluded_middleware: list = None           # 排除 middleware
    extra_middleware: list = None              # 额外 middleware
    general_purpose_subagent: GeneralPurposeSubagentProfile = None
```

注册新 profile:

```python
register_harness_profile("my-model", HarnessProfile(
    base_system_prompt="Custom prompt...",
    excluded_tools=["execute"]
))
```

#### 6.3.3 Backend 扩展

实现 BackendProtocol 可替换存储后端:

```python
class MyBackend(BackendProtocol):
    async def read_file(self, path: str) -> ReadResult: ...
    async def write_file(self, path: str, content: str) -> WriteResult: ...
    # ... 更多文件操作

agent = create_deep_agent(backend=MyBackend())
```

内置后端: StateBackend (内存), FilesystemBackend (文件系统)。

#### 6.3.4 Skills 系统

Skills 从 backend 路径加载 SKILL.md 文件:

```
/skills/user/web-research/
  ├── SKILL.md          # YAML frontmatter + markdown instructions
  └── helper.py         # 可选辅助文件
```

```python
agent = create_deep_agent(skills=["/skills/user/", "/skills/project/"])
```

SkillsMiddleware 将 skill 指令注入 system prompt。

#### 6.3.5 工具扩展

```python
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Tool description."""
    return f"Result: {query}"

agent = create_deep_agent(tools=[my_tool])
```

支持 LangChain 工具生态，包括 langchain-mcp-adapters 接入 MCP 工具。

### 6.4 扩展机制对比总结

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **核心扩展模式** | 事件订阅 + 注册式 API | Middleware 插入 |
| **扩展粒度** | 细粒度 (事件级别) | 中粒度 (请求/响应级别) |
| **扩展语言** | TypeScript | Python |
| **动态加载** | 是 (jiti 运行时编译) | 否 (Python import) |
| **工具扩展** | registerTool (TypeBox schema) | tools=[BaseTool] (Pydantic) |
| **命令扩展** | registerCommand | slash commands (CLI 层) |
| **UI 扩展** | 丰富 (widget, overlay, theme) | 有限 (Textual 框架内) |
| **模型扩展** | registerProvider (6+ 文件修改) | 安装 langchain-provider |
| **拦截能力** | 强 (任意事件可 cancel) | 中 (Middleware on_request/on_response) |
| **状态持久化扩展** | appendEntry (自定义 entry 类型) | BackendProtocol (替换存储) |
| **Skills** | 是 (通过扩展系统) | 是 (SkillsMiddleware) |

---

## 七、关键设计决策对比

### 7.1 自建 vs 嫁接

| 层面 | Pi (自建) | DeepAgents (嫁接) |
|------|-----------|-------------------|
| Agent Runtime | 自研 AgentLoop | LangGraph create_agent |
| LLM API | 自研 pi-ai 统一层 | LangChain BaseChatModel |
| TUI | 自研差分渲染 | Textual |
| 工具系统 | 自研 AgentTool | LangChain BaseTool |
| 流式处理 | 自研 EventStream | LangGraph streaming |

**Pi 的优势**: 零抽象泄漏，完全可控，可针对特定场景极致优化。
**Pi 的代价**: 需要维护所有层，社区贡献门槛高。

**DeepAgents 的优势**: 继承 LangChain 生态全部工具、模型、集成；社区贡献路径清晰。
**DeepAgents 的代价**: 受限于 LangGraph 的设计约束；某些场景下 overhead 不可控。

### 7.2 类型系统

| 维度 | Pi (TypeScript) | DeepAgents (Python) |
|------|-----------------|---------------------|
| **类型安全** | 编译时强类型 | 运行时类型检查 (Pydantic) |
| **Schema 定义** | TypeBox (JSON Schema) | Pydantic (BaseModel) |
| **工具参数** | Static<TSchema> | Pydantic 验证 |
| **IDE 支持** | 极佳 | 好 |

### 7.3 部署形态

| 维度 | Pi | DeepAgents |
|------|-----|-----------|
| **编译产物** | Bun 单二进制文件 | Python wheel |
| **启动速度** | 快 (Bun 编译) | 慢 (Python import) |
| **CLI 安装** | 编译安装 | pip/uv install |
| **沙箱支持** | 内置 (node:child_process) | 通过 BackendProtocol (Daytona 等) |

---

## 八、总结与建议

### 8.1 选型建议

**选择 Pi，如果你:**
- 需要极致的性能和控制力
- 团队主要使用 TypeScript
- 需要自定义 Agent runtime 的每个细节
- 愿意投入时间理解事件系统和类型体系
- 需要 Bun 编译的单二进制部署

**选择 DeepAgents，如果你:**
- 需要最快上手 (pip install + 一行代码运行)
- 团队主要使用 Python
- 需要 LangChain 生态的全部工具和集成
- 需要 LangGraph Studio 可视化调试
- 需要成熟的 checkpointer/persistence 支持

### 8.2 互相借鉴的方向

**Pi 可向 DeepAgents 学习:**
1. **Middleware 架构**: Pi 的扩展系统虽然强大，但缺少 Middleware 的声明式组合能力。引入 Middleware 堆栈概念可简化扩展开发。
2. **BackendProtocol**: Pi 的文件系统操作与执行环境耦合较紧，抽象出 BackendProtocol 可提高可测试性和可移植性。
3. **Profile 系统**: 按模型调优行为是高频需求，Pi 可通过扩展系统实现类似 HarnessProfile 的机制。

**DeepAgents 可向 Pi 学习:**
1. **事件粒度**: DeepAgents 的 Middleware 拦截在 request/response 级别，缺少 Pi 级别的细粒度事件 (text_delta, tool_execution_update)。增加细粒度事件可提升可观测性。
2. **Lazy Provider 加载**: Python import 系统天然支持 lazy loading，但 DeepAgents 的启动开销仍较大。借鉴 Pi 的按需加载策略可改善 CLI 启动速度。
3. **分支式会话**: Pi 的会话树 (fork/navigate) 是强大的交互模式，DeepAgents 的线性 checkpoint 可借鉴此设计。
4. **TUI 自研**: Textual 虽然成熟，但在极致性能和定制化方面不如自研 TUI。对于重度 CLI 用户，自研 TUI 可能带来更好体验。

### 8.3 共同趋势

1. **Skills 系统**: 两者都实现了 skills 加载机制，说明 "渐进式能力注入" 是 Agent 框架的共识。
2. **权限系统**: 两者都在工具层面引入权限控制 (Pi 的 beforeToolCall block, DeepAgents 的 FilesystemPermission)，说明 Agent 安全从 "信任 LLM" 转向 "边界控制"。
3. **上下文压缩**: 两者都实现了上下文压缩/摘要机制，说明长上下文管理是 Agent 框架的标配。
4. **SubAgent 原生支持**: DeepAgents 将子代理作为一等公民，Pi 通过扩展系统间接支持。多 Agent 协作是共同演进方向。

---

## 附录

### A. 参考可视化

- [架构对比图](./visualizations/architecture-comparison.html) — 展示两个项目的整体架构层次
- [抽象层级雷达图](./visualizations/abstraction-radar.html) — 多维度抽象层级对比
- [扩展机制对比图](./visualizations/extension-comparison.html) — 扩展点与扩展方式对比
- [设计理念对比图](./visualizations/philosophy-comparison.html) — 设计哲学与决策对比

### B. 关键代码路径

**Pi:**
- Agent runtime: `packages/agent/src/agent.ts`, `packages/agent/src/agent-loop.ts`
- Extension system: `packages/coding-agent/src/core/extensions/`
- AI layer: `packages/ai/src/stream.ts`, `packages/ai/src/providers/register-builtins.ts`
- TUI: `packages/tui/src/tui.ts`

**DeepAgents:**
- Graph assembly: `libs/deepagents/deepagents/graph.py`
- Middleware: `libs/deepagents/deepagents/middleware/`
- Profiles: `libs/deepagents/deepagents/profiles/`
- Backends: `libs/deepagents/deepagents/backends/`
