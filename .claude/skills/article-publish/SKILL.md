---
name: article-publish
description: Publish a finished article by updating its status, generating a description, downloading external images to local storage, replacing image links with relative paths, and syncing the wiki catalog. Use when the user says an article is complete, wants to publish, or finalize an article. Triggers on phrases like "发布", "publish", "写完了", "完成", "finalize", or the slash command /article-publish.
---

# Article Publish

Finalize an article by updating its status to "published", generating a description, and syncing all catalogs.

## Workflow

Publishing an article involves these steps:

1. Identify the article file
2. Read content and generate description
3. Update article frontmatter
4. Update category manager catalog
5. Update master manager README
6. Update public wiki.md

### Step 1: Identify the Article File

- If the user provided a title or filename, locate it.
- If no article is specified, list recent draft files and ask the user to pick one.
- Search in all category directories: `热点/`, `开发踩坑日记/`, `产品体验与思考/`, `经验总结/`, `小工具分享/`.

### Step 2: Read Content and Generate Description

Read the full article content. Generate a concise description (100 Chinese characters or fewer) that summarizes the core point. The description should:

- Capture the main takeaway
- Be suitable for a table of contents or social sharing
- Not exceed 100 characters

### Step 3: Update Article Frontmatter

Update the article's YAML frontmatter:

```yaml
---
status: published
tags: []               # add relevant tags if missing
created: YYYY-MM-DD    # keep original
published: YYYY-MM-DD  # today's date
category: <category>
description: <generated description>
---
```

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
   - Call: `python scripts/download_image.py <url> images/<slug>/` from the vault root directory
   - Capture stdout (local file path relative to the vault root, e.g. `images/<slug>/image-1.png`)
   - If exit code is 1 (download failed), skip this image and keep the original external URL

5. **Compute the article-relative image path and replace the link:**
   - `download_image.py` returns a path relative to the vault root.
   - Before writing the link into the article, convert it to a path relative to the **article file's directory** so that both Obsidian and GitHub Markdown preview resolve it correctly.
   - Conversion rule: `article_image_path = os.path.relpath(vault_root_image_path, article_file_parent_dir)`
   - Common cases:
     - Article in vault root: `images/<slug>/image-1.png` stays `images/<slug>/image-1.png`
     - Article in a first-level category folder (e.g. `产品体验与思考/`): `images/<slug>/image-1.png` becomes `../images/<slug>/image-1.png`
   - In article content, replace the external URL with the computed relative path: `![](<article_image_path>)`

6. **Save the updated article** with replaced image links.

**Examples:**

Article in vault root:
```markdown
# Before
![](https://priv-sdn-001.mowen.cn/.../2060198638129446914.png?Expires=...)

# After
![](images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png)
```

Article in `产品体验与思考/`:
```markdown
# Before
![](https://priv-sdn-001.mowen.cn/.../2060198638129446914.png?Expires=...)

# After
![](../images/dang-ni-yao-xu-yao-mcp-server-shi/image-1.png)
```

### Step 4: Update Category Manager Catalog

Open `manager/<category>.md`. Find the article's row in the table and update:

- `status`: idea/draft → **published**
- `发布日期`: add today's date
- Optionally append the description in parentheses after the title link

Move the article link from the "草稿" section (if present) to the "已发布" section.

### Step 5: Update Master Manager README

Open `manager/README.md` and update the count for the corresponding category in the summary table. Increment the published count, decrement the draft count if applicable.

### Step 6: Update Public Wiki

Open `wiki.md`. Under the heading matching the article's category, append a one-way link entry:

```markdown
- [[<title>]] — <description>
```

If the category heading does not exist yet, create it first.

## Notes

- If the article's `status` is already `published`, warn the user and skip frontmatter/catalog updates, BUT still run Step 3.5 (image download) if there are external images.
- The description is the key output — make it informative and concise.
- After publishing, suggest next steps: share the article, create a follow-up, or start a new one.
- **Image download idempotency:** Running publish multiple times on the same article is safe — existing images are skipped, and links are idempotently replaced.
