# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Obsidian vault** for personal articles and ideas. It serves as a private writing space where thoughts evolve into published pieces.

## Structure

- `manager/` — Internal catalog tracking all articles: what's published, what's just an idea, and what's in progress.
- `wiki.md` — Public-facing index of all published articles with one-way links.
- Articles live at the top level or in topical folders. Each article is a Markdown file.
- Use Obsidian wiki-links (`[[Article Title]]`) to connect related ideas.
- Use YAML frontmatter for metadata: `status` (idea/draft/published), `tags`, `date`.

## Claude's Role

Act as a **writing partner**: help draft, edit, and polish articles. Brainstorm ideas, suggest connections between notes, and improve clarity. Do not rewrite the user's voice — preserve their style while tightening prose.

## Conventions

- Prefer **sentence case** for article titles (not Title Case).
- Use **wiki-links** for cross-referencing ideas, not raw URLs.
- Tag articles with broad themes (e.g., `#productivity`, `#tech`, `#reflection`) for discoverability.
- When updating the manager catalog, keep the `status` field in sync with the article's frontmatter.
- New article ideas can start as stub files with just a title and `status: idea`.

## Article Frontmatter

All articles use YAML frontmatter. Key fields:

- `status`: `idea` | `draft` | `published`
- `tags`: list of hashtags
- `created`: `YYYY-MM-DD`
- `published`: `YYYY-MM-DD` (set when status becomes published)
- `category`: folder name (e.g. `开发踩坑日记`)
- `source`: primary link (usually 墨问)
- `channels`: **list of objects**, each with:
  - `name`: channel name (墨问 / CSDN / 知乎 / infoQ)
  - `url`: article URL on that channel
  - `views`, `likes`, `collects`, `comments`: numeric stats (default 0)
  - `published_at`: `YYYY-MM-DD`

**Important**: `channels` must be an array of objects, not a key-value map. Empty initial value is `channels: []`. See existing published articles for examples.
