# BofA Demo Runbook — Word-for-Word Script

> **Deck:** `boa.html` slides 0–6 (core) + 7–12 (appendix backup)
> **Total time:** 45 minutes
> **Informed by:** DE Technical Skills Framework (discovery, demo craft, security reasoning, agent loop intuition, deployment topology, competitive positioning)

---

## PRE-DEMO SETUP (5 min before call)

### Tabs to have open
1. **Deck** — `boa.html#0` (full screen)
2. **DeepWiki** — your Angular demo repo (e.g., `deepwiki.com/your-org/angular-demo-app`)
3. **Devin Cloud** — `app.devin.ai` logged in, with:
   - A **completed session** showing the Angular 14→18 migration PR
   - The **Knowledge** page with a few entries visible
   - The **Automations** page (if you have one configured)
4. **GitHub** — the finished PR from the completed session
5. **Backup:** Screenshot of Session Insights dashboard (in case live load is slow)

### Mental checklist
- [ ] Discovery notes from any pre-call intel (LinkedIn, annual report, prior conversations)
- [ ] Know which Angular version they're stuck on (if shared in pre-call)
- [ ] Have 2–3 "What I heard from you" tie-back phrases ready

---

## SLIDE 0 — TITLE (30 seconds)

> **[Slide is already showing as people join]**

**SAY:**

"Thanks for making the time. I'm Gaurav — I'm a Deployed Engineer at Cognition. That means I'm not sales. My job is to get embedded in your engineering org, configure Devin for your actual workflows, and make sure it delivers measurable results.

Before I show you anything — I want to spend the first few minutes understanding what's actually happening on the ground for your team. The more I know about your pain, the more relevant I can make the demo."

> **[Click → Slide 1]**

---

## SLIDE 1 — PLATFORM OVERVIEW (3 min)

**SAY:**

"Quick frame on what Devin actually is, because there's a lot of noise in the AI coding space right now.

Devin is not a copilot. A copilot sits in your IDE and suggests the next line of code — you're still driving. Devin is the opposite. You give it a task — a Jira ticket, a migration, a security finding — and it goes and does it. It spins up its own isolated VM with a shell, a browser, and an IDE. It clones your repo, reads the docs, writes the code, runs your test suite, iterates on failures until they pass, and opens a PR. Your engineer's job becomes reviewing the PR, same as they would for any other team member."

> **[Point to the 4 cards on screen]**

"Four things make this more than just a one-off code generator:

**One** — Devin Cloud sessions. Each one runs in its own isolated VM. And critically — **Managed Devins** — you can have one coordinator session break a big job into pieces and launch 50 parallel sessions, each in its own sandbox. That's how you go from 'one migration' to 'fleet migration.'

**Two** — Knowledge and Playbooks. This is the compounding effect. You teach Devin your patterns once — your migration recipes, your coding standards, your internal library quirks — and it auto-recalls that context in every future session. The first migration takes hours. The fiftieth takes the same amount of your time but Devin's already seen the pattern.

**Three** — Automations. This is where it gets interesting for security teams. A CVE scan fires, a finding lands in your queue, and a Devin session kicks off automatically — reads the advisory, fixes the code, opens a PR. No human needs to be in the loop to start the work. Only to review the output.

**Four** — Devin Review with Auto-Fix. Devin doesn't just open a PR and walk away. It reviews its own work. If CI fails, it reads the failure, fixes it, and re-pushes. If a reviewer leaves a comment, it responds and iterates. By the time you actually look at the PR, it's merge-ready."

> **[Gesture to customer logos at bottom]**

"This is already running in production at Itaú — Brazil's largest bank — where 70% of their security scanner findings are being resolved automatically. Nubank migrated a 6-million-line monolith with Devin. Gumroad's most prolific contributor is Devin — over 1,500 merged PRs."

> **[Pause. Let it land.]**

"But none of that matters if it doesn't map to your problems. So let me ask some questions."

> **[Click → Slide 2 briefly to show agenda, then → Slide 3]**

---

## SLIDE 2 — AGENDA (15 seconds, skip-through)

**SAY:**

"Quick agenda — five blocks, 45 minutes. Discovery is next, then I'll do a live demo shaped by what I hear from you. We'll save time at the end for security architecture and pilot design."

> **[Click → Slide 3]**

---

## SLIDE 3 — DISCOVERY (8 min)

> **THIS IS THE MOST IMPORTANT PART.** Don't rush it. The quality of this section determines whether the demo lands.

**SAY:**

"I want to start with a few questions. I don't need polished answers — I'm trying to understand what daily life looks like for your engineers."

### Question 1: Remediation timeline

**ASK:**

"When a critical CVE drops and it affects multiple repos — what does the end-to-end timeline look like from detection to merged fix? Not the policy. The reality."

> **LISTEN FOR:** Days vs. weeks vs. months. If weeks → that's the gap Devin fills. If they say "we're pretty fast" → probe: "Even for findings that require code changes, not just version bumps?"

### Question 2: Backlog

**ASK:**

"How many open security findings are sitting in your backlog right now? And is that number growing or shrinking?"

> **LISTEN FOR:** A number. If they won't share, ask: "Is it hundreds or thousands? Just trying to understand scale." Growing backlogs = urgency.

### Question 3: Toil ratio

**ASK:**

"If I talked to your most senior engineer right now — what would they say is the biggest waste of their time?"

> **LISTEN FOR:** Migrations, remediation, compliance work, boilerplate, CI babysitting. Whatever they say → you'll tie it to Devin in the demo.

### Question 4: Angular specifically

**ASK:**

"I understand there are Angular apps that need upgrading. Can you give me a sense of the scope — how many apps, which versions, and what's driving the timeline?"

> **LISTEN FOR:** Angular 14 (EOL Nov 2023), number of apps, whether they've started. If they haven't started → this is your pilot case.

### Question 5: AI governance

**ASK:**

"How does AI-generated code fit into your review process today? Is there a governance policy, or is the team still figuring that out?"

> **LISTEN FOR:** If they have a policy → you'll address it in security discussion. If not → opportunity to help them think through it. Either way, position Devin's "PR for human review" model as governance-compatible.

### Question 6: Compliance (if time)

**ASK:**

"When OCC examiners ask for test coverage evidence on compliance-critical paths — what do you show them today?"

> **LISTEN FOR:** Low coverage numbers, manual evidence collection, audit pain. This sets up the compliance expand.

### Bridge to demo

**SAY:**

"Really helpful — thank you. So what I'm hearing is [SUMMARIZE 2–3 KEY PAIN POINTS THEY SHARED]. Let me show you exactly how Devin addresses that."

> **[Click → Slide 4, then switch to browser for live demo]**

---

## SLIDE 4 → LIVE DEMO (15 min)

> **[Show slide 4 briefly as a roadmap, then switch to browser tabs]**

**SAY:**

"I'm going to walk you through the full end-to-end flow. I'll start with a finished Angular migration PR so you can see the output quality, then show you how the platform works underneath."

---

### STEP 1: DeepWiki (2 min)

> **[Switch to DeepWiki tab]**

**SAY:**

"Before Devin writes a single line of code, it needs to understand your codebase. This is DeepWiki — it auto-generates living documentation for any repo. Think of it as Devin's onboarding."

> **[Scroll through the generated docs — show the architecture diagram, the component tree, the dependency graph]**

"This is auto-generated. No one wrote this. Devin built this understanding of the repo by reading the code, the README, the test files, the config. When I give Devin a task in this repo, it already has this context.

Now — your engineers probably know their codebases intimately. But when you're running Devin across 10 or 50 repos, the agent can't rely on tribal knowledge. DeepWiki is how Devin gets the codebase context that a new hire would get in their first two weeks — except it does it in minutes."

---

### STEP 2: Ask Devin (2 min)

> **[Switch to Devin Cloud — open a new Ask Devin query or show a pre-run one]**

**SAY:**

"Before I even start a migration session, I can scope the work with Ask Devin. Watch this."

> **[Type or show the query: "Which components in this repo still use NgModules instead of standalone components?"]**

"This is code search powered by Devin's codebase understanding. It comes back with a structured answer — here are the 12 components still using NgModules, here's where they're imported, here's the dependency chain.

This is how I — as the Deployed Engineer — scope the work before launching a session. I know exactly what Devin is going to touch, and I can set clear success criteria: 'Convert all 12 NgModule components to standalone. Build must pass. Tests must pass.'

The clearer the success criteria, the higher the success rate. That's not just best practice — that's how the agent loop works. Verification is what makes autonomy possible."

> **[If someone asks "what if it gets stuck?" → HANDLE: "Great question. If Devin can't resolve a test failure after iterating, it flags it as low-confidence and stops. It doesn't push broken code. You can also pause any session at any time and take over in the IDE — it's not a black box."]**

---

### STEP 3: Session — The Finished PR (4 min)

> **[Switch to the completed Devin session showing the Angular 14→18 migration]**

**SAY:**

"Now let me show you the output. This is a completed Devin session — an Angular 14 to 18 migration on this repo."

> **[Click through the session timeline — show Devin's planning step, then code changes, then test runs]**

"Walk through what happened here. Devin started by reading the Angular 14 codebase — it identified every NgModule, every MatLegacy import, every deprecated RxJS operator. Then it planned the migration: standalone conversions first, then material import updates, then RxJS operators, then zone.js bootstrap changes.

Here's the key part — watch the test iteration."

> **[Show the part where Devin runs ng test, gets failures, reads the failure output, makes fixes, and re-runs]**

"This is what separates Devin from a copilot or from Dependabot. Dependabot bumps the version number and opens a PR. If the build breaks, it stops. Devin reads the test failure, understands what broke, fixes it, and re-runs. It kept iterating until `ng build --production` and `ng test` both passed.

That iteration loop is the whole ballgame. It's what turns a suggestion into a shippable PR."

> **[Switch to GitHub — show the PR]**

"And here's the output — a clean PR with a structured diff. NgModules converted to standalone. MatLegacy imports updated. RxJS operators replaced. Build green. Tests green. Full rationale in the PR description.

Now — this took Devin about [X minutes/hours]. A manual migration for a repo this size would typically take an engineer 6 to 8 developer-days. Your team's job is just to review this PR, same as they would for any other engineer's work."

> **[Pause. Let them absorb.]**

---

### STEP 4: Devin Review + Auto-Fix (1.5 min)

> **[Stay on the PR or show Devin Review interface]**

**SAY:**

"One more thing on this PR. Devin doesn't just open it and walk away. Devin Review runs automatically — it reviews its own PR, does visual QA in the browser, checks that the app actually renders correctly after the migration.

And if your reviewer leaves a comment — say, 'this import should use the new barrel export' — Devin reads the comment, makes the fix, and pushes a new commit. Auto-Fix. By the time you come back to the PR, it's usually merge-ready.

That matters at scale. If you're running 50 parallel migrations, you don't want to babysit 50 PRs. You want to come back to 50 merge-ready diffs."

---

### STEP 5: Automations (1.5 min)

> **[Switch to Automations page in Devin, or describe the concept]**

**SAY:**

"Now — that Angular migration, I kicked it off manually. But for security remediation, the real power is event-driven automations.

You can set up a trigger: when a SonarQube scan fires and creates a finding, or when a GitHub label gets applied to an issue, or when a Jira ticket lands in a specific queue — a Devin session kicks off automatically. No human needs to start it. The automation reads the finding, clones the repo, applies the fix, runs tests, and opens a PR.

So your scanner detects a CVE at 2 AM. By the time your engineer wakes up, there's a PR waiting for review. That's what 'closing the gap between scan speed and fix speed' actually looks like.

You can also schedule recurring work — daily dependency checks, weekly test coverage reports, nightly CI triage. Devin runs on a cron, does the work, posts results to Slack."

---

### STEP 6: Knowledge + Playbooks (1.5 min)

> **[Switch to Knowledge page in Devin settings]**

**SAY:**

"This is where the compounding effect comes in. Knowledge is how you onboard Devin to your org — the same way you'd onboard a new engineer.

Here's an example — I created this knowledge entry: 'When migrating Angular components in this org, always use the new barrel export pattern and preserve the existing test file structure.' Devin auto-recalls this in every relevant session. I don't have to repeat it.

Playbooks are the task-level version — a reusable migration recipe. 'Step 1: identify all NgModules. Step 2: convert to standalone. Step 3: update material imports. Step 4: run build and test. Step 5: flag low-confidence changes.'

The first migration takes real work to get right. The fiftieth runs the same playbook and Devin already has the knowledge. That's why Nubank saw 4× speed improvement after the initial fine-tuning — the system learns."

---

### STEP 7: Managed Devins / Parallel Fleet (2 min)

> **[Show or describe the coordinator pattern]**

**SAY:**

"And this is the scale play. Managed Devins.

Instead of running one session at a time, you spin up a coordinator session. The coordinator analyzes your repos, groups them into independent work packages that won't conflict, and launches a parallel Devin session for each one. Each session runs in its own isolated VM — completely sandboxed.

So if you have 30 Angular apps that need migrating — you don't do them one by one over 6 months. You launch 30 parallel sessions with the same playbook, the same knowledge, and the same success criteria. The coordinator tracks progress, monitors ACU consumption, and flags any sessions that got stuck.

You come back to 30 PRs waiting for review. That's the fundamental value proposition — it's not about making one engineer faster. It's about adding engineering capacity that scales linearly without hiring."

> **[Pause. This is the "aha" moment for most customers.]**

---

### DEMO TRANSITION BACK TO SLIDES

**SAY:**

"So that's the full flow — from codebase understanding to fleet-scale migration. Let me jump back to the slides for a couple of minutes and then we'll open it up for discussion."

> **[Click → Slide 5 (Angular use case)]**

---

## SLIDE 5 — ANGULAR USE CASE (1 min)

**SAY:**

"Quick recap on why Angular is the right starting point for a pilot. Three reasons:

One — **hard deadline.** Angular 14 has been end-of-life since November 2023. Every month on an unsupported framework is compliance exposure.

Two — **fully verifiable.** The build must pass. The tests must pass. There's no subjective judgment needed — either it works or it doesn't. That makes it the easiest use case to measure.

Three — **parallelisable.** Once the first migration works, you run the same playbook across your fleet.

After the pilot proves the model, security remediation and compliance test coverage are natural expands — same platform, same workflow, different use case."

> **[Click → Slide 6]**

---

## SLIDE 6 — PILOT DESIGN / NEXT STEPS (5 min)

**SAY:**

"Here's what I'd propose.

**Step one** — pick one Angular app. Ideally one with good test coverage so we can verify results cleanly. I'll work with your team to configure Devin's knowledge and playbook for your specific codebase patterns.

**Step two** — we run a two-week sprint with agreed success metrics. Time to merge, PR review quality, test pass rate. I'm embedded with your team during this — I'm not handing you a tool and disappearing.

**Step three** — we measure the results and decide whether to expand. Angular fleet, then security remediation, then compliance coverage.

A few things on the security side since I know that matters here:"

> **[Point to the three bullet points]**

"Devin never auto-merges to production. Every output is a PR that goes through your existing review process — branch protections, required reviewers, all of it still applies.

SOC 2 Type II certified. VPC deployment option — your code never has to leave your network. SAML SSO, RBAC, enterprise audit logs. And for enterprise customers — your code is never used for training. That's contractual."

---

## DISCUSSION / Q&A (10 min)

### Likely questions and how to handle them

**Q: "How is this different from GitHub Copilot?"**

**SAY:** "Copilot sits inside your IDE and suggests the next line while you're typing. You're still driving. It's an incremental productivity gain — maybe 10–20%. Devin is fundamentally different. You give it a task and it goes and does it — in its own VM, with its own shell and browser. It plans, codes, tests, and ships. Your engineer reviews the PR. That's an 8–40× time savings, not a 20% autocomplete boost. They solve different problems."

**Q: "What happens when Devin gets stuck or writes bad code?"**

**SAY:** "Two things. First — Devin iterates. If tests fail, it reads the failure output, fixes the code, and re-runs. It doesn't just give up. Second — when it genuinely can't resolve something, it flags it as low-confidence and stops. It never pushes code it's not confident in without telling you. And you can pause any session at any point and take over in the IDE. It's not a black box — there's full transparency into every step."

**Q: "What about data security? Our code can't leave the network."**

**SAY:** "Understood. Three options. Default SaaS with SOC 2 controls — each session in an isolated VM, data encrypted in transit and at rest, ephemeral by default. Second — VPC deployment — Devin runs inside your cloud, code never leaves your network. Third — self-hosted for the most restrictive environments. Enterprise customers also get contractual guarantees that code is never used for model training. All output IP is yours."

**Q: "Can it work with our internal tools / private packages?"**

**SAY:** "Yes. Two ways. First — Devin has a Secrets feature for credentials, so it can authenticate to your private registries and internal APIs. Second — MCP integrations. Devin connects to Datadog, Sentry, databases, Figma, Notion — and you can build custom MCP servers for internal tools. So if you have an internal deployment CLI or a custom testing framework, Devin can use it."

**Q: "What's the pricing model?"**

**SAY:** "Enterprise pricing is based on ACU consumption — Agent Compute Units. It scales with usage, not seat count. For a pilot, we'd scope it to a specific repo and use case so the cost is bounded and predictable. Happy to connect you with the team to walk through the specifics."

**Q: "How does this compare to [Cursor / Windsurf / Claude Code]?"**

**SAY:** "Those are IDE-centric tools — they make individual developers faster in their editor. Devin is a different category. It's an autonomous agent that works independently — in its own environment, on its own compute. The difference is: those tools require an engineer in the loop the entire time. Devin requires an engineer at the end to review the PR. That's a structural difference, not a feature difference. For fleet-scale work like migrating 30 repos in parallel, the IDE model doesn't work — you need autonomous agents.

Fun fact: Cognition acquired Windsurf, and it's now Devin Desktop. So you actually get both — the IDE copilot experience AND the autonomous agent. But for this conversation, the autonomous agent is what solves your migration and remediation problem."

---

## APPENDIX SLIDES — Use on demand

Only pull these up if the conversation goes there:

- **Slide 8 (ROI Model):** If they ask about cost justification → "Let me show you the math"
- **Slide 9 (Cloud Migration):** If they ask about cloud modernization → "Devin accelerates the code transformation after your architects set the target"
- **Slide 10 (Proof Points):** If they want more customer evidence → "Here's the detail on Itaú and Nubank"
- **Slide 11 (Compliance):** If they mention OCC / test coverage gaps → "This is the natural expand"
- **Slide 12 (Security):** If security team asks detailed questions → "Let me walk through the architecture"

---

## POST-MEETING (within 1 hour)

1. **Send follow-up email** with:
   - Summary of what you heard in discovery (2–3 bullet points)
   - Proposed pilot scope: one repo, 2-week sprint, specific metrics
   - Link to the deck for reference
   - Security whitepaper / trust center link
   - Clear next step with a date

2. **Update CRM** with:
   - Discovery findings
   - Competitive intel (what tools they mentioned)
   - Decision-making process / who else needs to be involved
   - Technical blockers identified
   - Proposed pilot timeline

3. **Internal sync** — share notes with your AE on what resonated and what objections came up

---

## DEMO CRAFT REMINDERS (from DE Skills Framework)

- **Discovery shapes the demo, not the other way around.** Whatever pain they shared in discovery → reference it when you show the relevant feature. "Remember you mentioned your remediation backlog is growing? This is exactly where automations fit."

- **Handle skepticism with transparency, not deflection.** If someone asks a gotcha question, don't dodge. Acknowledge limitations honestly. "Can Devin re-architect your entire cloud infrastructure? No. Can it execute the code-level transformations 10× faster once your architects set the target design? That's exactly what it does."

- **Explain the agent loop, not just the output.** Don't just show the PR. Show WHY it works — the plan → code → test → iterate → verify loop. That's what separates this from "AI wrote some code."

- **Security is not a slide. It's a thread.** Weave security into every step: "each session runs in its own isolated VM" during the session demo, "never auto-merges" during the PR review, "code never used for training" during next steps. Don't save it all for the end.

- **Read the room.** If they're leaning in on security remediation, spend more time on automations and less on Angular. If they're skeptical, slow down and go deeper on one feature instead of speed-running all seven. The agenda on the slide is a suggestion, not a script.

- **End with a clear ask.** Don't end with "any questions?" End with: "Can we identify a pilot repo and schedule a kickoff call with the engineering team next week?"
