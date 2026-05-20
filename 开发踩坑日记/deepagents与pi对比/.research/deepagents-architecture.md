# DeepAgents 架构深度分析

## 1. 整体架构

### 1.1 Monorepo 结构

```
deepagents/
├── libs/
│   ├── deepagents/          # SDK 核心包 (v0.6.1)
│   ├── cli/                 # CLI 工具包 (v0.0.59)
│   ├── acp/                 # Agent Context Protocol (v0.0.6)
│   ├── evals/               # 评估框架 (v0.0.1)
│   ├── code/                # 代码相关功能
│   └── partners/            # 第三方集成
│       ├── daytona/         # Daytona 沙箱集成
│       ├── modal/           # Modal 集成
│       ├── runloop/         # Runloop 集成
│       └── quickjs/         # QuickJS 集成
├── examples/                # 示例项目
│   ├── async-subagent-server/
│   ├── content-builder-agent/
│   ├── deep_research/
│   └── ...
├── AGENTS.md               # 项目级代理上下文
├── Makefile                # 构建脚本
└── README.md
```

### 1.2 包依赖关系

```
deepagents-cli (v0.0.59)
├── deepagents (v0.6.1) [核心依赖]
├── deepagents-acp (v0.0.6) [ACP 支持]
├── langgraph>=1.2.0 [图运行时]
├── langchain>=1.3.0 [Agent 框架]
├── textual>=8.2.5 [TUI 框架]
└── 各种模型提供商适配器

deepagents-acp (v0.0.6)
├── deepagents [核心依赖]
└── agent-client-protocol>=0.8.0 [ACP 协议]

deepagents-evals (v0.0.1)
├── deepagents>=0.5.7
├── deepagents-cli
└── harbor>=0.6.4 [评估运行时]
```

### 1.3 构建系统

- **deepagents SDK**: setuptools (传统构建)
- **cli/acp**: hatchling (现代构建)
- **evals**: setuptools
- 使用 `uv` 进行依赖管理和 editable 安装
- 每个包独立的 `pyproject.toml`

---

## 2. SDK 核心: `create_deep_agent`

### 2.1 入口函数

**文件**: `libs/deepagents/deepagents/graph.py:216`

```python
def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format: ResponseFormat[ResponseT] | type[ResponseT] | dict[str, Any] | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph[...]
```

### 2.2 核心架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    create_deep_agent                         │
├─────────────────────────────────────────────────────────────┤
│  1. 模型解析 (resolve_model)                                  │
│  2. HarnessProfile 选择 (_harness_profile_for_model)          │
│  3. 子代理处理 (SubAgent/CompiledSubAgent/AsyncSubAgent)       │
│  4. 中间件栈构建                                              │
│  5. 系统提示词组装 (_apply_profile_prompt)                     │
│  6. 调用 langchain.agents.create_agent 创建图                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 默认中间件栈 (从底到顶)

```
Base Stack:
├── TodoListMiddleware              # 待办事项管理
├── SkillsMiddleware (optional)     # 技能加载
├── FilesystemMiddleware            # 文件系统工具
├── SubAgentMiddleware              # 子代理调用 (task 工具)
├── AsyncSubAgentMiddleware         # 异步子代理
├── SummarizationMiddleware         # 自动摘要
├── PatchToolCallsMiddleware        # 工具调用补丁
│
User Middleware (插入点)
│
Tail Stack:
├── HarnessProfile.extra_middleware # 配置文件额外中间件
├── _ToolExclusionMiddleware        # 工具排除
├── AnthropicPromptCachingMiddleware # Anthropic 提示缓存
├── MemoryMiddleware (optional)     # 记忆加载
└── HumanInTheLoopMiddleware (optional) # 人工审批
```

### 2.4 状态结构

**文件**: `libs/deepagents/deepagents/graph.py:63`

```python
class _DeepAgentState(AgentState):
    """使用 DeltaChannel 减少 checkpoint 增长从 O(N²) 到 O(N)"""
    messages: Annotated[list[AnyMessage], DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]
```

---

## 3. 工具系统

### 3.1 内置工具集

**文件**: `libs/deepagents/deepagents/middleware/filesystem.py`

| 工具 | 功能 | 对应后端方法 |
|------|------|-------------|
| `ls` | 列出目录内容 | `backend.ls()` |
| `read_file` | 读取文件 (支持分页) | `backend.read()` |
| `write_file` | 写入新文件 | `backend.write()` |
| `edit_file` | 编辑文件 (字符串替换) | `backend.edit()` |
| `glob` | 文件模式匹配 | `backend.glob()` |
| `grep` | 文本搜索 | `backend.grep()` |
| `execute` | 执行 shell 命令 | `backend.execute()` (需 SandboxBackendProtocol) |
| `task` | 调用子代理 | SubAgentMiddleware |
| `write_todos` | 管理待办事项 | TodoListMiddleware (来自 langchain) |

### 3.2 工具描述覆盖

**文件**: `libs/deepagents/deepagents/_tools.py:29`

```python
def _apply_tool_description_overrides(
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None,
    overrides: Mapping[str, str],
) -> list[BaseTool | Callable | dict[str, Any]] | None:
    """应用工具描述覆盖，不修改调用者拥有的工具"""
```

### 3.3 文件系统权限

**文件**: `libs/deepagents/deepagents/middleware/filesystem.py:76`

```python
@dataclass
class FilesystemPermission:
    operations: list[FilesystemOperation]  # ["read", "write"]
    paths: list[str]                       # ["/workspace/*"]
    mode: Literal["allow", "deny"] = "allow"
```

---

## 4. 后端系统 (Backend)

### 4.1 后端协议层次

```
BackendProtocol (基础文件操作)
├── StateBackend        # 存储在 LangGraph 状态中 (ephemeral)
├── FilesystemBackend   # 直接读写文件系统
├── StoreBackend        # 持久化存储
└── CompositeBackend    # 路由到多个后端

SandboxBackendProtocol (扩展执行能力)
├── BaseSandbox         # 抽象基类
├── LocalShellBackend   # 本地 shell 执行
└── 第三方沙箱 (Daytona, Modal, Runloop)
```

### 4.2 关键后端实现

#### StateBackend
**文件**: `libs/deepagents/deepagents/backends/state.py:38`

- 使用 LangGraph 的 `CONFIG_KEY_READ` / `CONFIG_KEY_SEND` 进行状态读写
- 文件存储在 agent state 中，随对话线程持久化
- 支持 v1 (list[str]) 和 v2 (str + encoding) 格式

#### FilesystemBackend
**文件**: `libs/deepagents/deepagents/backends/filesystem.py:44`

- 直接访问本地文件系统
- 支持 virtual_mode 路径隔离
- 使用 ripgrep 加速搜索 (回退到 Python 实现)

#### BaseSandbox
**文件**: `libs/deepagents/deepagents/backends/sandbox.py:394`

- 通过 `execute()` 在远程环境执行命令
- 文件操作通过上传/下载实现
- 支持服务器端分页读取和编辑

### 4.3 后端协议接口

**文件**: `libs/deepagents/deepagents/backends/protocol.py:319`

```python
class BackendProtocol(abc.ABC):
    def ls(self, path: str) -> LsResult
    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult
    def write(self, file_path: str, content: str) -> WriteResult
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult
    def grep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult
    def glob(self, pattern: str, path: str = "/") -> GlobResult
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]

class SandboxBackendProtocol(BackendProtocol):
    @property
    def id(self) -> str
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse
```

---

## 5. 子代理系统 (Sub-agents)

### 5.1 三种子代理类型

**文件**: `libs/deepagents/deepagents/middleware/subagents.py`

```python
# 1. SubAgent - 声明式同步子代理
class SubAgent(TypedDict):
    name: str
    description: str
    system_prompt: str
    tools: NotRequired[Sequence[BaseTool | Callable | dict[str, Any]]]
    model: NotRequired[str | BaseChatModel]
    middleware: NotRequired[list[AgentMiddleware]]
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]
    skills: NotRequired[list[str]]
    permissions: NotRequired[list[FilesystemPermission]]
    response_format: NotRequired[ResponseFormat[Any] | type | dict[str, Any]]

# 2. CompiledSubAgent - 预编译子代理
class CompiledSubAgent(TypedDict):
    name: str
    description: str
    runnable: Runnable  # 预编译的 LangGraph

# 3. AsyncSubAgent - 异步/远程子代理
class AsyncSubAgent(TypedDict):
    name: str
    description: str
    graph_id: str
    url: NotRequired[str]
    headers: NotRequired[dict[str, str]]
```

### 5.2 默认通用子代理

**文件**: `libs/deepagents/deepagents/middleware/subagents.py:350`

```python
GENERAL_PURPOSE_SUBAGENT: SubAgent = {
    "name": "general-purpose",
    "description": "General-purpose agent for researching complex questions...",
    "system_prompt": "In order to complete the objective...",
}
```

### 5.3 Task 工具

**文件**: `libs/deepagents/deepagents/middleware/subagents.py:386`

```python
def _build_task_tool(subagents: list[_SubagentSpec], task_description: str | None = None) -> BaseTool:
    """创建 task 工具，支持同步和异步调用"""
    
    def task(description: str, subagent_type: str, runtime: ToolRuntime) -> str | Command:
        # 1. 查找子代理
        # 2. 准备状态 (排除 _EXCLUDED_STATE_KEYS)
        # 3. 构建配置 (转发 callbacks, tags, configurable)
        # 4. 调用子代理
        # 5. 返回 Command 更新主代理状态
```

---

## 6. CLI 设计

### 6.1 架构概览

**文件**: `libs/cli/deepagents_cli/app.py`

```
┌─────────────────────────────────────────┐
│           DeepAgents CLI App            │
│         (Textual TUI Framework)         │
├─────────────────────────────────────────┤
│  UI Layer:                              │
│  ├── ChatInput        # 用户输入        │
│  ├── MessageStore     # 消息存储        │
│  ├── StatusBar        # 状态栏          │
│  └── WelcomeBanner    # 欢迎界面        │
├─────────────────────────────────────────┤
│  Agent Layer:                           │
│  ├── AgentManager     # 代理管理        │
│  ├── create_deep_agent # SDK 调用       │
│  └── SubAgentManager  # 子代理管理      │
├─────────────────────────────────────────┤
│  Integration Layer:                     │
│  ├── MCP Tools        # MCP 集成        │
│  ├── Sandbox Factory  # 沙箱工厂        │
│  └── Memory/Skills    # 记忆和技能      │
└─────────────────────────────────────────┘
```

### 6.2 关键模块

| 模块 | 文件 | 功能 |
|------|------|------|
| App | `app.py` | Textual 应用主类，事件循环 |
| Agent | `agent.py` | 代理创建和管理，ShellAllowListMiddleware |
| Server | `server.py` | LangGraph 服务器模式 |
| Config | `config.py` | 配置管理 |
| Input | `input.py` | 输入处理 |
| Theme | `theme.py` | UI 主题 |
| MCP | `mcp_commands.py`, `mcp_tools.py` | MCP 集成 |

### 6.3 Slash Commands

CLI 支持多种 slash 命令（通过 Textual 实现）：
- `/model` - 选择模型
- `/compact` - 压缩对话
- `/clear` - 清空对话
- `/help` - 显示帮助

---

## 7. ACP (Agent Context Protocol)

### 7.1 设计目的

ACP 是 Deep Agents 与外部客户端通信的标准协议，允许：
- 标准化的代理会话管理
- 工具调用和审批流程
- 多模态内容传输
- MCP 服务器集成

### 7.2 核心组件

**文件**: `libs/acp/deepagents_acp/server.py:92`

```python
class AgentServerACP(ACPAgent):
    """ACP 代理服务器，桥接 Deep Agents 与 ACP 协议"""
    
    def __init__(
        self,
        agent: CompiledStateGraph | Callable[[AgentSessionContext], CompiledStateGraph],
        *,
        # ... 配置参数
    ):
        # 初始化 ACP 会话、工具、MCP 服务器
```

### 7.3 ACP 功能

- **会话管理**: 创建、配置、切换会话模式
- **工具调用**: 标准化工具调用和响应格式
- **审批流程**: 危险操作的权限控制
- **MCP 集成**: 连接外部 MCP 服务器
- **多模态**: 支持文本、图像、音频内容块

---

## 8. Evals 评估框架

### 8.1 架构

**文件**: `libs/evals/deepagents_evals/cli.py`

```
┌─────────────────────────────────────────┐
│        DeepAgents Evals CLI             │
├─────────────────────────────────────────┤
│  Commands:                              │
│  ├── run           # 单次评估运行       │
│  ├── trials        # N 次运行聚合       │
│  ├── aggregate     # 聚合历史报告       │
│  ├── radar         # 生成雷达图         │
│  ├── catalog       # 管理评估目录       │
│  └── list          # 发现评估项         │
├─────────────────────────────────────────┤
│  Harbor Integration:                    │
│  ├── deepagents_harbor/backend.py       │
│  ├── deepagents_harbor/langsmith.py     │
│  └── deepagents_harbor/deepagents_wrapper.py │
└─────────────────────────────────────────┘
```

### 8.2 评估类别

**文件**: `libs/evals/deepagents_evals/categories.json`

评估按类别组织：
- 文件操作 (file_operations)
- 工具使用 (tool_usage)
- 记忆多轮 (memory_multiturn)
- 跟进质量 (followup_quality)
- 外部基准 (external_benchmarks)

### 8.3 Harbor 运行时

**文件**: `libs/evals/deepagents_harbor/backend.py`

- 使用 Harbor 框架运行评估
- 支持 Docker 容器隔离
- 与 LangSmith 集成进行追踪

---

## 9. 上下文管理

### 9.1 自动摘要 (Auto-summarization)

**文件**: `libs/deepagents/deepagents/middleware/summarization.py`

```python
class _DeepAgentsSummarizationMiddleware(AgentMiddleware):
    """自动摘要中间件，当 token 使用超过阈值时压缩对话"""
    
    # 触发条件: 模型配置文件的 85% max_input_tokens
    # 保留策略: 最近 10% 的上下文
    # 历史卸载: 保存到 /conversation_history/{thread_id}.md
```

### 9.2 大输出保存到文件

**文件**: `libs/deepagents/deepagents/middleware/filesystem.py:1806`

```python
def _process_large_message(
    self,
    message: ToolMessage,
    resolved_backend: BackendProtocol,
) -> tuple[ToolMessage, bool]:
    """处理大 ToolMessage，将内容卸载到文件系统"""
    
    # 1. 检查内容是否超过阈值 (默认 20000 tokens)
    # 2. 写入后端: /large_tool_results/{tool_call_id}
    # 3. 创建预览 (head + tail)
    # 4. 返回截断消息，包含文件路径引用
```

### 9.3 HumanMessage 卸载

**文件**: `libs/deepagents/deepagents/middleware/filesystem.py:1944`

```python
def _evict_and_truncate_messages(
    self,
    request: ModelRequest[ContextT],
) -> tuple[list[AnyMessage], Command | None] | None:
    """将超大 HumanMessage 卸载到文件系统"""
    
    # 1. 检查最新消息是否超过阈值 (默认 50000 tokens)
    # 2. 写入后端: /conversation_history/{uuid}.md
    # 3. 标记消息: additional_kwargs["lc_evicted_to"] = file_path
    # 4. 返回截断消息列表
```

### 9.4 记忆系统

**文件**: `libs/deepagents/deepagents/middleware/memory.py:161`

```python
class MemoryMiddleware(AgentMiddleware):
    """从 AGENTS.md 文件加载记忆到系统提示词"""
    
    # 1. 从配置的路径加载 AGENTS.md 文件
    # 2. 注入到系统提示词的 <agent_memory> 标签中
    # 3. 支持 Anthropic 提示缓存 (cache_control)
    # 4. 提供记忆更新指导
```

---

## 10. 关键设计模式

### 10.1 中间件模式

所有功能通过 `AgentMiddleware` 实现：

```python
class AgentMiddleware(Generic[StateT, ContextT, ResponseT]):
    # 可选实现的方法:
    def before_agent(self, state, runtime, config) -> StateUpdate | None
    def wrap_model_call(self, request, handler) -> ModelResponse
    def wrap_tool_call(self, request, handler) -> ToolMessage | Command
    # 以及对应的 async 版本
```

### 10.2 状态管理

- 使用 LangGraph 的 `DeltaChannel` 优化状态更新
- 自定义 reducer 处理文件数据的增删改
- 私有状态属性 (`PrivateStateAttr`) 隔离内部状态

### 10.3 提示词组装

系统提示词按顺序组装：
```
USER (调用者传入)
→ BASE (SDK 默认) 或 CUSTOM (HarnessProfile 覆盖)
→ SUFFIX (HarnessProfile 后缀)
→ 中间件注入的提示词 (文件系统、子代理、摘要等)
```

### 10.4 HarnessProfile

**文件**: `libs/deepagents/deepagents/profiles/`

- 按模型提供商/型号定义配置
- 支持排除中间件和工具
- 支持自定义提示词和工具描述
- 支持额外中间件注入

---

## 11. 关键文件索引

| 组件 | 文件路径 | 说明 |
|------|----------|------|
| 主入口 | `libs/deepagents/deepagents/__init__.py` | 公开 API |
| 图构建 | `libs/deepagents/deepagents/graph.py` | create_deep_agent |
| 文件系统中间件 | `libs/deepagents/deepagents/middleware/filesystem.py` | 文件工具 |
| 子代理中间件 | `libs/deepagents/deepagents/middleware/subagents.py` | task 工具 |
| 摘要中间件 | `libs/deepagents/deepagents/middleware/summarization.py` | 自动摘要 |
| 记忆中间件 | `libs/deepagents/deepagents/middleware/memory.py` | AGENTS.md |
| 后端协议 | `libs/deepagents/deepagents/backends/protocol.py` | 接口定义 |
| 状态后端 | `libs/deepagents/deepagents/backends/state.py` | StateBackend |
| 文件系统后端 | `libs/deepagents/deepagents/backends/filesystem.py` | FilesystemBackend |
| 沙箱基类 | `libs/deepagents/deepagents/backends/sandbox.py` | BaseSandbox |
| CLI 应用 | `libs/cli/deepagents_cli/app.py` | Textual TUI |
| CLI Agent | `libs/cli/deepagents_cli/agent.py` | 代理管理 |
| ACP 服务器 | `libs/acp/deepagents_acp/server.py` | ACP 桥接 |
| Evals CLI | `libs/evals/deepagents_evals/cli.py` | 评估命令 |
