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
