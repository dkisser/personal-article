---
name: article-publish
description: Publish a finished article by updating its status, generating a description, and syncing the wiki catalog. Use when the user says an article is complete, wants to publish, or finalize an article. Triggers on phrases like "发布", "publish", "写完了", "完成", "finalize", or the slash command /article-publish.
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

- If the article's `status` is already `published`, warn the user and skip updates.
- The description is the key output — make it informative and concise.
- After publishing, suggest next steps: share the article, create a follow-up, or start a new one.
