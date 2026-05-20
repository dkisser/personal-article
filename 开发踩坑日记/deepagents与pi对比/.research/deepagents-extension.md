# Deep Agents 扩展设计深度分析

## 概述

Deep Agents 是一个基于 LangChain/LangGraph 构建的 AI Agent SDK，采用**分层扩展架构**：核心 SDK (`libs/deepagents`) 提供扩展点，CLI (`libs/cli`)、ACP (`libs/acp`)、Partner 包 (`libs/partners`) 作为扩展实现。其扩展哲学是**"约定优于配置，协议驱动集成"**——通过定义清晰的协议（Protocol）和注册机制，让外部扩展能够无缝接入核心框架。

---

## 1. 工具系统扩展

### 1.1 自定义工具

**扩展点**：`create_deep_agent(tools=[...])`

Deep Agents 接受任何 LangChain `BaseTool` 子类或符合 `StructuredTool` 规范的 callable。工具通过标准 LangChain 工具协议集成：

```python
# libs/deepagents/deepagents/graph.py
from langchain_core.tools import BaseTool
# tools 参数类型: Sequence[BaseTool | Callable | dict[str, Any]]
```

**关键设计**：
- 工具描述覆盖：通过 `HarnessProfile.tool_description_overrides` 可在不修改工具源码的情况下覆盖工具描述
- 工具排除：通过 `HarnessProfile.excluded_tools` 可按名称排除特定工具
- 动态工具过滤：`FilesystemMiddleware` 根据 backend 能力动态过滤 `execute` 工具（`deepagents/middleware/filesystem.py:2152` 附近）

### 1.2 MCP (Model Context Protocol) 支持

**扩展点**：`MCPClient` + 信任存储机制

```python
# libs/cli/deepagents_cli/mcp_commands.py
# MCP 配置发现与合并
discover_mcp_configs() -> list[Path]  # 自动发现用户级和项目级配置
classify_discovered_configs() -> tuple[list[Path], list[Path]]  # 分类用户/项目配置
merge_mcp_configs(configs) -> dict  # 按优先级合并
```

**安全扩展设计**：
- **信任门控（Trust Gating）**：项目级 MCP 配置需通过指纹验证才能加载，防止克隆的恶意仓库窃取本地密钥
- **OAuth 登录流**：`run_mcp_login()` 处理 MCP 服务器的 OAuth 认证，支持自动发现和显式配置路径
- **配置验证**：`_validate_server_config()` 在加载时验证配置形状，防止路径遍历攻击

### 1.3 Partner 包工具扩展模式

Partner 包通过实现 `BackendProtocol` 或 `SandboxBackendProtocol` 来扩展工具能力：

| Partner | 扩展方式 | 核心类 |
|---------|---------|--------|
| `langchain-quickjs` | Middleware + REPL 工具 | `CodeInterpreterMiddleware` |
| `langchain-modal` | SandboxBackend 实现 | `ModalSandbox` |
| `langchain-daytona` | SandboxBackend 实现 | `DaytonaSandbox` |
| `langchain-runloop` | SandboxBackend 实现 | `RunloopSandbox` |

---

## 2. 模型/Provider 扩展

### 2.1 双层 Profile 系统

Deep Agents 采用** ProviderProfile + HarnessProfile **的双层架构分离模型构造和运行时行为：

```python
# libs/deepagents/deepagents/profiles/provider/provider_profiles.py
@dataclass(frozen=True)
class ProviderProfile:
    init_kwargs: Mapping[str, Any]           # 静态构造参数
    pre_init: Callable[[str], None] | None   # 初始化前副作用
    init_kwargs_factory: Callable[[], dict] | None  # 动态参数工厂
```

**扩展方式**：
```python
from deepagents import ProviderProfile, register_provider_profile

# 1. 为整个 provider 注册默认配置
register_provider_profile("openai", ProviderProfile(
    init_kwargs={"temperature": 0}
))

# 2. 为特定模型注册覆盖配置
register_provider_profile("openai:gpt-5.4", ProviderProfile(
    init_kwargs={"max_tokens": 4096}
))
```

**合并语义**：
- 注册是**累加**的：新 profile 合并到现有注册之上
- `init_kwargs` 按 key 合并，新值覆盖旧值
- `pre_init` 和 `init_kwargs_factory` **链式执行**（先 base 后 override）
- 解析顺序：精确匹配 `provider:model` -> provider 前缀 -> None

### 2.2 HarnessProfile（运行时行为配置）

```python
# libs/deepagents/deepagents/profiles/harness/harness_profiles.py
@dataclass(frozen=True)
class HarnessProfile:
    base_system_prompt: str | None           # 替换 BASE_AGENT_PROMPT
    system_prompt_suffix: str | None         # 追加到系统提示末尾
    tool_description_overrides: dict[str, str]  # 工具描述覆盖
    excluded_tools: set[str]                 # 排除的工具名称
    excluded_middleware: set[str | type]     # 排除的中间件
    extra_middleware: list[AgentMiddleware]  # 额外中间件
    general_purpose_subagent: GeneralPurposeSubagentProfile  # 默认子代理配置
```

**注册方式**：
```python
from deepagents import HarnessProfile, register_harness_profile

register_harness_profile("anthropic:claude-sonnet-4-6", HarnessProfile(
    system_prompt_suffix="You are running in a testing environment...",
    excluded_tools={"execute"}
))
```

### 2.3 init_chat_model 桥接

`resolve_model()` 函数（`deepagents/_models.py`）桥接字符串 spec 到 `BaseChatModel`：

```python
def resolve_model(model: str | BaseChatModel) -> BaseChatModel:
    if isinstance(model, BaseChatModel):
        return model
    # 解析 "provider:model-name" 格式
    provider, model_name = model.split(":", 1)
    kwargs = apply_provider_profile(model)  # 注入 provider 特定配置
    return init_chat_model(model_name, model_provider=provider, **kwargs)
```

**扩展点**：任何 LangChain 支持的 provider 自动可用，通过 `ProviderProfile` 可微调构造行为。

---

## 3. LangGraph 扩展性

### 3.1 Checkpointer

**扩展点**：`create_deep_agent(checkpointer=...)`

直接接受任何 LangGraph `Checkpointer` 实现：
- `MemorySaver`：内存中的 checkpoint（开发/测试）
- `PostgresCheckpoint`：持久化到 PostgreSQL
- `RedisCheckpoint`：持久化到 Redis
- 自定义实现：实现 `Checkpointer` 抽象基类

### 3.2 Store

**扩展点**：`create_deep_agent(store=...)`

LangGraph `BaseStore` 实现用于跨会话状态存储：
```python
from langgraph.store.base import BaseStore

class MyCustomStore(BaseStore):
    async def aget(self, namespace, key): ...
    async def aput(self, namespace, key, value): ...
    async def asearch(self, namespace, query): ...
```

### 3.3 Streaming

Deep Agents 继承 LangGraph 的流式架构：
- **Token 流**：通过 `agent.astream()` 获取实时 token
- **事件流**：通过 `agent.astream_events()` 获取结构化事件（工具调用开始/结束等）
- **自定义流处理器**：在 middleware 的 `wrap_model_call` 中拦截和转换流

### 3.4 DeltaChannel（性能优化扩展点）

```python
# libs/deepagents/deepagents/graph.py:63-66
class _DeepAgentState(AgentState):
    messages: Required[Annotated[list[AnyMessage], 
        DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]]
```

`DeltaChannel` 将 checkpoint 增长从 O(N²) 降至 O(N)，是 LangGraph 的扩展机制在 Deep Agents 中的关键应用。

### 3.5 图自定义

虽然 `create_deep_agent` 是高层工厂，但可通过以下方式自定义底层图：
1. **Middleware 堆栈**：每个 middleware 可修改请求/响应、注入工具、修改状态
2. **CompiledSubAgent**：传入预编译的 `CompiledStateGraph` 作为子代理
3. **直接构建**：绕过 `create_deep_agent`，使用 `langchain.agents.create_agent()` + 手动 middleware 堆栈

---

## 4. 子代理扩展

### 4.1 三种子代理类型

```python
# libs/deepagents/deepagents/middleware/subagents.py

class SubAgent(TypedDict):
    """声明式子代理规范"""
    name: str
    description: str
    system_prompt: str
    tools: NotRequired[Sequence[BaseTool]]
    model: NotRequired[str | BaseChatModel]
    middleware: NotRequired[list[AgentMiddleware]]
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]
    skills: NotRequired[list[str]]
    permissions: NotRequired[list[FilesystemPermission]]
    response_format: NotRequired[ResponseFormat]

class CompiledSubAgent(TypedDict):
    """预编译子代理"""
    name: str
    description: str
    runnable: Runnable  # 预构建的 CompiledStateGraph
```

**扩展方式**：
```python
# 1. 声明式子代理
subagent = SubAgent(
    name="code-reviewer",
    description="Review code for bugs and style issues",
    system_prompt="You are a senior code reviewer...",
    tools=[my_custom_tool],
    model="openai:gpt-4o"
)

# 2. 预编译子代理（完全自定义图）
from langgraph.graph import StateGraph
graph = StateGraph(MyState).add_node(...).compile()
compiled = CompiledSubAgent(
    name="custom-analyzer",
    description="Custom analysis pipeline",
    runnable=graph
)

agent = create_deep_agent(subagents=[subagent, compiled])
```

### 4.2 Task 工具设计

`SubAgentMiddleware` 自动构建 `task` 工具：

```python
# _build_task_tool() 生成 StructuredTool
# - 输入 schema: TaskToolSchema(description, subagent_type)
# - 支持并行调用：多个 task 可在同一轮中并行执行
# - 状态隔离：子代理只接收过滤后的状态（排除 _EXCLUDED_STATE_KEYS）
# - 追踪上下文：自动标记 ls_agent_type="subagent"
```

**关键扩展点**：
- `task_description` 参数可自定义 task 工具描述
- `{available_agents}` 占位符自动替换为可用代理列表
- 子代理配置继承 + 覆盖机制

### 4.3 AsyncSubAgent（远程部署）

```python
# libs/deepagents/deepagents/middleware/async_subagents.py
class AsyncSubAgent(TypedDict):
    name: str
    description: str
    url: str  # 远程 agent 端点
    headers: NotRequired[dict[str, str]]
```

用于将任务委托给远程 LangSmith 部署或其他 HTTP 服务。

---

## 5. CLI 扩展

### 5.1 Slash 命令扩展

CLI 基于 Textual 构建，slash 命令通过 argparse 子解析器注册：

```python
# libs/cli/deepagents_cli/skills/commands.py
def setup_skills_parser(subparsers, *, make_help_action, add_output_args):
    skills_parser = subparsers.add_parser("skills", help="Manage agent skills")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command")
    
    # 子命令: list, create, info, delete
    list_parser = skills_subparsers.add_parser("list", ...)
    create_parser = skills_subparsers.add_parser("create", ...)
    ...
```

**扩展模式**：
1. 创建新的命令模块（如 `my_commands.py`）
2. 实现 `setup_*_parser()` 和 `execute_*_command()` 函数
3. 在 `main.py` 中注册到主解析器

### 5.2 Skill 系统扩展

Skills 是 CLI 的核心扩展机制，采用 **Agent Skills 规范**：

```
skill-directory/
├── SKILL.md          # YAML frontmatter + Markdown 指令
├── helper.py         # 可选：支持文件
└── ...
```

**SKILL.md 格式**：
```markdown
---
name: web-research
description: Structured approach to web research
license: MIT
compatibility: Deep Agents CLI
allowed-tools: Bash(git:*) Read
metadata:
  author: my-org
  version: "1.0"
---

# Web Research Skill

## When to Use
- User asks for research on a topic
...
```

**加载优先级**（后加载覆盖先加载）：
1. `~/.agents/skills/` — 用户级
2. `~/.deepagents/<agent>/skills/` — 用户级（别名）
3. `.agents/skills/` — 项目级
4. `.deepagents/skills/` — 项目级（别名）
5. `<package>/built_in_skills/` — 内置

**Skill 作为代码扩展**（QuickJS 集成）：
```python
# langchain_quickjs/_skills.py
# Skill 可声明 module 入口点，在 REPL 中通过 await import("@/skills/<name>") 加载
```

### 5.3 自定义工具（CLI 层）

```python
# libs/cli/deepagents_cli/tools.py
@tool
def web_search(query: str) -> str:
    """Search the web using Tavily."""
    ...

@tool  
def fetch_url(url: str) -> str:
    """Fetch and convert a URL to markdown."""
    ...
```

CLI 自动将这些工具注入到 agent 的工具列表中。

---

## 6. ACP (Agent Context Protocol) 扩展

### 6.1 ACP 服务器实现

```python
# libs/acp/deepagents_acp/server.py
class AgentServerACP(ACPAgent):
    """ACP 协议桥接，将 Deep Agents 暴露为 ACP 服务"""
    
    def __init__(self, agent_factory: Callable[..., Runnable], ...):
        # agent_factory 在每次会话时创建新的 agent 实例
        
    async def handle_prompt(self, prompt: str, ...):
        # 处理流式提示，支持工具调用分块
        
    def set_config_option(self, key: str, value: Any):
        # 运行时切换模型、会话模式等
```

**扩展点**：
- `agent_factory`：自定义 agent 创建逻辑
- 会话模式：支持 `interactive`、`batch`、`streaming`
- 权限处理：`approve_always` 按命令类型自动批准

### 6.2 与 SDK 的集成

ACP 包依赖 SDK 的核心功能但独立发布：
- `deepagents-acp` 包依赖 `deepagents`
- 通过工厂模式解耦，ACP 不直接依赖具体的 agent 实现

---

## 7. Partner 包扩展模式

Partner 包是 Deep Agents 扩展架构的最佳实践示例，遵循**"独立包 + 协议实现"**模式：

### 7.1 Sandbox Backend 扩展

所有 sandbox partner 包实现 `SandboxBackendProtocol`：

```python
# 协议定义（SDK 中）
class SandboxBackendProtocol(BackendProtocol):
    @property
    def id(self) -> str: ...
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse: ...

# Partner 实现示例（Modal）
class ModalSandbox(BaseSandbox):
    def __init__(self, *, sandbox: modal.Sandbox): ...
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse: ...
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]: ...
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]: ...
```

**关键设计**：
- `BaseSandbox` 提供基于 `execute()` 的默认文件操作实现（ls、read、write、edit、grep、glob）
- Partner 只需实现 `execute()`、`upload_files()`、`download_files()` 和 `id` 属性
- 文件操作通过 server-side Python 脚本执行，避免大文件传输

### 7.2 Middleware 扩展（QuickJS）

`CodeInterpreterMiddleware` 是 partner 包扩展 middleware 的范例：

```python
# libs/partners/quickjs/langchain_quickjs/middleware.py
@beta()
class CodeInterpreterMiddleware(AgentMiddleware[REPLState, ContextT, ResponseT]):
    state_schema = REPLState  # 自定义状态模式
    
    def __init__(self, *, memory_limit=64*1024*1024, timeout=5.0, 
                 ptc=None, skills_backend=None, ...):
        # 配置 REPL 参数
        
    def wrap_model_call(self, request, handler):
        # 注入 REPL 系统提示和 PTC 绑定
        
    def before_agent(self, state, runtime):
        # 从快照恢复 REPL 状态
        
    def after_agent(self, state, runtime):
        # 创建快照并清理 REPL 实例
```

**扩展特性**：
- **PTC (Programmatic Tool Calling)**：在 REPL 中通过 `tools.<name>()` 调用 agent 工具
- **Skill 模块加载**：支持 `await import("@/skills/<name>")` 加载 skill 代码
- **快照持久化**：跨 turn 保持 REPL 状态

### 7.3 Partner 包注册（CLI 集成）

```python
# libs/cli/deepagents_cli/integrations/sandbox_factory.py
_PROVIDER_TO_WORKING_DIR = {
    "agentcore": "/tmp",
    "daytona": "/home/daytona",
    "langsmith": "/tmp",
    "modal": "/workspace",
    "runloop": "/home/user",
}

def _get_provider(provider_name: str) -> SandboxProvider:
    if provider_name == "modal":
        return _ModalProvider()
    if provider_name == "daytona":
        return _DaytonaProvider()
    ...
```

Partner 包通过**可选依赖**集成：
```bash
pip install 'deepagents-cli[modal]'    # 安装 modal 支持
pip install 'deepagents-cli[daytona]'  # 安装 daytona 支持
```

---

## 8. Prompt 定制扩展

### 8.1 四层提示组装

```python
# libs/deepagents/deepagents/graph.py:69-141
# 最终系统提示 = USER -> (BASE 或 CUSTOM) -> SUFFIX

# USER: create_deep_agent(system_prompt=...) 参数
# BASE: BASE_AGENT_PROMPT 常量（默认行为指令）
# CUSTOM: HarnessProfile.base_system_prompt（替换 BASE）
# SUFFIX: HarnessProfile.system_prompt_suffix（追加）
```

**扩展方式**：
```python
# 方式 1：直接传入 system_prompt
agent = create_deep_agent(system_prompt="You are a specialized data analyst...")

# 方式 2：通过 HarnessProfile 全局覆盖
register_harness_profile("openai", HarnessProfile(
    base_system_prompt="Custom base prompt...",
    system_prompt_suffix="Additional guidance..."
))

# 方式 3：针对特定模型
register_harness_profile("anthropic:claude-sonnet-4-6", HarnessProfile(
    system_prompt_suffix="Remember to use XML tags..."
))
```

### 8.2 Memory 注入

```python
# libs/deepagents/deepagents/middleware/memory.py
class MemoryMiddleware(AgentMiddleware):
    """从 AGENTS.md 文件加载记忆到系统提示"""
    
    def modify_request(self, request):
        # 将 memory_contents 格式化为 <agent_memory> 块注入系统提示
        agent_memory = self._format_agent_memory(contents)
        new_system_message = append_to_system_message(request.system_message, agent_memory)
```

**AGENTS.md 格式**：标准 Markdown，无强制结构，常见段落包括项目概述、构建命令、代码风格、架构笔记。

### 8.3 Skill 提示注入

```python
# libs/deepagents/deepagents/middleware/skills.py
class SkillsMiddleware(AgentMiddleware):
    """从 SKILL.md 文件加载技能到系统提示"""
    
    def modify_request(self, request):
        # 按来源分组技能，格式化为 Markdown 列表注入
        # 支持渐进式披露：只在需要时加载技能详情
```

---

## 9. 配置扩展

### 9.1 环境变量配置

```python
# libs/cli/deepagents_cli/config.py
class Settings:
    """从环境变量加载配置"""
    
    @classmethod
    def from_environment(cls) -> Settings:
        # 检测 API keys、项目根目录、shell 白名单等
        
    def get_default_model_spec(self) -> str:
        # 基于可用凭证的降级链：
        # ANTHROPIC_API_KEY -> OPENAI_API_KEY -> OPENROUTER_API_KEY -> ...
```

**配置优先级**：
1. 显式代码参数（最高优先级）
2. 环境变量（`DEEPAGENTS_CLI_` 前缀优先）
3. 配置文件（`~/.deepagents/config.yaml`）
4. 默认值

### 9.2 HarnessProfileConfig（YAML/JSON 配置）

```python
# libs/deepagents/deepagents/profiles/harness/harness_profiles.py
@dataclass(frozen=True)
class HarnessProfileConfig:
    """声明式 harness profile 配置，支持 YAML/JSON 序列化"""
    base_system_prompt: str | None
    system_prompt_suffix: str | None
    tool_description_overrides: dict[str, str] | None
    excluded_tools: list[str] | None
    excluded_middleware: list[str] | None
    extra_middleware: list[dict] | None  # 通过类路径实例化
    general_purpose_subagent: dict | None
```

### 9.3 ProviderProfile 动态配置

```python
# 通过 init_kwargs_factory 实现运行时配置
ProviderProfile(
    init_kwargs={"temperature": 0},
    init_kwargs_factory=lambda: {
        "base_url": os.environ.get("CUSTOM_BASE_URL"),
        "api_key": os.environ.get("CUSTOM_API_KEY")
    }
)
```

---

## 10. Backend 协议扩展

### 10.1 BackendProtocol

```python
# libs/deepagents/deepagents/backends/protocol.py
class BackendProtocol(abc.ABC):
    def ls(self, path: str) -> LsResult: ...
    def read(self, file_path: str, offset=0, limit=2000) -> ReadResult: ...
    def grep(self, pattern: str, path=None, glob=None) -> GrepResult: ...
    def glob(self, pattern: str, path="/") -> GlobResult: ...
    def write(self, file_path: str, content: str) -> WriteResult: ...
    def edit(self, file_path: str, old_string: str, new_string: str) -> EditResult: ...
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]: ...
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]: ...
```

**内置实现**：
- `FilesystemBackend`：本地文件系统
- `StateBackend`：内存/状态存储（ephemeral）

**扩展方式**：实现 `BackendProtocol` 或 `SandboxBackendProtocol`。

### 10.2 BackendFactory 模式

```python
BackendFactory = Callable[[ToolRuntime], BackendProtocol]
BACKEND_TYPES = BackendProtocol | BackendFactory
```

支持传入工厂函数，在运行时根据 tool runtime 状态创建 backend（用于 `StateBackend` 等需要运行时上下文的场景）。

---

## 11. Middleware 扩展架构

### 11.1 AgentMiddleware 接口

```python
# 来自 langchain.agents.middleware.types
class AgentMiddleware(ABC, Generic[StateT, ContextT, ResponseT]):
    state_schema: type[AgentState] | None = None
    tools: list[BaseTool] = []
    
    def before_agent(self, state, runtime, config) -> dict | None: ...
    def abefore_agent(self, state, runtime, config) -> Awaitable[dict | None]: ...
    
    def after_agent(self, state, runtime) -> dict | None: ...
    def aafter_agent(self, state, runtime) -> Awaitable[dict | None]: ...
    
    def wrap_model_call(self, request, handler) -> ModelResponse: ...
    def awrap_model_call(self, request, handler) -> Awaitable[ModelResponse]: ...
    
    def wrap_tool_call(self, runtime, handler): ...
    def awrap_tool_call(self, runtime, handler): ...
    
    def modify_request(self, request) -> ModelRequest: ...
```

### 11.2 内置 Middleware 堆栈

| Middleware | 职责 | 是否可排除 |
|-----------|------|----------|
| `FilesystemMiddleware` | 文件工具 + 权限控制 | **否**（必需脚手架） |
| `SubAgentMiddleware` | task 工具 + 子代理调度 | **否**（必需脚手架） |
| `SkillsMiddleware` | Skill 加载和注入 | 是 |
| `MemoryMiddleware` | AGENTS.md 记忆加载 | 是 |
| `HumanInTheLoopMiddleware` | HITL 中断 | 是 |
| `TodoListMiddleware` | 待办事项管理 | 是 |
| `SummarizationMiddleware` | 消息摘要 | 是 |
| `AnthropicPromptCachingMiddleware` | Anthropic 提示缓存 | 是 |
| `PatchToolCallsMiddleware` | 工具调用补丁 | 是 |
| `CodeInterpreterMiddleware` | QuickJS REPL（Partner） | 是 |

### 11.3 自定义 Middleware 示例

```python
class LoggingMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        print(f"Model call: {request.model}")
        response = handler(request)
        print(f"Response tokens: {len(response.messages)}")
        return response
    
    def before_agent(self, state, runtime, config):
        print(f"Agent turn started: {runtime.config['configurable'].get('thread_id')}")
        return None

agent = create_deep_agent(middleware=[LoggingMiddleware()])
```

---

## 12. 扩展设计总结

### 12.1 核心扩展机制矩阵

| 扩展目标 | 机制 | 复杂度 | 文件位置 |
|---------|------|--------|---------|
| 自定义工具 | `BaseTool` + `tools` 参数 | 低 | 用户代码 |
| MCP 服务器 | 配置文件 + OAuth | 中 | `~/.mcp.json`, `.mcp.json` |
| 新模型 Provider | `ProviderProfile` 注册 | 低 | 用户代码 / 配置 |
| 提示定制 | `HarnessProfile` + `system_prompt` | 低 | 用户代码 / 配置 |
| 新 Backend | 实现 `BackendProtocol` | 中 | Partner 包 |
| 新 Sandbox | 实现 `SandboxBackendProtocol` | 中 | Partner 包 |
| 自定义 Middleware | 继承 `AgentMiddleware` | 中 | 用户代码 / Partner 包 |
| 子代理 | `SubAgent` / `CompiledSubAgent` | 中 | 用户代码 |
| Skill | `SKILL.md` + 目录 | 低 | `~/.agents/skills/` |
| CLI 命令 | Argparse 子解析器 | 中 | CLI 代码 |
| ACP 服务 | 实现 `ACPAgent` | 高 | `libs/acp` |

### 12.2 设计原则

1. **协议优先**：通过 `BackendProtocol`、`SandboxBackendProtocol`、`AgentMiddleware` 等抽象协议定义扩展边界
2. **累加配置**：Profile 注册采用合并而非替换语义，支持分层配置
3. **安全内建**：MCP 信任门控、权限系统、工具排除等安全机制是扩展的一等公民
4. **渐进式披露**：Skills 和记忆采用按需加载，避免提示膨胀
5. **LangGraph 原生**：充分利用 LangGraph 的 checkpointer、store、channel 等扩展机制
6. **Partner 包模式**：独立包 + 可选依赖 + 协议实现，保持核心轻量

### 12.3 与 LangChain 生态的关系

Deep Agents 的扩展设计深度依赖 LangChain 生态：
- **模型**：通过 `init_chat_model` 桥接所有 LangChain Chat Models
- **工具**：兼容所有 LangChain Tools
- **图**：基于 LangGraph 的 StateGraph 和 checkpoint 机制
- **追踪**：通过 LangSmith 进行运行追踪和监控
- **Middleware**：继承自 `langchain.agents.middleware`

这种设计使得 Deep Agents 的扩展边界与 LangChain 生态完全对齐——任何 LangChain 扩展自动成为 Deep Agents 扩展。
