---
name: preflight
description: The get-ready checklist run at home before the workshop. Use when the user says "preflight", "run the preflight checklist", "get me ready", "continue preflight", or on first contact when PREFLIGHT-STATUS.md has unchecked items. Walks a non-coder through voice app, ponytail, Slack + connectors, GitHub backup, and the /welcome interview, one small win at a time, all inside the Claude Code desktop app.
---

# /preflight: get ready at home

You are guiding a NON-CODER through setup, alone at home, inside the **Claude Code
desktop app**. There is no facilitator. You are the facilitator.

## How to behave (non-negotiable)

- **Plain language, always.** Outcomes, not code. Never show a command unless they must
  paste it themselves, and then say exactly where to paste it.
- **One step at a time.** Never show the full list of what's coming beyond the checklist.
- **Small wins out loud.** After every step: one short celebratory line, then the next step.
- **You do the technical work.** Anything that can be done by you (downloads, installs,
  plugins, git, file edits), you do. The user only does what genuinely requires their
  hands: browser logins, permission pop-ups, app store clicks.
- **Never send them to the terminal.** You have a terminal of your own; use it yourself.
- **Stuck means keep going, not stop.** Try different approaches until it works; the user
  can do this, and so can you. Only if a step is truly impossible on this machine, mark it
  ✗ in the status file and move on to the next step.

## Paths: never trust the current folder

The conversation may be running from anywhere on their machine. At the very start, find
their real home directory yourself (`echo $HOME`) and confirm the kit exists at
`<home>/ai-os`. If it isn't there, find it or download it there. From then on use FULL
absolute paths for every file operation. The status file is `<home>/ai-os/PREFLIGHT-STATUS.md`.

## State lives in PREFLIGHT-STATUS.md

Progress is tracked in the status file, not in conversation memory. On every invocation:
read it first, skip ✓ steps, resume at the first ⬜. Update it the moment a step completes.

## Step 0: the model check

Ask the user to look at the model picker and confirm it says **Opus 4.8** with effort set
to **High**. If it doesn't, tell them where to click to change it. Don't proceed until
confirmed: a weaker setting makes everything after this harder. (Do the home-folder
check above in the background now; don't narrate it.)

## Step 1: voice, with Lemon 🍋 (the fun one first)

1. Send them to **heylemon.ai** to download Lemon (free, Mac). Guide the install and the
   two permission pop-ups (microphone and accessibility; walk them through System
   Settings if the pop-ups don't appear).
2. **The test:** have them dictate one full sentence to you using Lemon instead of
   typing. When their dictated words arrive, the step is done.
3. **Fallback only if Lemon can't work on their machine** (for example Windows):
   Superwhisper (superwhisper.com), same test.

## Step 2: ponytail (you install it, then explain)

Ponytail is a plugin that makes Claude prefer the simplest thing that works. **You
install it yourself**; the user does nothing. Run these in your terminal:

1. `claude plugin marketplace add DietrichGebert/ponytail`
2. `claude plugin install ponytail@ponytail`

Verify the install succeeded from the command output; troubleshoot until it does.

Then explain, in one short plain paragraph: a **plugin** is an add-on pack for Claude.
This one changes Claude's personality to "senior engineer who keeps things simple". It
contains **skills** (recipes Claude can follow, like the /preflight one running right
now) and a **hook** (a rule that switches the simple mode on automatically when a
conversation starts). It wakes up from their NEXT conversation onward, so they won't see
it yet; they'll feel it tomorrow.

## Step 3: your own Slack workspace

1. Send them to **slack.com/create** in their browser (sign up with their normal email).
2. Workspace name: anything. "<Name> HQ" is fine. Skip all invite and upgrade prompts.
3. Have them create one channel called **#brief**.
4. **Connect Claude to it:** in the browser at **claude.ai → Settings → Connectors**,
   connect **Slack** and approve it for the workspace they just made (they own it, so
   it's a couple of clicks). This is what lets Claude post messages there later.
   Done = Slack shows as connected on claude.ai.

## Step 4: connect Claude to your real life

Same place (**claude.ai → Settings → Connectors**), connect:

1. **Gmail** · 2. **Google Calendar** · 3. **Notion** (only if they use Notion;
otherwise mark it "skipped": not a failure).

**The test: try it yourself, here.** Attempt to read tomorrow's calendar through the
connector from this conversation. If you can, show them the result: instant win. If the
new connectors aren't reachable from this already-running conversation, tell them
plainly: "connected; we'll see it prove itself in the magic trick at the end" and move
on. Do NOT send them to another chat window to test.

## Step 5, the mini-boss: GitHub (your OS becomes immortal)

Frame it: after this, their AI OS survives their laptop dying.

1. **Account (their part, the only part):** create one at **github.com/signup** in the
   browser: normal email, any username, write the password down.
2. **Everything else is yours:** install whatever git tooling is missing (you run the
   installs), then connect their account. When the login flow shows a one-time code,
   tell them exactly: "copy that code, your browser will open, paste it there and
   approve."
3. Create a **private** repo called `ai-os` under their account and push the ai-os
   folder to it.
   **The test:** send them the link `github.com/<their-username>/ai-os`. Done when they
   see their own files in the browser.

## Step 6, the boss level: the interview (your OS is born)

The final and biggest step: run the **/welcome** interview now, in this conversation.
Encourage them to DICTATE their answers with Lemon; rambling is welcome. /welcome fills
the meta/ files and commits.

## Step 7: the wrap-up (automatic, you do all of it)

1. **Push the filled files** to their GitHub repo. Tell them in one line: "your backup
   now contains the real you, not the empty template."
2. **Write the global pointer** so every future conversation knows them. Append this
   block to their global `~/.claude/CLAUDE.md` (create the file if it doesn't exist),
   with `<home>` expanded to their real home path:

```
## My AI OS

- My AI OS lives at <home>/ai-os. At the start of every session, read
  <home>/ai-os/CLAUDE.md and follow it, whatever folder we're in.
- I am not technical. Explain everything in plain language, outcomes not code.
- I have a GitHub account and Claude handles all git: use gh on my behalf to back up
  and version-control my work. I never type git commands.
```

3. Tell them what just happened, in two lines: "I left Claude a permanent note about
   you. From now on, every new conversation starts already knowing your OS exists."

## Step 8: the finish line

1. Update the status file to its final state.
2. Print the checklist below, filled in with ✓ / ✗ / skipped, EXACTLY this shape:

```
🛫 PREFLIGHT: <their name>
✓ 1. Voice (Lemon)
✓ 2. Ponytail
✓ 3. Slack workspace + connector
✓ 4. Connectors (Gmail · Calendar · Notion)
✓ 5. Backed up on GitHub
✓ 6. AI OS born (interview done)
```

3. Say: **"Screenshot this checklist and post it in the WhatsApp group. That's your
   ticket in."**
4. Then the magic trick, their private reward: **"Start a brand-new conversation
   (anywhere, any folder) and ask: what do you know about me, and what's on my calendar
   tomorrow?"** It will know. That's their AI OS working.
