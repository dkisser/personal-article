---
name: goal-review
description: >
  Review writing goals against actual vault article output. Use when the user
  asks about goal progress, achievement status, or writing review:
  (1) Phrases like "目标达成", "goal review", "review goals", "目标回顾",
      "进度如何", "写了多少", "本周/本月写了多少"
  (2) Questions about whether weekly/monthly article targets were met
  (3) Requests for improvement suggestions based on current writing pace
  (4) Checking what articles need attention (missing dates, stuck drafts, etc.)
  (5) Any request to analyze or summarize the current state of the vault
---

# Goal Review

Read the current goal from the vault root `goals.md`, then analyze all articles
in the vault to assess progress and give actionable feedback.

## Workflow

1. **Load the goal**
   - Read `goals.md` from the vault root.
   - Extract the current target (e.g. "每周 3 篇").

2. **Collect statistics**
   - Determine the goal period from `goals.md` (weekly / monthly / yearly).
   - Run `scripts/analyze_vault.py <vault-root> --period <weekly|monthly|yearly>` via Bash.
   - The script returns JSON with:
     - `period` and `period_start`
     - `period_count` / `period_articles` (matching the goal period)
     - `total_articles`
     - `by_status` (e.g. idea, draft, published)
     - `this_week_count` / `this_month_count` / `this_year_count`
     - `articles_with_date` / `articles_without_date`
     - `by_tag`

3. **Compare and evaluate**
   - Map the goal interval (weekly / monthly / yearly) to `period_count`.
   - Determine if the target is met, exceeded, or short.
   - Flag articles that lack a `date` field (they skew time-based metrics).
   - Note drafts that have been idle for a long time.

4. **Report findings**
   - State the current goal clearly.
   - Show actual numbers vs. target.
   - List articles written in the relevant period.
   - Call out gaps: missing dates, stalled drafts, low tag variety, etc.

5. **Calculate rewards and penalties**
   - Read `reward.md` from the vault root.
   - Based on the goal target and actual output, determine applicable rewards
     or penalties:
     - Target met or exceeded → apply rewards per the rules table.
     - Target missed → apply penalties per the rules table.
   - Show the user the calculated result before writing it.

6. **Write reward record**
   - Append a new row to the **奖惩记录** table in `reward.md` with:
     - Date (today)
     - Cycle identifier (e.g. "2026-W19" or "第 3 周")
     - Event description (e.g. "完成 3/3 篇，达标" or "完成 1/3 篇，未达标")
     - Reward or penalty value
     - Running cumulative total
   - Do NOT overwrite existing rows; always append.

7. **Suggest improvements**
   - If short: suggest quick wins (finish a short draft, write a stub).
   - If met or exceeded: suggest quality improvements (polish a draft,
     cross-link articles, add tags).
   - If many articles lack dates: suggest a bulk date update.

8. **Update goal history (optional)**
   - If the user agrees, append a new row to the goal history table in
     `goals.md` when the goal changes or a review milestone is reached.
