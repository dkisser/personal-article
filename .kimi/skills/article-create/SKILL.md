---
name: article-create
description: Create a new article idea and scaffold it in the Obsidian vault. Use when the user wants to start writing a new article, generate an article idea, or create a draft. Triggers on phrases like "写一篇", "新建文章", "文章想法", "article idea", "new article", or when the user wants to add content to any of the five categories (热点, 开发踩坑日记, 产品体验与思考, 经验总结, 小工具分享).
---

# Article Create

Create a new article scaffold in the vault and register it in the manager catalog.

## Workflow

Creating a new article involves these steps:

1. Determine category and topic
2. Generate or confirm title
3. Create article file with template frontmatter
4. Register in category manager catalog
5. Update master manager README stats

### Step 1: Determine Category and Topic

The vault has five categories. Identify which one matches the user's intent:

| Category | Description | Directory |
|----------|-------------|-----------|
| 热点 | 行业热点、新闻事件、技术趋势看法 | `热点/` |
| 开发踩坑日记 | 技术踩坑记录与解决方案 | `开发踩坑日记/` |
| 产品体验与思考 | 产品深度体验分析与思考 | `产品体验与思考/` |
| 经验总结 | 工作、学习、生活经验沉淀 | `经验总结/` |
| 小工具分享 | 自己开发或发现的有用工具 | `小工具分享/` |

If the user did not specify a category, ask them to choose one. If they mentioned a topic but not a category, infer the best fit and confirm.

### Step 2: Generate or Confirm Title

- If the user provided a title, use it (sentence case preferred).
- If the user only gave a topic/idea, generate 2-3 title options and let them pick or refine.
- The title becomes the filename (e.g. `文章标题.md`).

### Step 3: Create Article File

Create the article in the appropriate directory with this frontmatter:

```yaml
---
status: idea
tags: []
created: YYYY-MM-DD
published:
category: <category-name>
---
```

Add a heading `# <title>` and a brief outline or placeholder sections based on the category:

- **热点**: 背景 / 观点 / 影响 / 总结
- **开发踩坑日记**: 问题描述 / 环境 / 排查过程 / 解决方案 / 教训
- **产品体验与思考**: 产品简介 / 核心体验 / 优点 / 不足 / 思考
- **经验总结**: 背景 / 方法 / 实践 / 成果 / 可复用性
- **小工具分享**: 工具简介 / 使用场景 / 安装/使用方法 / 效果展示

### Step 4: Register in Category Manager Catalog

Open `manager/<category>.md` and append a row to the article list table:

```markdown
| [[<title>]] | idea | — | YYYY-MM-DD | — |
```

Also add a link under the "想法" section if one exists.

### Step 5: Update Master Manager README

Open `manager/README.md` and update the count for the corresponding category in the summary table.

## Notes

- Do not overwrite existing files. If a file with the same name exists, append a number or ask the user.
- Keep the outline minimal — just enough structure to get started.
- After creation, tell the user the file path and suggest the next step (start writing or brainstorm).
