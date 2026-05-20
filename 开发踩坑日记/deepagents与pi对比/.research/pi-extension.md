# pi 项目扩展机制深度分析

> 研究范围：pi (https://github.com/earendil-works/pi-mono)  
> 分析日期：2026-05-15  
> 分析者：Claude Code Agent

---

## 1. 项目概述

pi 是一个 TypeScript monorepo，包含 5 个核心包：

| 包名 | 路径 | 职责 |
|------|------|------|
| `packages/ai` | `packages/ai/src/` | 统一多 provider LLM API 抽象层 |
| `packages/agent` | `packages/agent/src/` | Agent runtime（循环、状态、事件） |
| `packages/coding-agent` | `packages/coding-agent/src/` | 交互式 coding agent CLI |
| `packages/tui` | `packages/tui/src/` | 终端 UI 库 |
| `packages/web-ui` | `packages/web-ui/src/` | Web 组件 |

扩展机制分布在 `packages/ai`、`packages/agent`、`packages/coding-agent` 三个包中，形成从底层到上层的分层扩展体系。

---

## 2. LLM Provider 扩展机制

### 2.1 核心注册表

**文件**: `packages/ai/src/api-registry.ts`

Provider 注册基于一个全局 Map：`apiProviderRegistry`，键为 API 标识符，值为 provider 实现。

```typescript
// 核心接口
export interface ApiProvider<TApi extends Api = Api, TOptions extends StreamOptions = StreamOptions> {
  api: TApi;
  stream: StreamFunction<TApi, TOptions>;
  streamSimple: StreamFunction<TApi, SimpleStreamOptions>;
}

// 注册函数
export function registerApiProvider<TApi extends Api, TOptions extends StreamOptions>(
  provider: ApiProvider<TApi, TOptions>,
  sourceId?: string,
): void

// 查询函数
export function getApiProvider(api: Api): ApiProviderInternal | undefined
export function getApiProviders(): ApiProviderInternal[]
export function unregisterApiProviders(sourceId: string): void
export function clearApiProviders(): void
```

**扩展方式**：
- 调用 `registerApiProvider()` 注册新的 API provider
- 通过 `sourceId` 支持按来源批量注销（用于扩展热重载）
- `unregisterApiProviders(sourceId)` 可清理特定扩展注册的 provider

### 2.2 Lazy Registration 模式

**文件**: `packages/ai/src/providers/register-builtins.ts`

所有内置 provider 均采用 **懒加载（lazy load）** 模式：

```typescript
// 懒加载模块接口
interface LazyProviderModule<TApi extends Api, TOptions extends StreamOptions, TSimpleOptions extends SimpleStreamOptions> {
  stream: (model: Model<TApi>, context: Context, options?: TOptions) => AsyncIterable<AssistantMessageEvent>;
  streamSimple: (model: Model<TApi>, context: Context, options?: TSimpleOptions) => AsyncIterable<AssistantMessageEvent>;
}

// 懒加载工厂函数
function createLazyStream<TApi extends Api, TOptions extends StreamOptions, TSimpleOptions extends SimpleStreamOptions>(
  loadModule: () => Promise<LazyProviderModule<TApi, TOptions, TSimpleOptions>>,
): StreamFunction<TApi, TOptions>

// 每个 provider 的加载器
function loadAnthropicProviderModule(): Promise<LazyProviderModule<"anthropic-messages", ...>> {
  anthropicProviderModulePromise ||= import("./anthropic.js").then((module) => ({
    stream: module.streamAnthropic,
    streamSimple: module.streamSimpleAnthropic,
  }));
  return anthropicProviderModulePromise;
}
```

**懒加载机制**：
1. 使用 `import()` 动态导入 provider 实现模块
2. Promise 缓存（`||=`）确保同一 provider 只加载一次
3. `createLazyStream` 包装器在首次流式调用时触发加载
4. 加载失败时返回包含错误信息的 `AssistantMessage`

**已支持的 Provider**（共 9 个）：
- `anthropic-messages` — Anthropic Messages API
- `openai-completions` — OpenAI Completions API
- `openai-responses` — OpenAI Responses API
- `openai-codex-responses` — OpenAI Codex Responses
- `azure-openai-responses` — Azure OpenAI Responses
- `mistral-conversations` — Mistral Conversations
- `google-generative-ai` — Google Generative AI
- `google-vertex` — Google Vertex AI
- `bedrock-converse-stream` — Amazon Bedrock

### 2.3 添加新 Provider 的步骤

根据 `AGENTS.md` 文档，添加新 provider 需要修改 7 个层面：

1. **Core Types** (`packages/ai/src/types.ts`)
   - 在 `Api` union type 中添加新 API 标识符
   - 创建 options interface 继承 `StreamOptions`
   - 添加到 `ApiOptionsMap`
   - 在 `KnownProvider` union 中添加 provider 名称

2. **Provider Implementation** (`packages/ai/src/providers/<provider>.ts`)
   - 导出 `stream<Provider>()` 返回 `AssistantMessageEventStream`
   - 导出 `streamSimple<Provider>()` 用于 `SimpleStreamOptions`
   - 实现消息/工具转换函数
   - 响应解析发射标准化事件：`text`、`tool_call`、`thinking`、`usage`、`stop`

3. **Exports & Lazy Registration**
   - 在 `packages/ai/package.json` 添加 subpath export
   - 在 `packages/ai/src/index.ts` 添加 `export type`
   - 在 `register-builtins.ts` 中通过 lazy loader 注册
   - 在 `env-api-keys.ts` 添加凭证检测

4. **Model Generation** (`packages/ai/scripts/generate-models.ts`)
   - 添加从 provider 源获取/解析模型的逻辑
   - 映射到标准 `Model` 接口

5. **Tests** (`packages/ai/test/`)
   - 在 `stream.test.ts` 添加至少一个代表性模型
   - 在 provider matrix 测试中添加

6. **Coding Agent** (`packages/coding-agent/`)
   - `model-resolver.ts`: 添加默认模型 ID
   - `provider-display-names.ts`: 添加显示名称
   - `cli/args.ts`: 添加环境变量文档
   - `README.md` / `docs/providers.md`: 添加文档

7. **Documentation**
   - `packages/ai/README.md`: 添加到 providers 表格
   - `packages/ai/CHANGELOG.md`: 添加条目

---

## 3. 工具注册机制

### 3.1 Agent Core 层工具定义

**文件**: `packages/agent/src/types.ts`

```typescript
export interface AgentTool<TParameters extends TSchema = TSchema, TDetails = any> extends Tool<TParameters> {
  label: string;
  prepareArguments?: (args: unknown) => Static<TParameters>;
  execute: (
    toolCallId: string,
    params: Static<TParameters>,
    signal?: AbortSignal,
    onUpdate?: AgentToolUpdateCallback<TDetails>,
  ) => Promise<AgentToolResult<TDetails>>;
  executionMode?: ToolExecutionMode; // "sequential" | "parallel"
}
```

**工具调用流程**：
1. LLM 输出 `tool_call` 内容块
2. Agent loop 解析工具调用参数
3. 通过 `validateToolArguments` 验证参数（schema 校验）
4. 调用 `beforeToolCall` 钩子（可拦截）
5. 执行 `AgentTool.execute()`
6. 调用 `afterToolCall` 钩子（可修改结果）
7. 生成 `toolResult` 消息并加入上下文

### 3.2 Coding Agent 层工具定义

**文件**: `packages/coding-agent/src/core/tools/index.ts`

Coding agent 提供 7 个内置工具：

| 工具 | 工厂函数 | 定义工厂 |
|------|----------|----------|
| read | `createReadTool()` | `createReadToolDefinition()` |
| bash | `createBashTool()` | `createBashToolDefinition()` |
| edit | `createEditTool()` | `createEditToolDefinition()` |
| write | `createWriteTool()` | `createWriteToolDefinition()` |
| grep | `createGrepTool()` | `createGrepToolDefinition()` |
| find | `createFindTool()` | `createFindToolDefinition()` |
| ls | `createLsTool()` | `createLsToolDefinition()` |

工具创建采用 **工厂模式**，每个工具通过 `createXxxTool()` 创建 `AgentTool` 实例，通过 `createXxxToolDefinition()` 创建 `ToolDefinition`（用于扩展系统）。

### 3.3 扩展系统工具注册

**文件**: `packages/coding-agent/src/core/extensions/types.ts`

扩展可以通过 `ExtensionAPI.registerTool()` 注册自定义工具：

```typescript
export interface ExtensionAPI {
  registerTool<TParams extends TSchema = TSchema, TDetails = unknown, TState = any>(
    tool: ToolDefinition<TParams, TDetails, TState>,
  ): void;
}

export interface ToolDefinition<TParams extends TSchema = TSchema, TDetails = unknown, TState = any> {
  name: string;
  label: string;
  description: string;
  promptSnippet?: string;
  promptGuidelines?: string[];
  parameters: TParams;
  renderShell?: "default" | "self";
  prepareArguments?: (args: unknown) => Static<TParams>;
  executionMode?: ToolExecutionMode;
  execute(toolCallId, params, signal, onUpdate, ctx): Promise<AgentToolResult<TDetails>>;
  renderCall?: (args, theme, context) => Component;
  renderResult?: (result, options, theme, context) => Component;
}
```

**工具注册特点**：
- 使用 TypeBox schema 定义参数类型
- 支持自定义 `renderCall` 和 `renderResult` 用于 TUI 渲染
- `promptSnippet` 和 `promptGuidelines` 可自动注入系统提示
- `executionMode` 支持逐工具覆盖并行/串行执行模式

### 3.4 Web UI 工具渲染扩展

**文件**: `packages/web-ui/src/tools/index.ts`

```typescript
export function registerToolRenderer(toolName: string, renderer: ToolRenderer): void
export function getToolRenderer(toolName: string): ToolRenderer | undefined
export function renderTool(toolName, params, result, isStreaming): ToolRenderResult
```

Web UI 有独立的工具渲染注册表，与 TUI 的渲染系统分离。内置 renderer：
- `BashRenderer` — bash 命令渲染
- `DefaultRenderer` — 默认 JSON 渲染

---

## 4. Agent 状态扩展

### 4.1 AgentState 接口

**文件**: `packages/agent/src/types.ts`

```typescript
export interface AgentState {
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

### 4.2 自定义消息类型（Declaration Merging）

**关键扩展点**：通过 TypeScript 的 declaration merging 扩展消息类型：

```typescript
// packages/agent/src/types.ts:292-301
export interface CustomAgentMessages {
  // Empty by default - apps extend via declaration merging
}

export type AgentMessage = Message | CustomAgentMessages[keyof CustomAgentMessages];
```

**使用示例**：
```typescript
declare module "@earendil-works/pi-agent-core" {
  interface CustomAgentMessages {
    artifact: ArtifactMessage;
    notification: NotificationMessage;
  }
}
```

### 4.3 Agent 构造选项

**文件**: `packages/agent/src/agent.ts:95-115`

```typescript
export interface AgentOptions {
  initialState?: Partial<...>;
  convertToLlm?: (messages: AgentMessage[]) => Message[] | Promise<Message[]>;
  transformContext?: (messages: AgentMessage[], signal?: AbortSignal) => Promise<AgentMessage[]>;
  streamFn?: StreamFn;
  getApiKey?: (provider: string) => Promise<string | undefined> | string | undefined;
  onPayload?: SimpleStreamOptions["onPayload"];
  onResponse?: SimpleStreamOptions["onResponse"];
  beforeToolCall?: (context, signal?) => Promise<BeforeToolCallResult | undefined>;
  afterToolCall?: (context, signal?) => Promise<AfterToolCallResult | undefined>;
  prepareNextTurn?: (signal?) => Promise<AgentLoopTurnUpdate | undefined>;
  steeringMode?: QueueMode;
  followUpMode?: QueueMode;
  sessionId?: string;
  thinkingBudgets?: ThinkingBudgets;
  transport?: Transport;
  maxRetryDelayMs?: number;
  toolExecution?: ToolExecutionMode;
}
```

**状态扩展钩子**：
- `convertToLlm`: 自定义消息转换逻辑
- `transformContext`: 上下文窗口管理（剪枝、注入外部上下文）
- `beforeToolCall` / `afterToolCall`: 工具调用前后拦截
- `prepareNextTurn`: 每轮结束后修改下一轮状态

---

## 5. 扩展系统（Extension System）

### 5.1 架构概览

**核心文件**：
- `packages/coding-agent/src/core/extensions/loader.ts` — 扩展加载
- `packages/coding-agent/src/core/extensions/runner.ts` — 扩展运行时
- `packages/coding-agent/src/core/extensions/types.ts` — 类型定义

### 5.2 扩展加载机制

**加载流程**：
1. `discoverAndLoadExtensions()` 从三个来源发现扩展：
   - 项目本地：`cwd/.pi/extensions/`
   - 全局：`~/.pi/agent/extensions/`
   - 显式配置路径

2. 发现规则：
   - 直接文件：`extensions/*.ts` 或 `*.js`
   - 子目录含 `index.ts`/`index.js`
   - 子目录含 `package.json` 且 `"pi".extensions` 字段声明入口

3. 使用 **jiti** 加载 TypeScript 模块（支持 Bun binary 和 Node.js 两种模式）

4. 每个扩展必须导出一个 **factory function**：
```typescript
export type ExtensionFactory = (pi: ExtensionAPI) => void | Promise<void>;
```

### 5.3 扩展 API

**文件**: `packages/coding-agent/src/core/extensions/types.ts:1084-1311`

```typescript
export interface ExtensionAPI {
  // === 事件订阅 ===
  on(event: "resources_discover", handler: ...): void;
  on(event: "session_start", handler: ...): void;
  on(event: "context", handler: ...): void;
  on(event: "before_provider_request", handler: ...): void;
  on(event: "after_provider_response", handler: ...): void;
  on(event: "before_agent_start", handler: ...): void;
  on(event: "agent_start", handler: ...): void;
  on(event: "agent_end", handler: ...): void;
  on(event: "turn_start", handler: ...): void;
  on(event: "turn_end", handler: ...): void;
  on(event: "message_start" | "message_update" | "message_end", handler: ...): void;
  on(event: "tool_execution_start" | "tool_execution_update" | "tool_execution_end", handler: ...): void;
  on(event: "tool_call", handler: ...): void;
  on(event: "tool_result", handler: ...): void;
  on(event: "model_select", handler: ...): void;
  on(event: "input", handler: ...): void;
  on(event: "user_bash", handler: ...): void;
  // ... 共 30+ 个事件类型

  // === 工具注册 ===
  registerTool(tool: ToolDefinition): void;

  // === 命令/快捷键/Flag 注册 ===
  registerCommand(name: string, options: Omit<RegisteredCommand, "name" | "sourceInfo">): void;
  registerShortcut(shortcut: KeyId, options: { description?: string; handler: ... }): void;
  registerFlag(name: string, options: { description?: string; type: "boolean" | "string"; default? }): void;
  getFlag(name: string): boolean | string | undefined;

  // === 消息渲染 ===
  registerMessageRenderer<T>(customType: string, renderer: MessageRenderer<T>): void;

  // === 动作 ===
  sendMessage(message, options?): void;
  sendUserMessage(content, options?): void;
  appendEntry(customType: string, data?): void;
  setSessionName(name: string): void;
  getSessionName(): string | undefined;
  setLabel(entryId: string, label?: string): void;
  exec(command: string, args: string[], options?): Promise<ExecResult>;
  getActiveTools(): string[];
  getAllTools(): ToolInfo[];
  setActiveTools(toolNames: string[]): void;
  getCommands(): SlashCommandInfo[];
  setModel(model: Model<any>): Promise<boolean>;
  getThinkingLevel(): ThinkingLevel;
  setThinkingLevel(level: ThinkingLevel): void;

  // === Provider 注册 ===
  registerProvider(name: string, config: ProviderConfig): void;
  unregisterProvider(name: string): void;

  // === 事件总线 ===
  events: EventBus;
}
```

### 5.4 事件系统

**完整事件列表**（按类别）：

| 类别 | 事件 | 可取消/可修改 |
|------|------|--------------|
| 资源发现 | `resources_discover` | 可返回路径 |
| Session | `session_start`, `session_before_switch`, `session_before_fork`, `session_before_compact`, `session_compact`, `session_shutdown`, `session_before_tree`, `session_tree` | 部分可取消 |
| 上下文 | `context` | 可修改 messages |
| Provider | `before_provider_request`, `after_provider_response` | 可修改 payload |
| Agent 生命周期 | `before_agent_start`, `agent_start`, `agent_end` | 可修改 systemPrompt |
| Turn | `turn_start`, `turn_end` | — |
| 消息 | `message_start`, `message_update`, `message_end` | `message_end` 可替换消息 |
| 工具执行 | `tool_execution_start`, `tool_execution_update`, `tool_execution_end` | — |
| 工具调用 | `tool_call` | 可 block |
| 工具结果 | `tool_result` | 可修改 content/details/isError |
| 模型 | `model_select`, `thinking_level_select` | — |
| 用户输入 | `input` | 可 transform 或 handle |
| 用户 Bash | `user_bash` | 可自定义执行 |

### 5.5 扩展运行时生命周期

**文件**: `packages/coding-agent/src/core/extensions/runner.ts`

```
加载阶段 (loader.ts)
  ├─ createExtensionRuntime() — 创建带 stub action 的运行时
  ├─ loadExtensionModule() — 用 jiti 加载 TS 模块
  ├─ createExtensionAPI() — 创建 API 对象
  └─ factory(api) — 执行扩展工厂函数

绑定阶段 (runner.bindCore())
  ├─ 替换 runtime 中的 action stubs 为真实实现
  ├─ flush pendingProviderRegistrations
  └─ 此后 provider 注册立即生效

绑定命令上下文 (runner.bindCommandContext())
  └─ 注入 session 控制方法

绑定 UI (runner.setUIContext())
  └─ 注入 UI 交互方法

运行时
  ├─ emit() — 通用事件发射
  ├─ emitToolCall() — 工具调用拦截
  ├─ emitToolResult() — 工具结果修改
  ├─ emitContext() — 上下文修改
  ├─ emitBeforeProviderRequest() — payload 修改
  └─ emitBeforeAgentStart() — systemPrompt 修改
```

### 5.6 虚拟模块系统（Bun Binary 支持）

**文件**: `packages/coding-agent/src/core/extensions/loader.ts:44-61`

为支持编译为 Bun binary 后扩展仍能 import 依赖，实现了虚拟模块系统：

```typescript
const VIRTUAL_MODULES: Record<string, unknown> = {
  "typebox": _bundledTypebox,
  "@sinclair/typebox": _bundledTypebox,
  "@earendil-works/pi-agent-core": _bundledPiAgentCore,
  "@earendil-works/pi-tui": _bundledPiTui,
  "@earendil-works/pi-ai": _bundledPiAi,
  "@earendil-works/pi-coding-agent": _bundledPiCodingAgent,
  // ... 以及旧包名别名
};
```

在 Bun binary 模式下，jiti 使用 `virtualModules` 选项；在 Node.js 开发模式下使用 `alias` 选项。

---

## 6. Coding Agent 自定义机制

### 6.1 Prompt 模板系统

**文件**: `packages/coding-agent/src/core/prompt-templates.ts`

Prompt 模板从三个来源加载：
1. 全局：`~/.pi/agent/prompts/*.md`
2. 项目本地：`cwd/.pi/prompts/*.md`
3. 显式路径

模板文件格式（YAML frontmatter + body）：
```markdown
---
description: "模板描述"
argument-hint: "参数提示"
---
模板内容，支持 $1, $2, $@, $ARGUMENTS, ${@:N}, ${@:N:L}
```

通过 `/templateName args...` 语法触发模板扩展。

### 6.2 Skills 系统

**文件**: `packages/coding-agent/src/core/skills.ts`

Skills 是 Markdown 文件，遵循 [agentskills.io](https://agentskills.io) 标准：

- 目录含 `SKILL.md` 即被视为一个 skill
- 支持 YAML frontmatter：`name`, `description`, `disable-model-invocation`
- 通过 `formatSkillsForPrompt()` 格式化为 XML 注入系统提示

加载来源：
1. `~/.pi/agent/skills/`（全局）
2. `cwd/.pi/skills/`（项目本地）
3. 显式路径

### 6.3 系统提示构建

**文件**: `packages/coding-agent/src/core/system-prompt.ts`

```typescript
export interface BuildSystemPromptOptions {
  customPrompt?: string;        // 完全替换默认提示
  selectedTools?: string[];     // 启用的工具列表
  toolSnippets?: Record<string, string>;  // 工具单行描述
  promptGuidelines?: string[];  // 额外指南
  appendSystemPrompt?: string;  // 追加文本
  cwd: string;
  contextFiles?: Array<{ path: string; content: string }>;
  skills?: Skill[];
}
```

扩展可通过 `before_agent_start` 事件的 `systemPrompt` 返回值修改系统提示。

### 6.4 快捷键系统

**文件**: `packages/coding-agent/src/core/keybindings.ts`

```typescript
export interface AppKeybindings {
  "app.interrupt": true;
  "app.clear": true;
  "app.exit": true;
  "app.model.cycleForward": true;
  // ... 共 40+ 个快捷键
}

export const KEYBINDINGS = {
  ...TUI_KEYBINDINGS,
  "app.interrupt": { defaultKeys: "escape", description: "Cancel or abort" },
  "app.clear": { defaultKeys: "ctrl+c", description: "Clear editor" },
  // ...
} as const satisfies KeybindingDefinitions;
```

**自定义方式**：
- 用户通过 `~/.pi/agent/keybindings.json` 覆盖默认快捷键
- 扩展通过 `registerShortcut()` 注册新快捷键
- 内置快捷键冲突检测：扩展快捷键不能与保留快捷键冲突

### 6.5 主题系统

**文件**: `packages/coding-agent/src/modes/interactive/theme/theme.ts`

主题使用 JSON 文件定义，包含 50+ 个颜色值：

```typescript
const ThemeJsonSchema = Type.Object({
  name: Type.String(),
  vars: Type.Optional(Type.Record(Type.String(), ColorValueSchema)),
  colors: Type.Object({
    accent: ColorValueSchema,
    border: ColorValueSchema,
    // ... 50+ 颜色定义
  }),
});
```

主题加载来源：
1. 内置主题：`packages/coding-agent/src/modes/interactive/theme/{dark,light}.json`
2. 用户自定义：`~/.pi/agent/themes/*.json`
3. 扩展可通过 `resources_discover` 事件返回 `themePaths`

### 6.6 配置系统

**文件**: `packages/coding-agent/src/core/settings-manager.ts`

配置层级（后覆盖前）：
1. 内置默认值
2. `~/.pi/agent/settings.json`（全局用户配置）
3. `cwd/.pi/settings.json`（项目本地配置）
4. CLI 参数

```typescript
export interface Settings {
  defaultProvider?: string;
  defaultModel?: string;
  defaultThinkingLevel?: ThinkingLevel;
  transport?: TransportSetting;
  theme?: string;
  compaction?: CompactionSettings;
  retry?: RetrySettings;
  terminal?: TerminalSettings;
  images?: ImageSettings;
  thinkingBudgets?: ThinkingBudgetsSettings;
  markdown?: MarkdownSettings;
  warnings?: WarningSettings;
  // 扩展相关
  packages?: PackageSource[];
  extensions?: string[];
  skills?: string[];
  prompts?: string[];
  themes?: string[];
  enabledModels?: string[];
  // ...
}
```

---

## 7. Web UI 组件扩展

### 7.1 消息渲染注册表

**文件**: `packages/web-ui/src/components/message-renderer-registry.ts`

```typescript
export interface MessageRenderer<TMessage extends AgentMessage = AgentMessage> {
  render(message: TMessage): TemplateResult;
}

export function registerMessageRenderer<TRole extends MessageRole>(
  role: TRole,
  renderer: MessageRenderer<Extract<AgentMessage, { role: TRole }>>,
): void

export function getMessageRenderer(role: MessageRole): MessageRenderer | undefined
```

通过 `registerMessageRenderer()` 可按消息角色注册自定义渲染器。

### 7.2 工具渲染注册表

**文件**: `packages/web-ui/src/tools/renderer-registry.ts`

```typescript
export interface ToolRenderer {
  render(params: any, result: ToolResultMessage | undefined, isStreaming?: boolean): ToolRenderResult;
}

export function registerToolRenderer(toolName: string, renderer: ToolRenderer): void
export function getToolRenderer(toolName: string): ToolRenderer | undefined
```

### 7.3 Sandbox Runtime Provider

**文件**: `packages/web-ui/src/components/sandbox/`

Web UI 支持通过 `SandboxRuntimeProvider` 扩展沙箱运行时能力：

```typescript
export interface SandboxRuntimeProvider {
  readonly name: string;
  canHandle(url: string): boolean;
  createSandbox(url: string, iframe: HTMLIFrameElement): Promise<SandboxResult>;
}
```

内置 provider：
- `ArtifactsRuntimeProvider` — 代码产物运行
- `AttachmentsRuntimeProvider` — 附件处理
- `ConsoleRuntimeProvider` — 控制台日志
- `FileDownloadRuntimeProvider` — 文件下载

---

## 8. 模块/插件系统总结

### 8.1 扩展机制矩阵

| 扩展点 | 机制 | 文件位置 | 动态性 |
|--------|------|----------|--------|
| LLM Provider | 全局注册表 + lazy load | `packages/ai/src/api-registry.ts` | 运行时注册 |
| 工具 | ExtensionAPI.registerTool | `packages/coding-agent/src/core/extensions/` | 运行时注册 |
| 命令 | ExtensionAPI.registerCommand | `packages/coding-agent/src/core/extensions/` | 运行时注册 |
| 快捷键 | ExtensionAPI.registerShortcut | `packages/coding-agent/src/core/extensions/` | 运行时注册 |
| CLI Flag | ExtensionAPI.registerFlag | `packages/coding-agent/src/core/extensions/` | 启动时注册 |
| 事件钩子 | ExtensionAPI.on(event, handler) | `packages/coding-agent/src/core/extensions/` | 运行时订阅 |
| 消息渲染 | registerMessageRenderer | `packages/web-ui/src/components/` | 运行时注册 |
| 工具渲染 | registerToolRenderer | `packages/web-ui/src/tools/` | 运行时注册 |
| 主题 | JSON 文件 + 发现机制 | `theme.ts` + `resources_discover` | 热重载 |
| Skills | Markdown 文件 + 发现机制 | `skills.ts` + `resources_discover` | 热重载 |
| Prompt 模板 | Markdown 文件 + 发现机制 | `prompt-templates.ts` | 热重载 |
| 自定义消息类型 | Declaration Merging | `packages/agent/src/types.ts` | 编译时 |

### 8.2 扩展加载优先级

```
1. 内置 provider（registerBuiltInApiProviders）
2. 内置工具（createAllTools）
3. 内置主题、skills、prompts
4. 扩展（discoverAndLoadExtensions）
   ├─ 项目本地扩展
   ├─ 全局扩展
   └─ 显式配置扩展
5. 扩展注册的工具、命令、快捷键、provider
6. 用户配置（settings.json、keybindings.json）
```

### 8.3 设计特点

1. **分层扩展**：从底层 `packages/ai` 的 provider 注册，到 `packages/agent` 的工具/状态扩展，再到 `packages/coding-agent` 的完整扩展系统，层次分明

2. **事件驱动**：扩展系统基于丰富的事件总线，30+ 事件类型覆盖完整的 Agent 生命周期

3. **懒加载优化**：Provider 实现采用懒加载，减少启动时间和内存占用

4. **TypeScript 原生**：扩展使用 TypeScript 编写，通过 jiti 运行时加载，保持类型安全

5. **热重载支持**：通过 `/reload` 命令可重新加载扩展、skills、prompts、主题

6. **Bun Binary 兼容**：虚拟模块系统确保编译为独立二进制后扩展仍能正常工作

7. **声明合并**：利用 TypeScript 的 declaration merging 实现消息类型扩展，无需修改核心代码

---

## 9. 关键代码路径索引

| 功能 | 文件路径 |
|------|----------|
| Provider 注册表 | `packages/ai/src/api-registry.ts` |
| Provider 懒加载 | `packages/ai/src/providers/register-builtins.ts` |
| Agent 状态/工具 | `packages/agent/src/types.ts` |
| Agent 类 | `packages/agent/src/agent.ts` |
| Agent 循环 | `packages/agent/src/agent-loop.ts` |
| 扩展类型定义 | `packages/coding-agent/src/core/extensions/types.ts` |
| 扩展加载器 | `packages/coding-agent/src/core/extensions/loader.ts` |
| 扩展运行时 | `packages/coding-agent/src/core/extensions/runner.ts` |
| 工具定义 | `packages/coding-agent/src/core/tools/index.ts` |
| 系统提示构建 | `packages/coding-agent/src/core/system-prompt.ts` |
| Prompt 模板 | `packages/coding-agent/src/core/prompt-templates.ts` |
| Skills 加载 | `packages/coding-agent/src/core/skills.ts` |
| 快捷键管理 | `packages/coding-agent/src/core/keybindings.ts` |
| 主题系统 | `packages/coding-agent/src/modes/interactive/theme/theme.ts` |
| 配置管理 | `packages/coding-agent/src/core/settings-manager.ts` |
| 模型注册表 | `packages/coding-agent/src/core/model-registry.ts` |
| Web UI 消息渲染 | `packages/web-ui/src/components/message-renderer-registry.ts` |
| Web UI 工具渲染 | `packages/web-ui/src/tools/renderer-registry.ts` |
| 添加 Provider 指南 | `AGENTS.md` (第 123-175 行) |
