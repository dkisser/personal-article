---
status: draft
tags: [Browser-Bridge, open-source, agent, browser-automation, V2EX]
created: 2026-06-23
published:
category: Browser-Bridge
channels: [V2EX-EN]
---

# I built a Chrome extension that lets any local agent drive your real browser — no more being locked into Kimi/Codex

## Background

English version targeted at the V2EX-style audience (more conversational, pain-point first). Use this if you want to cross-post to English-speaking dev forums (Reddit r/LocalLLaMA, r/programming, dev.to) where a more narrative tone works better than HN's terse "Show HN" format.

## Body

> Short version: I wanted the "AI drives my browser" experience from Codex / Kimi, without being chained to their desktop app. So I built it.

Over the past few months, "agent that controls a browser" went from research demo to a flagship feature in every big launch — Codex desktop has it, Kimi shipped a whole standalone browser around it, Dia and Arc Search are pushing the same direction.

The experience is genuinely great. But the more I used it, the more it bothered me:

- I want **Claude Code** to peek at an internal wiki page while it codes — it can't.
- I want a **Dify / Coze** workflow to grab data from a logged-in dashboard at 9am every day — the workflow runs in the cloud, it can't reach my Chrome.
- I want my own **Langchain / Python** script to reuse the Chrome I'm already logged into — back to wrestling with Playwright and re-doing auth.

The pattern is clear: **"controlling a browser" should not be a feature of one specific app. It should be shared infrastructure that any agent can plug into.**

So I built [Browser-Bridge](https://github.com/dkisser/browser-bridge).

## What it is

In one line: **it turns the Chrome you're already using into a tool any agent can call.**

<!-- GIF placeholder: 30-second demo — Claude Code using Browser-Bridge to operate my logged-in internal page -->

It's not yet another agent. It's the "browser hands and feet" that all your existing agents can share. Plug in once, every tool gets it.

## Why not Playwright / Browser-Use / Playwright MCP

Honest comparison:

| | Browser-Bridge | Playwright MCP | Browser-Use | Codex / Kimi browser |
|---|---|---|---|---|
| Drives **your real** Chrome (with sessions) | yes | no — fresh headless | no — fresh instance | yes, but locked in their app |
| Protocol-neutral, any agent can plug in | yes | MCP only | framework-bound | no |
| No inbound port, outbound-only | yes | no | no | — |
| Install effort | one curl + load extension | medium | medium | install their app |

The first row is the whole story. Playwright-based stacks always spawn a clean browser — none of your Gmail, Notion, SSO, internal VPN cookies are in there. Browser-Bridge drives the actual Chrome on your screen.

That means **any page that needs you to be logged in, an agent can drive directly** — which is exactly the addictive part of Codex/Kimi browsers, and exactly the missing piece in Playwright MCP-style solutions.

## Architecture (30-second read)

```
[ Agent / CLI / script ]
       │ WebSocket
[ Cloud relay ]
       │ WebSocket
[ Local agent (your machine) ]
       │
[ Chrome extension (MV3) ]
       │
[ Your real Chrome tab ]
```

Four-hop WebSocket, **outbound connections only**:
- No local port opened, no inbound exposure
- Cookies / sessions / credentials **never leave your machine** — the relay only forwards commands, it never touches your data
- Extension must authenticate before registering; commands must transit the relay

If you care about security, this is the part I spent the most time on. Happy to take it apart in comments.

## 30-second start

```bash
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# Load the generated extension folder in Chrome, start the service.

bridge browser:list
bridge navigate https://github.com --browser <browser-id>
```

<!-- GIF placeholder: install → first navigate -->

## Real-world uses

**1. Claude Code as a coding assistant with internet access**

My most common use. While Claude Code is writing code, I let it pull from our company wiki / Jira / internal API docs — it works because the Chrome it's driving is already logged in as me. A Claude Code skill ships with the repo.

**2. Dify / Coze workflows that touch local state**

Add a HTTP / WebSocket node and your cloud workflow can suddenly "reach into" your local browser. E.g. every morning, open a couple of internal dashboards, screenshot, push to Slack.

**3. Langchain / your own scripts**

WebSocket protocol, language-agnostic. ~30 lines of Python lets your script "borrow" your Chrome.

**4. As an MCP server**

Wraps cleanly into MCP, so Cursor / Cline / Claude Desktop can call it directly.

## What it deliberately doesn't do

- **Doesn't replace Browser-Use's DOM reasoning.** Browser-Bridge is the transport layer. If you want "look at the page and decide what to click", bring your own LLM on top.
- **Not a cloud browser.** It's your laptop's Chrome — close the laptop, it's gone.
- **API surface is still thin.** navigate and basic actions work; richer ones land as users tell me what they need.

Better to be honest about the edges than over-promise.

## Status & feedback wanted

- MIT, Bun + TypeScript end-to-end
- Just started promoting it; goal is 100 users / 10 real pieces of feedback
- Roadmap follows real workloads, not my imagination

Repo: **https://github.com/dkisser/browser-bridge**

If you also believe browser control shouldn't be locked inside one app, give it a kick. Issues, PRs, complaints all welcome — the most useful feedback is **"I wanted to use it for X but it's missing Y"**.

## Summary

Codex and Kimi proved that "AI driving a browser" is a killer experience, but they shipped it as locked-in apps. Browser-Bridge pulls that layer out and makes it neutral infrastructure that any agent — Claude Code, Cursor, Dify, Langchain, or just a curl one-liner — can plug into.

## Links

- Repo: https://github.com/dkisser/browser-bridge
