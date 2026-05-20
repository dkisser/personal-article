# Pi 项目架构深度分析

> 研究日期：2026-05-15
> 项目路径：`/Users/wenchen/workspace/github/pi`
> 版本：0.74.0

---

## 一、整体架构概览

### 1.1 Monorepo 结构

Pi 是一个 TypeScript monorepo，使用 npm workspaces 管理，包含 5 个核心包：

```
pi-monorepo/
├── packages/
│   ├── ai/           # 统一多 Provider LLM API (@earendil-works/pi-ai)
│   ├── agent/        # Agent Runtime (@earendil-works/pi-agent-core)
│   ├── coding-agent/ # 交互式 Coding Agent CLI (@earendil-works/pi-coding-agent)
│   ├── tui/          # 终端 UI 库 (@earendil-works/pi-tui)
│   └── web-ui/       # Web 组件 (@earendil-works/pi-web-ui)
├── scripts/          # 构建和发布脚本
├── agent-architecture-explorer.html      # 架构可视化
└── agent-extension-mechanism.html        # 扩展机制可视化
```

### 1.2 包依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                    coding-agent (CLI 入口)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   agent      │  │     ai       │  │      tui         │  │
│  │  (runtime)   │◄─┤  (LLM API)   │  │ (终端 UI 组件)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │  web-ui │          │ 外部 SDK │
    │(Web组件)│          │Anthropic│
    └─────────┘          │ OpenAI  │
                         │ Google  │
                         └─────────┘
```

**依赖方向：**
- `coding-agent` 依赖 `agent` + `ai` + `tui`
- `agent` 依赖 `ai`
- `web-ui` 依赖 `ai` + `tui`
- `tui` 无内部依赖（独立终端库）

### 1.3 构建流程

- 构建器：`tsgo`（TypeScript 原生编译器预览版）
- 构建顺序：`tui` → `ai` → `agent` → `coding-agent` → `web-ui`
- AI 包在构建时自动生成模型列表：`generate-models` + `generate-image-models`
- 代码检查：Biome + tsgo --noEmit

---

## 二、AI 层（packages/ai）

### 2.1 核心设计哲学

**统一抽象，Provider 透明**。所有 LLM Provider 被抽象为统一的 `StreamFunction` 接口，上层代码无需关心底层是 OpenAI、Anthropic 还是 Google。

### 2.2 关键类型与接口

**文件：** `packages/ai/src/types.ts`

```typescript
// 统一消息类型
interface UserMessage { role: "user"; content: string | (TextContent | ImageContent)[]; }
interface AssistantMessage { role: "assistant"; content: (TextContent | ThinkingContent | ToolCall)[]; }
interface ToolResultMessage { role: "toolResult"; toolCallId: string; content: ...; }

type Message = UserMessage | AssistantMessage | ToolResultMessage;

// 统一模型定义
interface Model<TApi extends Api> {
  id: string;
  name: string;
  api: TApi;           // 如 "openai-completions", "anthropic-messages"
  provider: Provider;  // 如 "openai", "anthropic"
  baseUrl: string;
  reasoning: boolean;
  thinkingLevelMap?: ThinkingLevelMap;
  input: ("text" | "image")[];
  cost: { input, output, cacheRead, cacheWrite };
  contextWindow: number;
  maxTokens: number;
  compat?: OpenAICompletionsCompat | OpenAIResponsesCompat | AnthropicMessagesCompat;
}

// 流式选项
interface StreamOptions {
  temperature?: number;
  maxTokens?: number;
  signal?: AbortSignal;
  apiKey?: string;
  transport?: Transport;      // "sse" | "websocket" | "auto"
  cacheRetention?: CacheRetention;
  sessionId?: string;
  onPayload?: (payload, model) => unknown;   // 请求前拦截
  onResponse?: (response, model) => void;    // 响应后拦截
  headers?: Record<string, string>;
  timeoutMs?: number;
  maxRetries?: number;
}
```

### 2.3 流式事件协议

**文件：** `packages/ai/src/types.ts` (347-359 行)

```typescript
type AssistantMessageEvent =
  | { type: "start"; partial: AssistantMessage }
  | { type: "text_start"; contentIndex: number; partial: AssistantMessage }
  | { type: "text_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
  | { type: "text_end"; contentIndex: number; content: string; partial: AssistantMessage }
  | { type: "thinking_start"; contentIndex: number; partial: AssistantMessage }
  | { type: "thinking_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
  | { type: "thinking_end"; contentIndex: number; content: string; partial: AssistantMessage }
  | { type: "toolcall_start"; contentIndex: number; partial: AssistantMessage }
  | { type: "toolcall_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
  | { type: "toolcall_end"; contentIndex: number; toolCall: ToolCall; partial: AssistantMessage }
  | { type: "done"; reason: StopReason; message: AssistantMessage }
  | { type: "error"; reason: StopReason; error: AssistantMessage };
```

### 2.4 API Provider 注册表

**文件：** `packages/ai/src/api-registry.ts`

采用**运行时注册表**模式：

```typescript
const apiProviderRegistry = new Map<string, RegisteredApiProvider>();

export function registerApiProvider(provider: ApiProvider, sourceId?: string): void;
export function getApiProvider(api: Api): ApiProviderInternal | undefined;
export function unregisterApiProviders(sourceId: string): void;
```

### 2.5 流式入口

**文件：** `packages/ai/src/stream.ts`

```typescript
export function stream<TApi extends Api>(model, context, options?): AssistantMessageEventStream;
export function complete<TApi extends Api>(model, context, options?): Promise<AssistantMessage>;
export function streamSimple<TApi extends Api>(model, context, options?): AssistantMessageEventStream;
export function completeSimple<TApi extends Api>(model, context, options?): Promise<AssistantMessage>;
```

### 2.6 Provider 实现（懒加载）

**文件：** `packages/ai/src/providers/register-builtins.ts`

支持 9 种 API：
- `openai-completions` — OpenAI Chat Completions + 兼容接口
- `openai-responses` — OpenAI Responses API
- `openai-codex-responses` — OpenAI Codex
- `anthropic-messages` — Anthropic Messages
- `azure-openai-responses` — Azure OpenAI
- `mistral-conversations` — Mistral
- `google-generative-ai` — Google Gemini
- `google-vertex` — Google Vertex AI
- `bedrock-converse-stream` — AWS Bedrock

**懒加载机制：** 每个 Provider 使用动态 `import()` 按需加载，减少启动开销。

### 2.7 模型注册表

**文件：** `packages/ai/src/models.ts`

```typescript
// 从生成的 MODELS 数据初始化
const modelRegistry: Map<string, Map<string, Model<Api>>> = new Map();

export function getModel(provider, modelId): Model;
export function getProviders(): KnownProvider[];
export function getModels(provider): Model[];
export function calculateCost(model, usage): Cost;
export function getSupportedThinkingLevels(model): ModelThinkingLevel[];
export function clampThinkingLevel(model, level): ModelThinkingLevel;
```

### 2.8 事件流实现

**文件：** `packages/ai/src/utils/event-stream.ts`

```typescript
export class EventStream<T, R = T> implements AsyncIterable<T> {
  push(event: T): void;
  end(result?: R): void;
  result(): Promise<R>;
  [Symbol.asyncIterator](): AsyncIterator<T>;
}

export class AssistantMessageEventStream extends EventStream<AssistantMessageEvent, AssistantMessage> {}
```

---

## 三、Agent Runtime（packages/agent）

### 3.1 核心设计

Agent Runtime 是**状态机 + 事件驱动**的架构：
- `Agent` 类管理状态和生命周期
- `agent-loop.ts` 实现核心循环逻辑
- `AgentHarness` 提供更高级的会话抽象

### 3.2 Agent 类

**文件：** `packages/agent/src/agent.ts`

```typescript
export class Agent {
  private _state: MutableAgentState;
  private readonly listeners = new Set<(event: AgentEvent, signal: AbortSignal) => Promise<void> | void>();
  private readonly steeringQueue: PendingMessageQueue;
  private readonly followUpQueue: PendingMessageQueue;
  private activeRun?: ActiveRun;

  // 核心方法
  subscribe(listener): () => void;
  prompt(message): Promise<void>;      // 发送用户消息
  steer(message): void;                // 插入 steering 消息（中断当前）
  followUp(message): void;             // 插入 follow-up 消息（等待完成）
  continue(): Promise<void>;           // 继续执行
  abort(): void;                       // 中止

  // 状态访问
  get state(): AgentState;
}
```

**AgentState 结构：**
```typescript
interface AgentState {
  systemPrompt: string;
  model: Model<any>;
  thinkingLevel: ThinkingLevel;
  set tools(tools: AgentTool<any>[]);
  get tools(): AgentTool<any>[];
  set messages(messages: AgentMessage[]);
  get messages(): AgentMessage[];
  readonly isStreaming: boolean;
  readonly streamingMessage?: AgentMessage;
  readonly pendingToolCalls: ReadonlySet<string>;
  readonly errorMessage?: string;
}
```

### 3.3 Agent Loop

**文件：** `packages/agent/src/agent-loop.ts`

核心循环逻辑（伪代码）：

```
function runLoop(context, newMessages, config, signal, emit, streamFn):
  pendingMessages = getSteeringMessages() || []

  while true:  // 外层：处理 follow-up
    hasMoreToolCalls = true

    while hasMoreToolCalls || pendingMessages.length > 0:  // 内层：处理 tool calls
      // 1. 处理 pending messages
      for message in pendingMessages:
        emit message_start/message_end
        context.messages.push(message)
        newMessages.push(message)
      pendingMessages = []

      // 2. 流式获取 assistant 响应
      message = await streamAssistantResponse(context, config, signal, emit, streamFn)
      newMessages.push(message)

      if message.stopReason == "error" or "aborted":
        emit turn_end, agent_end
        return

      // 3. 提取 tool calls
      toolCalls = extractToolCalls(message)

      if toolCalls.length == 0:
        hasMoreToolCalls = false
        emit turn_end
        break

      // 4. 执行 tool calls（sequential 或 parallel）
      toolResults = await executeToolCalls(toolCalls, config, signal, emit)

      // 5. 检查是否停止
      if shouldStopAfterTurn():
        emit turn_end, agent_end
        return

      // 6. 准备下一轮
      turnUpdate = prepareNextTurn()
      if turnUpdate: apply update

    // 检查 follow-up messages
    pendingMessages = getFollowUpMessages() || []
    if pendingMessages.length == 0:
      emit agent_end
      return
```

### 3.4 Agent 事件协议

**文件：** `packages/agent/src/types.ts` (395-410 行)

```typescript
type AgentEvent =
  // Agent 生命周期
  | { type: "agent_start" }
  | { type: "agent_end"; messages: AgentMessage[] }
  // Turn 生命周期（一次 assistant 响应 + tool calls）
  | { type: "turn_start" }
  | { type: "turn_end"; message: AgentMessage; toolResults: ToolResultMessage[] }
  // Message 生命周期
  | { type: "message_start"; message: AgentMessage }
  | { type: "message_update"; message: AgentMessage; assistantMessageEvent: AssistantMessageEvent }
  | { type: "message_end"; message: AgentMessage }
  // Tool 执行生命周期
  | { type: "tool_execution_start"; toolCallId: string; toolName: string; args: any }
  | { type: "tool_execution_update"; toolCallId: string; toolName: string; args: any; partialResult: any }
  | { type: "tool_execution_end"; toolCallId: string; toolName: string; result: any; isError: boolean };
```

### 3.5 AgentHarness（高级抽象）

**文件：** `packages/agent/src/harness/agent-harness.ts`

`AgentHarness` 在 `Agent` 之上提供：
- 会话管理（Session）集成
- 技能（Skill）和提示模板（PromptTemplate）支持
- 系统提示构建
- 流选项管理
- 钩子系统（hooks）

```typescript
export class AgentHarness<TSkill, TPromptTemplate, TTool> {
  readonly agent: Agent;
  readonly env: ExecutionEnv;
  private session: Session;
  private resources: AgentHarnessResources;
  private hooks = new Map<keyof AgentHarnessEventResultMap, Set<Handler>>();

  // 核心方法
  async prompt(text, images?): Promise<void>;
  async continue(): Promise<void>;
  abort(): void;

  // 事件监听
  on(event, handler): () => void;
  off(event, handler): void;

  // 工具管理
  registerTool(tool): void;
  unregisterTool(name): void;

  // 资源管理
  setResources(resources): void;
}
```

### 3.6 会话存储

**文件：** `packages/agent/src/harness/session/session.ts`

采用**树形结构**存储会话历史：

```typescript
export class Session<TMetadata> {
  private storage: SessionStorage<TMetadata>;

  getBranch(fromId?): Promise<SessionTreeEntry[]>;  // 获取从叶子到根的路径
  buildContext(): Promise<SessionContext>;           // 构建对话上下文
  appendMessage(message): Promise<string>;
  appendThinkingLevelChange(level): Promise<string>;
  appendModelChange(provider, modelId): Promise<string>;
}
```

**Entry 类型：**
- `message` — 对话消息
- `thinking_level_change` — 思考级别变更
- `model_change` — 模型切换
- `compaction` — 上下文压缩记录
- `branch_summary` — 分支摘要
- `custom_message` — 自定义消息

### 3.7 上下文压缩（Compaction）

**文件：** `packages/agent/src/harness/compaction/compaction.ts`

当上下文窗口接近上限时自动或手动压缩：

```typescript
export function compact(context, options): CompactionResult;
export function shouldCompact(context, settings): boolean;
export function prepareCompaction(context): CompactionPreparation;
export function generateSummary(messages): Promise<string>;
export function estimateTokens(messages): number;
export function calculateContextTokens(context): number;
```

### 3.8 代理流（Proxy Stream）

**文件：** `packages/agent/src/proxy.ts`

支持通过代理服务器路由 LLM 请求：

```typescript
export function streamProxy(model, context, options: ProxyStreamOptions): AssistantMessageEventStream;
```

---

## 四、Coding Agent（packages/coding-agent）

### 4.1 架构分层

Coding Agent 是最终用户面对的 CLI 应用，分为三层：

```
┌─────────────────────────────────────────────┐
│  CLI 入口 (main.ts)                          │
│  - 参数解析                                  │
│  - 模式分发 (interactive / print / rpc)      │
├─────────────────────────────────────────────┤
│  AgentSession (agent-session.ts)             │
│  - 会话生命周期管理                           │
│  - 事件订阅与持久化                           │
│  - 模型/思考级别管理                          │
│  - 自动压缩和重试                             │
├─────────────────────────────────────────────┤
│  SDK (sdk.ts)                                │
│  - createAgentSession() 工厂函数              │
│  - 工具创建工厂                               │
│  - 扩展运行时集成                             │
├─────────────────────────────────────────────┤
│  Core 模块                                   │
│  - 工具系统 (tools/)                          │
│  - 扩展系统 (extensions/)                     │
│  - 会话管理 (session-manager.ts)              │
│  - 设置管理 (settings-manager.ts)             │
│  - 模型注册 (model-registry.ts)               │
│  - 认证存储 (auth-storage.ts)                 │
└─────────────────────────────────────────────┘
```

### 4.2 AgentSession

**文件：** `packages/coding-agent/src/core/agent-session.ts`

`AgentSession` 是 Coding Agent 的核心，封装了：

```typescript
export class AgentSession {
  // 核心属性
  private agent: Agent;
  private sessionManager: SessionManager;
  private settingsManager: SettingsManager;
  private modelRegistry: ModelRegistry;
  private extensionRunner?: ExtensionRunner;

  // 用户交互
  async prompt(text, options?: PromptOptions): Promise<void>;
  steer(text): void;
  followUp(text): void;
  continue(): Promise<void>;
  abort(): void;

  // 模型管理
  cycleModel(): Promise<ModelCycleResult>;
  setModel(model): void;
  setThinkingLevel(level): void;

  // 会话管理
  fork(): Promise<void>;
  switchSession(sessionId): Promise<void>;
  compact(reason): Promise<void>;
  exportToHtml(): Promise<string>;

  // 事件订阅
  subscribe(listener: AgentSessionEventListener): () => void;
}
```

### 4.3 工具系统

**文件：** `packages/coding-agent/src/core/tools/index.ts`

内置 7 种工具：

| 工具 | 功能 | 文件 |
|------|------|------|
| `read` | 读取文件内容 | `read.ts` |
| `write` | 写入文件 | `write.ts` |
| `edit` | 编辑文件（搜索替换） | `edit.ts` |
| `bash` | 执行 shell 命令 | `bash.ts` |
| `grep` | 文本搜索 | `grep.ts` |
| `find` | 文件查找 | `find.ts` |
| `ls` | 目录列表 | `ls.ts` |

工具工厂函数：
```typescript
export function createCodingTools(cwd, options?): AgentTool[];
export function createReadOnlyTools(cwd, options?): AgentTool[];
export function createAllTools(cwd, options?): Record<ToolName, AgentTool>;
export function createTool(toolName, cwd, options?): AgentTool;
```

### 4.4 扩展系统

**文件：** `packages/coding-agent/src/core/extensions/`

扩展是 TypeScript 模块，可以：
- 订阅 Agent 生命周期事件
- 注册 LLM 可调用的工具
- 注册命令、快捷键、CLI 标志
- 通过 UI 原语与用户交互

**核心类型：** `packages/coding-agent/src/core/extensions/types.ts`

```typescript
export interface Extension {
  name: string;
  version: string;
  setup(runtime: ExtensionRuntime): void | Promise<void>;
}

export interface ExtensionRuntime {
  // 事件订阅
  on(event: ExtensionEvent, handler: ExtensionHandler): void;

  // 工具注册
  registerTool(tool: RegisteredTool): void;

  // 命令注册
  registerCommand(command: RegisteredCommand): void;

  // 快捷键注册
  registerShortcut(shortcut: ExtensionShortcut): void;

  // UI 交互
  ui: ExtensionUIContext;

  // 上下文访问
  sessionManager: ReadonlySessionManager;
  modelRegistry: ModelRegistry;
  // ...
}
```

**ExtensionRunner：** `packages/coding-agent/src/core/extensions/runner.ts`

管理扩展的生命周期和事件分发：
- 加载扩展（从目录或工厂函数）
- 事件路由
- 错误处理
- 快捷键冲突解决

### 4.5 运行模式

**文件：** `packages/coding-agent/src/modes/`

三种运行模式：

1. **Interactive Mode** (`interactive/interactive-mode.ts`)
   - 全功能 TUI 交互
   - 实时消息渲染
   - 编辑器、选择器、对话框
   - 文件大小：184KB（最复杂）

2. **Print Mode** (`print-mode.ts`)
   - 非交互式，输出到 stdout
   - 适合脚本和管道

3. **RPC Mode** (`rpc/`)
   - JSON-RPC 接口
   - 供 IDE 插件等外部工具调用

### 4.6 会话持久化

**文件：** `packages/coding-agent/src/core/session-manager.ts`

```typescript
export class SessionManager {
  // 存储格式：JSON Lines (.jsonl)
  // 每条记录是一个 SessionEntry

  static create(cwd, sessionDir?): SessionManager;
  static inMemory(): SessionManager;

  async createSession(options?): Promise<SessionInfo>;
  async loadSession(sessionId): Promise<SessionInfo>;
  async list(cwd, sessionDir?): Promise<SessionInfo[]>;
  async listAll(): Promise<SessionInfo[]>;
}
```

---

## 五、TUI 层（packages/tui）

### 5.1 核心设计

**差分渲染（Differential Rendering）** — 只更新变化的终端行，而非全屏重绘。

**文件：** `packages/tui/src/tui.ts`

### 5.2 关键组件

```typescript
// 容器
export class TUI extends Container {
  render(): void;           // 差分渲染
  setFocus(component): void;
  showOverlay(component, options): OverlayHandle;
}

// 组件接口
export interface Component {
  render(width: number): string[];
  handleInput?(data: string): void;
  invalidate(): void;
}

// 可聚焦组件
export interface Focusable {
  focused: boolean;
}

// 光标标记（零宽转义序列）
export const CURSOR_MARKER = "\x1b_pi:c\x07";
```

### 5.3 内置组件

| 组件 | 功能 | 文件 |
|------|------|------|
| `Box` | 边框容器 | `components/box.ts` |
| `Text` | 文本渲染 | `components/text.ts` |
| `Markdown` | Markdown 渲染 | `components/markdown.ts` |
| `Editor` | 文本编辑器 | `components/editor.ts` |
| `Input` | 输入框 | `components/input.ts` |
| `SelectList` | 选择列表 | `components/select-list.ts` |
| `SettingsList` | 设置列表 | `components/settings-list.ts` |
| `Image` | 终端图片（Kitty/iTerm2） | `components/image.ts` |
| `Loader` | 加载动画 | `components/loader.ts` |

### 5.4 键盘输入处理

**文件：** `packages/tui/src/keys.ts`

- 支持 Kitty 键盘协议
- 键位绑定管理（`keybindings.ts`）
- 输入缓冲（`stdin-buffer.ts`）

### 5.5 终端图片

**文件：** `packages/tui/src/terminal-image.ts`

支持两种终端图片协议：
- **Kitty Graphics Protocol** — 现代终端
- **iTerm2 Inline Images** — iTerm2 / WezTerm

---

## 六、Web UI 层（packages/web-ui）

### 6.1 技术栈

- **框架**：Lit（Web Components）
- **样式**：Tailwind CSS
- **构建**：tsc + tailwindcss

### 6.2 核心组件

**文件：** `packages/web-ui/src/index.ts`

```typescript
// 主聊天界面
export { ChatPanel } from "./ChatPanel.js";

// 消息组件
export { AgentInterface } from "./components/AgentInterface.js";
export { MessageList } from "./components/MessageList.js";
export { AssistantMessage, UserMessage, ToolMessage } from "./components/Messages.js";

// 输入组件
export { Input } from "./components/Input.js";
export { MessageEditor } from "./components/MessageEditor.js";

// 对话框
export { ModelSelector } from "./dialogs/ModelSelector.js";
export { SettingsDialog } from "./dialogs/SettingsDialog.js";
export { SessionListDialog } from "./dialogs/SessionListDialog.js";

// 沙箱运行时
export { SandboxIframe } from "./components/SandboxedIframe.js";
export { RuntimeMessageBridge } from "./components/sandbox/RuntimeMessageBridge.js";
```

### 6.3 存储系统

**文件：** `packages/web-ui/src/storage/`

```typescript
export { AppStorage, getAppStorage, setAppStorage } from "./storage/app-storage.js";
export { IndexedDBStorageBackend } from "./storage/backends/indexeddb-storage-backend.js";
export { Store } from "./storage/store.js";

// 数据存储
export { CustomProvidersStore } from "./storage/stores/custom-providers-store.js";
export { ProviderKeysStore } from "./storage/stores/provider-keys-store.js";
export { SessionsStore } from "./storage/stores/sessions-store.js";
export { SettingsStore } from "./storage/stores/settings-store.js";
```

---

## 七、已有可视化文档分析

### 7.1 agent-architecture-explorer.html

该 HTML 文件是一个**交互式架构探索器**，展示了：
- Pi Agent 的完整架构层次
- 各层之间的数据流向
- 关键组件的交互关系
- 使用 D3.js 或类似库实现的可交互图表

### 7.2 agent-extension-mechanism.html

该 HTML 文件是一个**扩展机制可视化文档**，展示了：
- Extension 的生命周期（加载 → 设置 → 运行 → 卸载）
- 事件订阅机制
- 工具注册流程
- UI 上下文交互
- 使用 CSS 动画和交互式图表说明扩展系统的工作原理

---

## 八、关键代码路径汇总

### 8.1 AI 层

| 功能 | 文件路径 |
|------|----------|
| 统一类型定义 | `packages/ai/src/types.ts` |
| API Provider 注册表 | `packages/ai/src/api-registry.ts` |
| 流式入口 | `packages/ai/src/stream.ts` |
| 模型注册表 | `packages/ai/src/models.ts` |
| 事件流实现 | `packages/ai/src/utils/event-stream.ts` |
| Provider 懒加载注册 | `packages/ai/src/providers/register-builtins.ts` |
| Anthropic Provider | `packages/ai/src/providers/anthropic.ts` |
| OpenAI Completions | `packages/ai/src/providers/openai-completions.ts` |
| OpenAI Responses | `packages/ai/src/providers/openai-responses.ts` |
| Google Provider | `packages/ai/src/providers/google.ts` |
| 消息转换 | `packages/ai/src/providers/transform-messages.ts` |

### 8.2 Agent Runtime

| 功能 | 文件路径 |
|------|----------|
| Agent 类 | `packages/agent/src/agent.ts` |
| Agent Loop | `packages/agent/src/agent-loop.ts` |
| Agent 类型定义 | `packages/agent/src/types.ts` |
| AgentHarness | `packages/agent/src/harness/agent-harness.ts` |
| Harness 类型 | `packages/agent/src/harness/types.ts` |
| 会话存储 | `packages/agent/src/harness/session/session.ts` |
| 上下文压缩 | `packages/agent/src/harness/compaction/compaction.ts` |
| 代理流 | `packages/agent/src/proxy.ts` |
| 系统提示 | `packages/agent/src/harness/system-prompt.ts` |
| 技能管理 | `packages/agent/src/harness/skills.ts` |

### 8.3 Coding Agent

| 功能 | 文件路径 |
|------|----------|
| CLI 入口 | `packages/coding-agent/src/main.ts` |
| CLI 参数 | `packages/coding-agent/src/cli/args.ts` |
| AgentSession | `packages/coding-agent/src/core/agent-session.ts` |
| SDK 工厂 | `packages/coding-agent/src/core/sdk.ts` |
| 会话服务 | `packages/coding-agent/src/core/agent-session-services.ts` |
| 工具总览 | `packages/coding-agent/src/core/tools/index.ts` |
| 扩展类型 | `packages/coding-agent/src/core/extensions/types.ts` |
| 扩展运行器 | `packages/coding-agent/src/core/extensions/runner.ts` |
| 扩展加载器 | `packages/coding-agent/src/core/extensions/loader.ts` |
| 会话管理 | `packages/coding-agent/src/core/session-manager.ts` |
| 设置管理 | `packages/coding-agent/src/core/settings-manager.ts` |
| 模型注册 | `packages/coding-agent/src/core/model-registry.ts` |
| 认证存储 | `packages/coding-agent/src/core/auth-storage.ts` |
| 交互模式 | `packages/coding-agent/src/modes/interactive/interactive-mode.ts` |
| 打印模式 | `packages/coding-agent/src/modes/print-mode.ts` |
| RPC 客户端 | `packages/coding-agent/src/modes/rpc/rpc-client.ts` |

### 8.4 TUI

| 功能 | 文件路径 |
|------|----------|
| TUI 核心 | `packages/tui/src/tui.ts` |
| 组件接口 | `packages/tui/src/tui.ts` (Component, Focusable) |
| 终端抽象 | `packages/tui/src/terminal.ts` |
| 键盘处理 | `packages/tui/src/keys.ts` |
| 键位绑定 | `packages/tui/src/keybindings.ts` |
| 终端图片 | `packages/tui/src/terminal-image.ts` |
| Markdown | `packages/tui/src/components/markdown.ts` |
| 编辑器 | `packages/tui/src/components/editor.ts` |

### 8.5 Web UI

| 功能 | 文件路径 |
|------|----------|
| 主入口 | `packages/web-ui/src/index.ts` |
| 聊天面板 | `packages/web-ui/src/ChatPanel.ts` |
| 消息组件 | `packages/web-ui/src/components/Messages.js` |
| 存储系统 | `packages/web-ui/src/storage/` |

---

## 九、架构特点总结

### 9.1 分层清晰

- **AI 层**：纯粹的 LLM API 抽象，不依赖任何上层
- **Agent 层**：通用的 Agent 运行时，可复用于非 coding 场景
- **Coding Agent**：特定领域的 CLI 应用，通过扩展保持可扩展性
- **TUI / Web UI**：独立的 UI 层，可被不同应用复用

### 9.2 事件驱动

全链路采用事件驱动架构：
- AI 层：`AssistantMessageEventStream`
- Agent 层：`AgentEvent`
- Coding Agent：`AgentSessionEvent`

### 9.3 高度可扩展

- **Provider 扩展**：通过 `registerApiProvider()` 注册新 LLM Provider
- **工具扩展**：通过 Extension 系统注册自定义工具
- **UI 扩展**：通过 ExtensionUIContext 定制交互
- **命令扩展**：注册斜杠命令和快捷键

### 9.4 类型安全

- 全链路 TypeScript，严格的类型定义
- 使用 TypeBox 进行运行时参数校验
- 声明合并支持自定义消息类型

### 9.5 流式优先

从 LLM Provider 到终端渲染，全链路支持流式处理：
- 流式 API 调用
- 流式事件分发
- 流式终端渲染（差分更新）
- 流式工具执行（支持 partial updates）
