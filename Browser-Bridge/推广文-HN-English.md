---
status: draft
tags: [Browser-Bridge, open-source, agent, browser-automation, HackerNews]
created: 2026-06-23
published:
category: Browser-Bridge
channels: [HackerNews]
---

# Show HN: Browser-Bridge – Use your real Chrome as a tool from any agent

## Background

A "Show HN"-style post draft. Title proposed:

> **Show HN: Browser-Bridge – Use your real Chrome as a tool from any agent**

## Body

Hi HN,

I built [Browser-Bridge](https://github.com/dkisser/browser-bridge) because I was frustrated that "let an AI drive my browser" — arguably the most useful agent feature of the last year — keeps getting shipped as a vertically integrated app (OpenAI's Codex desktop browser, Kimi's standalone browser, Dia, Arc Search, etc.).

I don't want a new app. I want my **existing** Claude Code, Cursor, Dify workflow, or a 30-line Python script to be able to drive **the Chrome I'm already logged into**.

So Browser-Bridge is just that layer: a protocol-neutral bridge that exposes your real local Chrome as a tool any agent can call over WebSocket.

<!-- GIF placeholder: 30-second demo — Claude Code driving my logged-in Chrome to pull data from an internal dashboard -->

## Why not Playwright / Playwright MCP / Browser-Use?

Fair question — I asked myself this before writing a line of code.

| | Browser-Bridge | Playwright MCP | Browser-Use | Codex / Kimi browser |
|---|---|---|---|---|
| Drives **your** Chrome (logged-in sessions) | yes | no — fresh headless | no — fresh instance | yes, but locked to their app |
| Protocol-neutral, any agent can connect | yes | MCP only | framework-bound | no |
| No inbound port, outbound-only WebSocket | yes | no | no | — |
| Install | one curl + load extension | heavier | medium | install their app |

The first row is the whole point. Playwright-based solutions spawn a clean browser — none of your Gmail, Notion, internal SSO, or company VPN cookies are there. Browser-Bridge drives the actual Chrome window on your screen, which is exactly why the Codex/Kimi experience feels magical and why open-source alternatives have felt incomplete.

## Architecture

```
[ Agent / CLI / script ]
       │ WebSocket (outbound)
[ Cloud relay ]
       │ WebSocket (outbound)
[ Local agent on your machine ]
       │
[ Chrome extension (MV3) ]
       │
[ Your real Chrome tab ]
```

Four-hop WebSocket, **outbound connections only**:

- No inbound port opened on your machine
- Cookies / sessions / credentials never leave your device — the relay only forwards commands, it never sees your data
- Extension must authenticate before registering; commands must transit the relay

The threat model is roughly: "I trust my own machine and my Chrome profile; I don't want to expose any local port, and I want the relay to be unable to read my session even if compromised." Happy to dig into this in comments — it's the part I spent the most time on.

## 30-second start

```bash
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# Load the generated extension folder in Chrome, start the service.

bridge browser:list
bridge navigate https://github.com --browser <browser-id>
```

<!-- GIF placeholder: install → first navigate -->

## What it unlocks

- **Claude Code as a real coding assistant**: have it pull from your authenticated company wiki, Jira, internal API docs — because it's driving the Chrome you're already logged into. A Claude Code skill ships with the repo.
- **Dify / n8n / Coze workflows that touch local state**: cloud workflow nodes can now reach into your local browser (e.g. open authenticated dashboards, screenshot, post to Slack).
- **Langchain / arbitrary scripts**: protocol is plain WebSocket; ~30 lines of Python is enough.
- **MCP**: trivially wrappable as an MCP server for Cursor / Cline / Claude Desktop.

## What it deliberately is not

- **Not a replacement for Browser-Use's DOM reasoning.** Browser-Bridge is the transport/control layer. If you want "look at this page and decide what to click", bring your own LLM on top.
- **Not a cloud browser.** It's your laptop's Chrome — turn off your laptop, it's gone.
- **API surface is still thin.** `navigate` and primitive actions work; richer DOM operations are landing as real users tell me what they need.

I'd rather ship something honest about its limits than over-promise.

## Status

- MIT, Bun + TypeScript end-to-end
- Solo project, just started promoting it; goal is 100 users and 10 real pieces of feedback
- Roadmap follows whatever real workloads people throw at it

Repo: **https://github.com/dkisser/browser-bridge**

Most useful feedback I can get: "I wanted to use it for X but it's missing Y." Tear into the threat model too — that's the part I'm least sure about and most want challenged.

Thanks!

## Summary

Codex and Kimi proved that "AI driving a browser" is a killer experience, but they've shipped it as locked-in apps. Browser-Bridge extracts that layer into a neutral bridge so any agent — Claude Code, Cursor, Dify, Langchain, even a curl one-liner — can drive your real, logged-in Chrome.

## Links

- Repo: https://github.com/dkisser/browser-bridge
