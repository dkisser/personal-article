# article-publish 图片本地化集成 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 article-publish skill 添加外部图片自动下载功能，将文章中的外部图片 URL 替换为本地相对路径。

**Architecture:** 新增纯 CLI 脚本 `scripts/download_image.py` 负责单图下载（重试、扩展名推断、去重），由 SKILL.md 流程定义在 Step 3.5 调用。脚本与 Markdown 解析解耦，保持单一职责。

**Tech Stack:** Python 3.10+, `requests`, `pytest`, `responses` (for testing)

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `.claude/skills/article-publish/scripts/download_image.py` | 创建 | 单图下载 CLI 工具 |
| `.claude/skills/article-publish/SKILL.md` | 修改 | 插入 Step 3.5（图片下载与链接替换） |

---

## Task 1: 创建 `scripts/download_image.py`

**Files:**
- Create: `.claude/skills/article-publish/scripts/download_image.py`
- Create: `.claude/skills/article-publish/scripts/__init__.py` (optional, for Python package)
- Test: `.claude/skills/article-publish/scripts/test_download_image.py`

### 步骤 1: 创建 `scripts/` 目录

```bash
mkdir -p /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/scripts
```

### 步骤 2: 写测试

创建 `.claude/skills/article-publish/scripts/test_download_image.py`：

```python
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.dirname(__file__))
from download_image import infer_extension, generate_filename, download_image


class TestInferExtension:
    def test_from_content_type_png(self):
        assert infer_extension("image/png") == ".png"

    def test_from_content_type_jpeg(self):
        assert infer_extension("image/jpeg") == ".jpg"

    def test_from_content_type_webp(self):
        assert infer_extension("image/webp") == ".webp"

    def test_from_url_path(self):
        assert infer_extension(None, "https://example.com/photo.png") == ".png"

    def test_from_url_path_with_query(self):
        assert infer_extension(None, "https://example.com/photo.jpg?size=large") == ".jpg"

    def test_fallback_bin(self):
        assert infer_extension("application/octet-stream", "https://example.com/file") == ".bin"


class TestGenerateFilename:
    def test_first_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = generate_filename(tmpdir, ".png")
            assert filename == "image-1.png"

    def test_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "image-1.png"), "w").close()
            open(os.path.join(tmpdir, "image-2.png"), "w").close()
            filename = generate_filename(tmpdir, ".png")
            assert filename == "image-3.png"

    def test_different_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "image-1.png"), "w").close()
            filename = generate_filename(tmpdir, ".jpg")
            assert filename == "image-1.jpg"


class TestDownloadImage:
    @patch("download_image.requests.get")
    def test_successful_download(self, mock_get):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"fake image data"
            mock_response.headers = {"Content-Type": "image/png"}
            mock_get.return_value = mock_response

            result = download_image("https://example.com/photo.png", tmpdir)

            assert result == os.path.join(tmpdir, "image-1.png")
            assert os.path.exists(result)
            with open(result, "rb") as f:
                assert f.read() == b"fake image data"

    @patch("download_image.requests.get")
    def test_skip_existing_file(self, mock_get):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_path = os.path.join(tmpdir, "image-1.png")
            with open(existing_path, "wb") as f:
                f.write(b"fake image data")

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"fake image data"
            mock_response.headers = {"Content-Type": "image/png"}
            mock_get.return_value = mock_response

            result = download_image("https://example.com/photo.png", tmpdir)

            assert result == existing_path
            mock_get.assert_called_once()

    @patch("download_image.requests.get")
    def test_network_failure(self, mock_get):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get.side_effect = Exception("Connection timeout")

            with pytest.raises(SystemExit) as exc_info:
                download_image("https://example.com/photo.png", tmpdir)

            assert exc_info.value.code == 1
```

### 步骤 3: 运行测试（预期失败）

```bash
cd /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/scripts
python -m pytest test_download_image.py -v
```

**Expected:** FAIL with `ModuleNotFoundError: No module named 'download_image'` 或 `ImportError`

### 步骤 4: 实现 `download_image.py`

创建 `.claude/skills/article-publish/scripts/download_image.py`：

```python
#!/usr/bin/env python3
"""Download a single image from URL to a local directory."""

import argparse
import os
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)


def create_session():
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def infer_extension(content_type=None, url=None):
    """Infer file extension from Content-Type header or URL path."""
    CONTENT_TYPE_MAP = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
    }

    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct in CONTENT_TYPE_MAP:
            return CONTENT_TYPE_MAP[ct]

    if url:
        from urllib.parse import urlparse
        path = urlparse(url).path
        if path and "." in path:
            ext = os.path.splitext(path)[1].lower()
            if ext:
                return ext

    return ".bin"


def generate_filename(output_dir, extension):
    """Generate sequential filename like image-1.png, skipping existing files."""
    n = 1
    while True:
        filename = f"image-{n}{extension}"
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            return filename
        n += 1


def download_image(url, output_dir):
    """Download image from URL to output_dir. Return full file path."""
    os.makedirs(output_dir, exist_ok=True)

    session = create_session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        print(f"[download] Fetching {url}...", file=sys.stderr)
        response = session.get(url, headers=headers, timeout=(10, 30), stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[error] Failed to download {url}: {e}", file=sys.stderr)
        sys.exit(1)

    content_type = response.headers.get("Content-Type")
    extension = infer_extension(content_type, url)
    filename = generate_filename(output_dir, extension)
    filepath = os.path.join(output_dir, filename)

    # Check if file already exists with same size
    content_length = len(response.content)
    if os.path.exists(filepath) and os.path.getsize(filepath) == content_length:
        print(f"[skip] File already exists: {filepath}", file=sys.stderr)
        return filepath

    with open(filepath, "wb") as f:
        f.write(response.content)

    print(f"[done] Saved to {filepath}", file=sys.stderr)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Download an image from URL.")
    parser.add_argument("url", help="Image URL")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    filepath = download_image(args.url, args.output_dir)
    # stdout only outputs the final relative path
    print(filepath)


if __name__ == "__main__":
    main()
```

### 步骤 5: 运行测试（预期通过）

```bash
cd /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/scripts
python -m pytest test_download_image.py -v
```

**Expected:** All 8 tests PASS

### 步骤 6: 验证 CLI 行为

```bash
cd /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/scripts
chmod +x download_image.py
python download_image.py "https://httpbin.org/image/png" "/tmp/test-images/demo"
```

**Expected:**
- stderr: `[download] Fetching https://httpbin.org/image/png...` → `[done] Saved to /tmp/test-images/demo/image-1.png`
- stdout: `/tmp/test-images/demo/image-1.png`

### 步骤 7: 提交

```bash
cd /Users/wenchen/workspace/personal-article
git add .claude/skills/article-publish/scripts/
git commit -m "feat(article-publish): add download_image.py script

- Download single image from URL with retry and timeout
- Infer extension from Content-Type or URL path
- Sequential naming (image-1.png) with skip-if-exists
- CLI: stdout=path, stderr=logs, exit code 0/1"
```

---

## Task 2: 修改 `SKILL.md` 集成图片下载流程

**Files:**
- Modify: `.claude/skills/article-publish/SKILL.md`

### 步骤 1: 备份现有 SKILL.md

```bash
cp /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/SKILL.md \
   /Users/wenchen/workspace/personal-article/.claude/skills/article-publish/SKILL.md.bak
```

### 步骤 2: 修改 SKILL.md

在 Step 3 和 Step 4 之间插入 Step 3.5，同时在顶部 description 和 workflow 中体现新步骤。

编辑 `.claude/skills/article-publish/SKILL.md`：

**修改 frontmatter description：**

将 description 更新为：
```markdown
---
name: article-publish
description: Publish a finished article by updating its status, generating a description, downloading external images to local storage, replacing image links with relative paths, and syncing the wiki catalog. Use when the user says an article is complete, wants to publish, or finalize an article. Triggers on phrases like "发布", "publish", "写完了", "完成", "finalize", or the slash command /article-publish.
---
```

**在 Step 3 后插入 Step 3.5：**

```markdown
### Step 3.5: Download External Images

Before syncing catalogs, download any external images in the article to local storage:

1. **Extract article title slug:**
   - From frontmatter `title` field, or filename (without `.md`)
   - Slugify: lowercase, replace spaces/special chars with `-`, collapse consecutive `-`, strip leading/trailing `-`, max 50 chars

2. **Determine output directory:** `images/<slug>/`

3. **Find external image URLs:**
   - Use regex: `!\[(.*?)\]\((https?://[^)]+)\)`
   - Only match URLs starting with `http://` or `https://`
   - Preserve alt text unchanged

4. **Download each image:**
   - Call: `python scripts/download_image.py <url> images/<slug>/`
   - Capture stdout (local file path)
   - If exit code is 1 (download failed), skip this image and keep the original external URL
   - In article content, replace the external URL with the local relative path: `![](<local_path>)`

5. **Save the updated article** with replaced image links.

**Example:**
```markdown
# Before
![](https://priv-sdn-001.mowen.cn/.../2060198638129446914.png?Expires=...)

# After
![](images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png)
```
```

**更新 Notes 部分：**

在 Notes 中添加：
```markdown
## Notes

- If the article's `status` is already `published`, warn the user and skip frontmatter/catalog updates, BUT still run Step 3.5 (image download) if there are external images.
- The description is the key output — make it informative and concise.
- After publishing, suggest next steps: share the article, create a follow-up, or start a new one.
- **Image download idempotency:** Running publish multiple times on the same article is safe — existing images are skipped, and links are idempotently replaced.
```

### 步骤 3: 验证 SKILL.md 格式

```bash
cd /Users/wenchen/workspace/personal-article/.claude/skills/article-publish
head -5 SKILL.md
```

**Expected:** YAML frontmatter 格式正确，以 `---` 开头和结尾

```bash
python -c "import yaml; yaml.safe_load(open('SKILL.md').read().split('---')[1])"
```

**Expected:** 无错误，frontmatter YAML 可解析

### 步骤 4: 提交

```bash
cd /Users/wenchen/workspace/personal-article
git add .claude/skills/article-publish/SKILL.md
git rm .claude/skills/article-publish/SKILL.md.bak
git commit -m "feat(article-publish): add Step 3.5 image download to SKILL.md

- Insert image download & link replacement between Step 3 and 4
- Add slugify rules for directory naming
- Add idempotency note for repeated publishes
- Update skill description to mention image downloading"
```

---

## Self-Review

### Spec Coverage

| 设计文档章节 | 实现任务 |
|-------------|---------|
| 3.1-3.2 调用方式和参数 | Task 1, Step 4 `main()` 函数 |
| 3.3 行为（目录创建、重试、扩展名推断、文件名生成、去重、stdout/stderr、退出码） | Task 1, Step 4 完整实现 + Step 2 测试覆盖 |
| 3.4 示例 | Task 1, Step 6 CLI 验证 |
| 4.1 更新后的完整流程 | Task 2, Step 2 SKILL.md 修改 |
| 4.2 Step 3.5 详细步骤 | Task 2, Step 2 插入的 Markdown 内容 |
| 5. slugify 规则 | Task 2, Step 2 中的步骤 1 |
| 6. 错误处理策略 | Task 1, Step 4 异常处理 + Task 2 Step 2 "If exit code is 1..." |
| 7. 边界情况（重复发布、混合图片等） | Task 2, Step 2 Notes 中的 idempotency 说明 |

### Placeholder Scan

- ❌ 无 "TBD", "TODO", "implement later"
- ❌ 无 "Add appropriate error handling" 等模糊描述
- ❌ 无 "Similar to Task N" 引用
- ✅ 所有代码步骤包含完整代码
- ✅ 所有运行步骤包含确切命令和预期输出

### Type Consistency

- `download_image(url, output_dir)` 签名在测试和实现中一致
- `infer_extension(content_type, url)` 参数顺序一致
- `generate_filename(output_dir, extension)` 参数顺序一致

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-29-article-image-download.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session, batch execution with checkpoints

**Which approach?**
