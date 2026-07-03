---
status: draft
tags: [Browser-Bridge, open-source, agent, browser-automation, Reddit]
created: 2026-06-23
published:
category: Browser-Bridge
channels: [Reddit]
---

# I built an open-source bridge that lets any agent drive your real Chrome (instead of being locked into Kimi/Codex's apps)

## Background

General Reddit draft, tuned for r/programming, r/opensource, r/SideProject, r/coolgithubprojects. Tone is "I built this, here's why, here's the honest tradeoff" — no marketing fluff, no emoji, no "🚀 launching" energy. Reddit punishes that.

If you're cross-posting:
- **r/programming** — keep as is, lead with the technical comparison.
- **r/opensource** — emphasize MIT, self-hostable relay, no-telemetry.
- **r/SideProject** — soften the tone slightly, add "would love feedback" earlier.
- **r/selfhosted** — swap the title to focus on "self-hosted Chrome control for agents", lead with the architecture diagram.

Don't post the same text to multiple subs simultaneously — Reddit's spam filter will eat it. Space them out by a day, and rewrite the title for each.

## Body

### What I built

[Browser-Bridge](https://github.com/dkisser/browser-bridge) — an MIT-licensed bridge that turns the Chrome **you're already using** (with all your existing logins, cookies, SSO sessions) into a tool that any agent or script can call over WebSocket.

<!-- GIF placeholder: 30-second demo — an agent driving my logged-in Chrome to pull data from an authenticated dashboard -->

### Why I built it

"AI agent that drives a browser" became a flagship feature in the last year — Codex desktop has it, Kimi shipped a whole standalone browser around it, Dia and Arc Search are pushing the same idea.

The experience is great. The catch is that **every implementation is locked to one specific app**. I can't tell my Claude Code instance to peek at our internal wiki while it codes. I can't have a Dify workflow grab data from an authenticated dashboard at 9am. I can't use my own Langchain script to reuse the Chrome I'm already logged into.

Meanwhile the open-source alternatives (Playwright, Playwright MCP, Browser-Use) all have a sharp limitation: **they spawn a fresh browser instance**. None of your real cookies are there, so anything that needs a login is off-limits.

I wanted "browser control" to be infrastructure, not a feature of one product. So I built it.

### How it works

```
[ agent / CLI / script ]
        │ WebSocket (outbound)
[ relay ]
        │ WebSocket (outbound)
[ local agent on your machine ]
        │
[ Chrome extension (MV3) ]
        │
[ your real Chrome tab ]
```

Four-hop WebSocket, **outbound-only**:

- No inbound port opened on your machine
- Cookies, sessions, credentials never leave your device — the relay forwards opaque commands and never sees the data
- Extension must authenticate before registering; commands must transit the relay
- Relay is just a WS server, you can self-host it on a VPS / Tailscale node and skip the public one

MIT, Bun + TypeScript end-to-end.

### Comparison with the obvious alternatives

| | Browser-Bridge | Playwright MCP | Browser-Use | Codex / Kimi browser |
|---|---|---|---|---|
| Drives **your real** Chrome (with existing sessions) | yes | no — fresh headless | no — fresh instance | yes, but locked to their app |
| Protocol-neutral, any agent / framework can connect | yes | MCP only | framework-bound | no |
| No inbound port, outbound-only | yes | no | no | — |
| Self-hostable | yes | n/a | n/a | no |
| License | MIT | MIT/Apache | MIT | proprietary |

The first row is the whole pitch. Everything else flows from it.

### 30-second start

```bash
curl -fsSL https://github.com/dkisser/browser-bridge/releases/latest/download/install.sh | bash

# Load the generated extension folder in Chrome, start the service.

bridge browser:list
bridge navigate https://github.com --browser <browser-id>
```

<!-- GIF placeholder: install → first navigate -->

### Things people have wired it to

- **Claude Code** — pulling from authenticated company wiki / Jira / internal API docs while writing code. A skill ships with the repo.
- **Dify / n8n / Coze workflows** — cloud workflow nodes can finally reach into your local browser (open authenticated dashboards, screenshot, push to Slack).
- **Langchain / arbitrary scripts** — protocol is plain WebSocket; ~30 lines of Python is enough.
- **MCP** — wraps cleanly into an MCP server for Cursor / Cline / Claude Desktop.

### What it deliberately is not

- **Not a replacement for Browser-Use's DOM reasoning.** It's the transport layer. If you want "look at the page, decide what to click" — bring your own LLM on top.
- **Not a cloud browser.** It's your laptop's Chrome. Close the laptop, it's gone.
- **API surface is still thin.** `navigate` and basic actions work today; richer DOM operations land as real users tell me what they need.

I'd rather be honest about the edges than over-promise.

### Status

- MIT, just started promoting it
- Solo project, goal is 100 users + 10 real pieces of feedback
- Roadmap follows actual user workloads, not my imagination

Repo: **https://github.com/dkisser/browser-bridge**

Most useful feedback I can get is **"I wanted to use it for X but it's missing Y"** — that directly shapes what I build next. Threat-model criticism also very welcome; the outbound-only architecture is the part I spent the most time on and the part I'm least sure about.

Thanks for reading.

## Summary

Codex and Kimi proved "AI driving a browser" is a killer feature, but they shipped it as locked-in apps. Browser-Bridge extracts that capability into a neutral, MIT-licensed bridge so any agent — Claude Code, Cursor, Dify, Langchain, or a curl one-liner — can drive your real, already-logged-in Chrome. Outbound-only, self-hostable, no telemetry.

## Links

- Repo: https://github.com/dkisser/browser-bridge
