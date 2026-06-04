# ShieldOps Demo Storyline — The Presentation

## The Arc (5 minutes, told like a keynote)

This isn't a code walkthrough. It's a **story about trust**.

---

### ACT 1: THE PROBLEM (60 seconds)
**Slide/Section: "The Security Debt Death Spiral"**

Open with something every VP has lived through:

> "Your security scanner just told you there are 47 vulnerabilities in your dependencies. Your engineers are shipping features. Nobody picks up the tickets. Three months later, an auditor asks: 'What's your mean time to remediate critical CVEs?' and the room goes quiet."

Then the twist — the real problem isn't detection:

> "Scanning is solved. Even writing a version bump is solved — Dependabot does it for free. The problem is the 20% that breaks. A major upgrade changes an API. Dependabot opens a red PR and walks away. That PR sits there forever. THAT is where security debt actually lives."

**What the audience feels:** "Yeah, that's us."

---

### ACT 2: THE LIVE DEMO (120 seconds)
**Slide/Section: "Watch what happens"**

This is the hero moment. Show it happening in real-time (or replay real artifacts):

**Scene 1: The scan**
"We pointed ShieldOps at Apache Superset — 500K lines of code, 200+ Python dependencies. It found 7 vulnerabilities. Two are critical."

Show: The GitHub issues that were auto-created (they exist at gaurav21/superset)

**Scene 2: The triage**
"Not all vulnerabilities are equal. ShieldOps scored each one — severity, whether a fix exists, whether the vulnerable code is even reachable in this codebase. 30% of CVEs were deprioritized because the vulnerable code path isn't imported."

Show: Triage output with priority scores and reachability flags

**Scene 3: THE HERO — Devin fixes a breaking change**
"Here's the one that matters. Flask 2.3.3 → 3.x. This is a major version upgrade. Dependabot would open a PR, the build would fail, and it would sit red forever."

Show: 
- Devin session created
- First build fails (breaking change!)
- Devin reads the CHANGELOG
- Devin finds and fixes the call sites
- Tests go green
- PR created with evidence bundle

> "That right there — reading the error, understanding the CHANGELOG, fixing the call sites, iterating until green — that's the work only an autonomous coding agent can do."

**Scene 4: The policy boundary**
"But here's the thing — a VP doesn't want 47 PRs landing in their codebase unchecked. So every fix goes through a policy boundary."

Show: The policy decision
- Simple patch bump → auto-merge ready (tests pass, no breaking changes, high confidence)
- Breaking change fix → needs-human (but with a 2-minute evidence bundle)
- Failed fix → blocked (nothing merged, alert fired)

> "You're not removing the human. You're making sure a human only sees the few changes that need judgment — with everything they need to approve in two minutes."

---

### ACT 3: THE CONTROL PLANE (60 seconds)
**Slide/Section: "What the VP sees"**

This is where Datadog shines. Show the dashboard:

> "If I'm a VP, I have one question: is this thing safe to run?"

Walk through the dashboard:
- **The fleet:** 3 sessions active, 12% intervention rate, 87% confidence
- **The trust split:** 7 auto-merge ready, 2 need human review, 1 blocked
- **The Dependabot-can't metric:** 4 breaking changes handled autonomously
- **The cost:** $X per fix, 43 minutes average time to verified fix
- **The audit trail:** every scan, session, policy decision logged

> "This isn't a monitoring dashboard. It's a trust dashboard. It answers: can I let this fleet run while I sleep?"

---

### ACT 4: WHY DEVIN (30 seconds)
**Slide/Section: "The difference"**

Quick, sharp comparison:

> "Detection is solved. Easy bumps are solved. The judgment-heavy, breaking-change work wasn't — until an autonomous agent could do it safely behind a policy boundary."

The three things only Devin can do here:
1. Read a CHANGELOG and understand what will break
2. Fix call sites across a 500K-line codebase
3. Iterate on test failures until green

---

### ACT 5: NEXT STEPS (30 seconds)
**Slide/Section: "Where this goes"**

> "This demo ran against one repo. In production:
> - Wire into CI — scan on every merge
> - Expand auto-merge policy as trust grows
> - Scale across every repo in the org
> - Cost optimization with ACU budgeting
> - The fleet gets better as confidence data accumulates"

---

## HOW THE WEBSITE SUPPORTS THIS

The website IS the presentation. Not a marketing site — a **keynote deck in web form**.

Each section maps to an act:
1. Hero → Title card
2. The Problem → Act 1
3. The Insight → The twist (dark band)
4. How It Works → The system overview  
5. The Comparison → Why not Dependabot
6. Architecture → Technical credibility
7. VP Dashboard → Act 3 (the control plane)
8. Trust Metrics → The monitors that make it safe
9. Demo → Act 2 (embedded Loom or screenshots)
10. GitHub → "Try it yourself"
11. Footer

### What the website needs to become:

**Presentation mode** = each section is a FULL VIEWPORT SLIDE that you scroll through, like a deck. Not a long scrolling page — discrete slides with transitions.

Changes needed:
- Each section = 100vh (full screen)
- Horizontal progress indicator or slide numbers
- Keyboard navigation (arrow keys to advance)
- Larger text, fewer words per slide
- Real screenshots/artifacts where possible (not just mock data)
- The Loom video embed in the Demo section
- Clean transitions between slides

---

## WHAT WE STILL NEED TO MAKE THIS REAL

### Must have (the demo is fake without these):
1. **At least ONE real Devin session on Superset** — producing a real PR. Ideally the Flask hero. Fallback: Dockerfile hardening (Issue #6, simpler).
2. **Real Datadog dashboard** — created in Gaurav's DD account with at least mock metrics populated
3. **Screenshots of real artifacts** — Devin session URL, the PR diff, the evidence bundle comment, the Datadog dashboard

### Strong to have:
4. **The Loom video** — 5 min, following the storyline above
5. **Website in presentation mode** — full-viewport slides
6. **Merge Devin's 2 PRs on ShieldOps** — shows Devin improving its own platform (bonus story)

### Nice to have:
7. Multiple Devin sessions (show the "fleet" concept)
8. A real blocked/failed session (shows the safety story)
9. Real metrics in Datadog (not just the dashboard structure)
