# 设计文档 —— article-publish 图片本地化集成

**日期**: 2026-05-29
**主题**: article-publish skill 的图片自动下载与链接替换
**状态**: 已批准

---

## 1. 背景与目标

当前 vault 中的文章图片全部托管在外部平台（墨问 CDN），URL 形式为 `https://priv-sdn-001.mowen.cn/...`。存在以下问题：

1. **链接失效风险** — CDN 链接带过期签名（`Expires`、`Signature` 参数），过期后图片无法访问
2. **离线不可用** — 没有网络时无法查看文章中的图片
3. **平台绑定** — 图片与墨问强绑定，迁移成本高

**目标**：在 `article-publish` 发布流程中，自动将文章中的外部图片下载到本地 `images/{slug}/` 目录，并将 Markdown 中的链接替换为相对路径 `![](images/...)`。

---

## 2. 架构设计

### 2.1 目录结构

```
.claude/skills/article-publish/
├── SKILL.md              # 发布流程定义 + 触发器
└── scripts/
    └── download_image.py # 单图下载脚本
```

遵循 [skill-creator 规范](../references/skill-creator.md)，可执行脚本统一放在 `scripts/` 子目录下。

### 2.2 数据流

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────────┐
│  article.md     │────▶│  SKILL.md Step 3.5: │────▶│ scripts/download_image.py│
│ (含外部图片链接) │     │  正则提取所有外部图片  │     │ (逐个下载到本地)         │
└─────────────────┘     │  URL，调用脚本下载   │     └─────────────────────────┘
                        └─────────────────────┘              │
                                   │                         │
                                   ▼                         ▼
                            ┌─────────────┐           ┌─────────────┐
                            │ 替换链接为   │◄──────────│ 返回本地路径 │
                            │ ![](本地路径)│           │ images/...  │
                            └─────────────┘           └─────────────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │ 继续原流程   │
                            │ (catalog...) │
                            └─────────────┘
```

**关键设计决策**：
- `download_image.py` 是纯 CLI 工具，**不解析 Markdown**，只负责单张下载
- Markdown 解析、URL 提取、目录名生成由 SKILL.md 流程定义，Claude 执行

---

## 3. download_image.py 接口设计

### 3.1 调用方式

```bash
python scripts/download_image.py <url> <output_dir>
```

### 3.2 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | string | 图片完整 URL，如 `https://priv-sdn-001.mowen.cn/.../xxx.png?Expires=...` |
| `output_dir` | string | 目标目录，如 `images/dang-ni-yao-xu-yao-mcp-server-shi/` |

### 3.3 行为

1. **创建目录**：若 `output_dir` 不存在则自动创建（`os.makedirs(..., exist_ok=True)`）
2. **下载图片**：
   - `User-Agent`: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...`
   - 超时：连接 10s，读取 30s
   - 重试：3 次指数退避（1s → 2s → 4s）
3. **推断扩展名**：
   - 优先级 1：`Content-Type` header（`image/png` → `.png`）
   - 优先级 2：URL path 最后一段（`/xxx.png?Expires=...` → `.png`）
   - 兜底：`.bin`
4. **生成文件名**：`image-{N}.{ext}`，N 从 1 开始递增，跳过已存在文件
5. **去重检查**：若同名文件已存在且大小与下载内容一致，跳过下载，直接返回路径
6. **输出**：
   - **stdout**：仅输出最终相对路径（如 `images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png`）
   - **stderr**：输出日志（下载中、跳过、错误等）
7. **退出码**：
   - `0` — 成功（新下载或已存在）
   - `1` — 失败（网络错误、非 2xx、无法推断扩展名等）

### 3.4 示例

```bash
$ python scripts/download_image.py \
    "https://priv-sdn-001.mowen.cn/.../2060198638129446914.png?Expires=..." \
    "images/dang-ni-yao-xu-yao-mcp-server-shi"
images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png
```

---

## 4. article-publish 集成流程

在现有 6 步流程中，**在 Step 3 和 Step 4 之间插入 Step 3.5**。

### 4.1 更新后的完整流程

```
Step 1: Identify the article file
Step 2: Read content and generate description
Step 3: Update article frontmatter
Step 3.5: Download images to local ← 新增
Step 4: Update category manager catalog
Step 5: Update master manager README
Step 6: Update public wiki.md
```

### 4.2 Step 3.5 详细步骤

1. **提取文章标题并 slugify**：
   - 从 frontmatter 读取 `title` 字段
   - 若不存在，从文件名提取（去掉 `.md` 后缀）
   - 转小写、去除特殊字符、空格/标点 → `-`

2. **确定输出目录**：`images/<slug>/`

3. **提取外部图片 URL**：
   - 正则：`!\[(.*?)\]\((https?://[^)]+)\)`
   - 只匹配 `http://` 或 `https://` 开头的 URL
   - 保留 alt 文本不变

4. **循环下载**：
   - 对每个 URL 调用：`python scripts/download_image.py <url> <output_dir>`
   - 捕获 stdout（本地路径）
   - 在文章内容中将原 URL 替换为本地相对路径

5. **保存文章**：写回修改后的 Markdown 文件

### 4.3 替换示例

```markdown
# 替换前
![](https://priv-sdn-001.mowen.cn/.../2060198638129446914.png?Expires=...)

# 替换后
![](images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png)
```

---

## 5. 目录名生成规则（slugify）

从文章标题生成合法目录名：

1. 转小写
2. 将空格、标点、特殊字符替换为 `-`
3. 连续多个 `-` 合并为一个
4. 去除开头和结尾的 `-`
5. 限制长度（最大 50 字符）

| 文章标题 | 生成目录名 |
|---------|-----------|
| 「当你要需要MCP Server时，希望你先了解下FastM...」 | `dang-ni-yao-xu-yao-mcp-server-shi` |
| TypeScript全栈踩坑日记-项目搭建 | `typescript-quan-zhan-cai-keng-ri-ji-xiang-mu-da-jian` |
| 「管理TypeScript生态中的Monorepo项目」 | `guan-li-typescript-sheng-tai-zhong-de-monorepo-xiang-mu` |

---

## 6. 错误处理策略

| 场景 | 处理方式 |
|------|---------|
| **单张图片下载失败** | stderr 输出错误，stdout 无输出；article-publish 跳过该图，文章保留原外部 URL；继续处理剩余图片 |
| **所有图片都下载失败** | 继续发布流程，但提示用户"图片下载失败，文章仍使用外部链接" |
| **目录创建失败** | 报错退出（通常是权限问题） |
| **文件已存在** | 跳过下载，直接返回已有路径（基于文件大小判断是否一致） |
| **URL 返回非图片 Content-Type** | 仍保存文件，但按 Content-Type 推断扩展名；stderr 输出警告 |
| **文章无外部图片** | 跳过 Step 3.5，继续原流程 |

---

## 7. 边界情况

1. **重复发布同一篇文章**：第二次发布时，图片已存在于 `images/<slug>/`，`download_image.py` 会检测到并跳过下载，直接返回已有路径，然后 article-publish 将文章中的链接替换为相同路径（幂等）。
2. **文章中混合使用外部图片和本地图片**：正则只匹配 `https?://` 开头的 URL，本地路径（如 `![](images/...)`）不受影响。
3. **URL 中带中文或特殊字符**：`requests` 库自动处理 URL 编码。
4. **图片 URL 在 alt 文本或代码块中**：正则只匹配 Markdown 图片语法 `![]()`，不会误匹配代码块中的 URL。

---

## 8. 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `.claude/skills/article-publish/scripts/download_image.py` | 新增 | 单图下载脚本 |
| `.claude/skills/article-publish/SKILL.md` | 修改 | 在 Step 3 和 Step 4 之间插入 Step 3.5 |

---

## 9. 后续可扩展

- 支持其他图片托管平台（不仅限于墨问 CDN）
- 图片压缩/转 WebP
- 自动生成图片 alt 文本（AI 视觉识别）
- 发布到外部平台时，反向将本地链接替换为图床 URL
