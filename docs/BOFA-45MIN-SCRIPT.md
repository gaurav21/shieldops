# BofA × Devin — 45-Minute Meeting Script

**Audience:** VP-level engineering & technology leaders at Bank of America
**Goal:** Secure a 2-week pilot commitment on one Angular repo
**Structure:** 20 min pitch + discovery → 15 min live demo → 10 min close + Q&A

---

## PHASE 1: PITCH + DISCOVERY (20 minutes)

---

### 0:00–1:30 — Opening (Slide #0: Title)

> "Thank you for the time. I want to make this 45 minutes count, so here's the format: I'll spend a few minutes on what we've researched about BofA's priorities, validate that with you, then do a live demo — not slides pretending to be a demo — tailored to exactly what matters to your team. Then we'll talk next steps.
>
> Sound good? Great."

**💡 No fluff. Straight to structure. VPs respect people who respect their time.**

---

### 1:30–4:30 — The Cognition Elevator Pitch (Slide #1: Built for Regulated Industries)

> "So — who is Cognition and why should you care?
>
> We built Devin, the world's first AI software engineer. Not a copilot. Not autocomplete. A fully autonomous engineer that takes a task, plans the approach, writes the code, runs the tests, and opens a PR — all inside its own isolated cloud VM.
>
> Three things matter for BofA specifically:
>
> **First — we're already inside the banks.** Goldman Sachs, Citi, Itaú, Nubank — all running Devin in production. SOC 2 Type II certified. Zero data retention with LLM providers. Your code never leaves your network if you choose VPC deployment. This isn't a startup hoping to get into financial services — we're already there.
>
> **Second — Devin has its own computer.** This is the fundamental difference. Copilot and Cursor suggest code inside your developer's IDE. Devin runs in a full Linux VM — it has a shell, a browser, a file system, an IDE. It can install Angular CLI, run `ng build`, spin up the frontend, and visually verify the UI didn't break. No other AI coding tool can do that. When I show you the demo, you'll see it click through your application in a real browser.
>
> **Third — we're model-independent.** Devin routes each sub-task to the best AI model available. Planning goes to one model, coding to another, computer use to another. The AI frontier shifts every six months. With Copilot, you're locked to OpenAI. With us, your investment is future-proof.
>
> We're valued at $26 billion. But honestly — what matters is the results. Itaú saw 6× faster migrations. Nubank saw 20× cost savings. AHEAD saw 8-40× time savings. Let me show you why those numbers are real."

**💡 This pitch does three things: (1) establishes category leadership, (2) explains the technical moat in business terms, (3) drops peer proof. All in 3 minutes.**

---

### 4:30–8:00 — Research & What We Know (Slide #2: What We Know About BofA)

> "Before I show you anything, I want to share what we've researched about Bank of America — and I want you to tell me where we're right and where we're wrong.
>
> BofA runs a $13.5 billion technology budget. Roughly $4 billion — about 30% — is carved out for new strategic initiatives, including AI. That's grown 44% over the past decade.
>
> Hari Gopalkrishnan was promoted to CTIO mid-2025. His stated strategy is moving away from individual teams building one-off applications toward enterprise-wide reusable capabilities — across roughly 3,000 business processes. And his own framing of the challenge is telling: *'If you overdo governance, you stall innovation.'*
>
> That governance-versus-velocity tension? That's exactly where Devin fits. Every change Devin makes is a human-reviewed PR. Cited code, confidence scores, full rationale. You scale engineering throughput without loosening control."

*Pivot to right column — the three discovered areas:*

> "From our previous conversations, we've identified three areas where Devin maps to your priorities:
>
> **Angular migration** — customer-facing apps still on Angular 14, which has been end-of-life since November 2023. Your teams estimate 6 to 8 dev-weeks per app to migrate manually.
>
> **Security remediation** — the perpetual SonarQube and Veracode backlog. Every finding that sits in the queue is developer capacity not going toward innovation.
>
> **OCC compliance** — test coverage gaps on compliance-critical code paths. I understand examiner readiness is a board-level concern.
>
> Does that match what you're seeing? Anything I'm missing?"

**💡 Stop talking here. Let them react. This is your first discovery moment.**

---

### 🔍 ANGULAR DISCOVERY (8:00–14:00)

> "Great. I want to go deeper on the Angular migration specifically, because that's where we think the pilot makes the most sense — and it's what I'll demo today."

**Question 1 — Scale & Business Exposure**
> "How many Angular 14 applications are we talking about? And are these customer-facing digital banking, internal tooling, or a mix?"

*Listen. Then:*
> "And what's the real cost of staying on v14? Is it showing up in compliance conversations yet, or is it still an engineering backlog concern?"

**💡 Listening for:** Number of apps = deal size. Customer-facing = urgency. Compliance pressure = executive sponsor activation.

**Question 2 — What's Blocked Progress**
> "What's stopped the migration so far? Capacity — not enough hands? Complexity — too much regression risk? Or prioritization — it keeps getting bumped by feature work?"

*Respond based on answer:*

- **Capacity:** "That's the pattern. Itaú had 59 services to migrate. Same problem — not enough senior engineers. Devin ran them at 6× the speed. Your engineers reviewed the PRs instead of writing the code."
- **Complexity/Risk:** "Makes sense. The regression risk is real, especially on customer-facing apps. That's why Devin's approach matters — it runs the build, runs the tests, and spins up the frontend to visually verify nothing broke. I'll show you exactly that in the demo."
- **Prioritization:** "Which tells me the cost hasn't crossed the threshold yet. But here's the math: if you can clear 10 repos in the time it takes to manually do one, migration goes from a multi-quarter initiative to a sprint. It stops competing with feature work."

**Question 3 — Current AI Tooling**
> "What AI coding tools are your teams using today?"

*Then:*
> "The key difference: those tools help your engineers write code faster. Devin does the migration *for* them. It takes the ticket, reads the codebase, makes every change, runs the build, opens the PR. Your engineers spend 10 minutes reviewing instead of 6 weeks writing."

**Question 4 — Success Criteria**
> "If we ran a pilot on one repo — what would make it a clear win for your team?"

*Write down exactly what they say. This becomes the pilot contract.*

---

### 14:00–16:00 — Business Impact Framing (Slide #3: Angular — Business Impact)

> "Let me put some numbers around this.
>
> *[Point to stats]* Manual effort: 6 to 8 dev-weeks per app. With Devin: hours. And Devin runs 10+ repos in parallel — simultaneously, in isolated VMs.
>
> What that means for BofA:
>
> **Compliance** — you eliminate EOL exposure before the next OCC review cycle. That's not a nice-to-have, that's risk reduction.
>
> **Capacity** — your senior Angular engineers come off migration duty and go back to the $4 billion innovation budget. That's Gopalkrishnan's reusable-capability mandate, accelerated.
>
> **Speed** — the entire Angular backlog cleared in weeks, not quarters. This stops being a multi-quarter program and becomes a sprint.
>
> **Governance** — and critically, nothing about your governance changes. Every change is a PR. Branch protections, required reviewers, same approval process. Devin works inside your framework, not around it.
>
> Let me show you what this looks like live."

---

### 16:00–18:00 — Demo Setup (Slide: Demo Transition)

> "I'm going to kick off a Devin session right now on a real Angular 14 codebase. This is live — no recordings, no pre-baked outputs.
>
> While it runs, I'll walk you through the interface and show you four things:
> 1. How Devin understands a codebase before writing any code
> 2. The actual Angular migration — every file, every test
> 3. How it builds institutional knowledge in a Wiki that your whole team can use
> 4. Something no other AI tool can do — visual UI testing in a real browser"

*Kick off the Devin session*

---

## PHASE 2: LIVE DEMO (15 minutes)

---

### 18:00–20:00 — Devin Interface + ASK (2 min)

> "While Devin starts working, let me orient you on the interface.
>
> On the left is the conversation — this is what we call ASK. You talk to Devin like you'd brief an engineer. Not prompts, not templates — natural language. 'Migrate this Angular 14 app to v17. Run the build and tests. Open a PR when green.'
>
> On the right is Devin's workspace — its own IDE, terminal, browser. You can see everything it's doing in real-time. Full transparency.
>
> ASK is also how your team interacts day-to-day. Engineers can ask Devin questions about the codebase, debug issues together, or hand off tasks. It's not a black box — it's a collaborative interface."

**💡 VP hook:** "Think of ASK as how your team delegates work to Devin — same way you'd delegate to a junior engineer, except it works 24/7 and runs 10 things in parallel."

---

### 20:00–27:00 — Angular Migration Live (7 min)

Walk through the session as Devin works:

> "So Devin is reading the codebase right now. Watch — it's identifying every Angular 14 pattern that needs to change. It's not using a generic template. It's reading *this specific codebase* and making the right changes for *this code*.
>
> *[As changes appear]* See here — it's converting NgModule declarations to standalone components, updating the Material imports, replacing deprecated RxJS operators. Every file, every import, every template reference.
>
> *[When build runs]* Now it's running `ng build --production`. This is the moment of truth. If this fails — and sometimes it does — watch what happens next."

*If build fails:*
> "See that? Build failure. But Devin doesn't stop. It reads the error output, understands what broke, and fixes it. This is the iteration loop that replaces 6 weeks of manual work. A human would read this error, go look at the file, figure out the fix, run the build again. Devin does that in seconds."

*When build passes:*
> "Green build. Now it runs the test suite. Same loop — if tests fail, it fixes and re-runs.
>
> *[When PR opens]* And here's the PR. Full diff, cited rationale for every change, test results attached. This is what your engineer reviews. 10 minutes of code review instead of 6 weeks of migration work."

**💡 VP moment:**
> "What just happened in *[X]* minutes — your team would estimate at 6 to 8 weeks. Now multiply that by however many Angular apps you have. That's the capacity unlock."

---

### 27:00–30:00 — Wiki: Institutional Knowledge (3 min)

> "Now let me show you something that matters a lot for an organization at BofA's scale — the Wiki.
>
> *[Navigate to Wiki]* As Devin works on your codebase, it automatically builds documentation — architecture decisions, patterns it discovered, dependency maps. This isn't generated docs that nobody reads. It's living institutional knowledge.
>
> Why does this matter? Because your mainframe COBOL developers are retiring. Your Angular experts are getting pulled onto new projects. The knowledge walks out the door. Devin captures it and makes it searchable for every engineer on the team.
>
> When the next developer — or the next Devin session — touches this codebase, it doesn't start from zero. It reads the Wiki first. That's compounding intelligence — every session makes the next one faster."

**💡 VP hook:** "This directly addresses the 'enterprise-wide reusable capability' mandate. The knowledge isn't locked in one engineer's head — it's in the system."

---

### 30:00–33:00 — Desktop / Video: Visual UI Testing (3 min)

> "Last thing — and this is the differentiator nobody else has.
>
> *[Show Devin's browser/desktop]* Devin spun up the frontend in its VM and is actually running the application. Watch — it's clicking through the UI, navigating between pages, filling in forms, verifying that the migration didn't break the user experience.
>
> *[Show video recording]* It records the entire session on video. You can play this back, share it with QA, attach it to the PR. Visual proof that the application still works.
>
> For customer-facing digital banking applications, this is critical. You can't ship a migration that changes how a login form renders or how a transaction flow works. Devin doesn't just verify the code compiles — it verifies the user experience is intact.
>
> Copilot can't do this. Cursor can't do this. Claude Code can't do this. They don't have a browser. They don't have a screen. Devin does — because it runs on a full computer, not inside your editor."

**💡 This is the mic-drop moment. Let it land. Pause after.**

---

## PHASE 3: CLOSE + NEXT STEPS (10 minutes)

---

### 33:00–36:00 — Itaú Proof Point + Why Devin (Slides #6–7)

> "Quick proof point before we talk next steps.
>
> Itaú Unibanco — $500 billion in assets, 100,000 employees, one of the most regulated banks in the world. They deployed Devin for migration and security remediation:
>
> - 59 services migrated .NET to Java — 6× faster
> - 800 database objects migrated — 5× faster
> - 70% of security vulnerabilities auto-resolved
> - Test coverage went from 50% to over 90%
>
> Same regulatory environment as BofA. Same complexity. Same need for auditable changes. The model is proven.

*Advance to competitive slide:*

> "If you're evaluating alternatives — the honest comparison:
>
> **Model independence** — we route to the best model. Copilot is locked to OpenAI. The frontier shifts constantly.
>
> **Full computer** — other tools run in containers. No browser, no visual testing, no end-to-end verification.
>
> **Transformation partner** — I'm not handing you a license. I'm embedded in your org. I configure Devin's Knowledge and Playbooks for your codebase, your patterns, your CI/CD. That's the deployment model."

---

### 36:00–38:00 — Security (Slide #8)

> "I know this will come up in procurement, so let me address it now.
>
> Each Devin session runs in its own isolated VM — not a container, a full virtual machine. Every session is ephemeral — spun up, used, destroyed.
>
> VPC deployment option — code never leaves your network. SOC 2 Type II certified. Code is never used for training — contractual, not just policy. Every change goes through your existing PR review process — branch protections, required reviewers. Your governance doesn't change."

---

### 38:00–43:00 — Next Steps & Pilot Proposal (Slide #9)

> "Here's what I'd propose — and I want to be prescriptive about this.
>
> **Step one:** Pick one Angular 14 repo. Ideally something your team has already estimated manually — so we can measure the delta objectively.
>
> **Step two:** Two-week sprint. We agree on success metrics upfront — *[reference what they said during discovery]*. Devin migrates it end-to-end. Your engineers review the PRs.
>
> **Step three:** If the results hold — and based on what we've seen at Itaú, Goldman, and Nubank, I'm confident they will — we expand. Angular fleet first. Then security remediation. Then compliance test coverage. That's the land-and-expand path that doesn't require you to bet big on day one.
>
> Three questions for you:"

**Closing Discovery:**
> "**One** — what repo would make sense for the pilot? Ideally customer-facing, medium complexity — something that represents the fleet.
>
> **Two** — who else needs to be in the room to greenlight a pilot? If there's a security review or procurement process, let's get ahead of it now.
>
> **Three** — what's the timeline? When's the next OCC review cycle? I want to make sure we have results before then."

*If they push back on timing:*
> "I get it. But here's the math — every month on Angular 14 is compliance exposure. The pilot is two weeks with minimal engineering lift from your side. The risk of doing nothing is higher than the risk of trying."

---

### 43:00–45:00 — Q&A Buffer

> "What questions do you have? I have backup slides on ROI modeling, cloud migration use cases, compliance coverage, and the full security architecture — happy to go deep on anything."

*Use appendix slides (10–15) as needed.*

---

## CHEAT SHEET — Objection Handling

| Objection | Response |
|-----------|----------|
| **"We already have Copilot"** | "Keep it. Copilot helps engineers write code faster. Devin does the migration *for* them. Different capability — additive, not competitive." |
| **"How do we know PRs are good?"** | "67% merge rate, up from 34% last year. And your engineers review every PR — same process as any human engineer's work." |
| **"What about hallucinations?"** | "Devin runs the build and tests. If they fail, it fixes and re-runs. It also spins up the UI and visually verifies. The validation is end-to-end — not just 'does the code look right.'" |
| **"Security — code leaving network"** | "VPC deployment. Code never leaves your network. SOC 2 Type II. Zero training on your data. Contractual." |
| **"Need to evaluate other vendors"** | "Encourage it. Ask every vendor two questions: can it run the build? Can it open a browser and verify the UI? That's the test." |
| **"Not the right time"** | "Every month on Angular 14 is compliance exposure. The pilot is 2 weeks, minimal lift from your team. When does the next OCC cycle start?" |
| **"Need more stakeholders"** | "Who should be in the room? I'll tailor the next session — security team gets the architecture deep-dive, engineering leads get the hands-on demo." |
| **"What about COBOL?"** | "That's the expand path. Mercedes-Benz: 8-month COBOL modernization compressed to 8 days in a pilot. Synechron embeds Devin specifically for COBOL modernization at major banks. Angular proves the model — then we go after mainframe." |

---

## DEMO FLOW CHECKLIST

Before the meeting, have ready:
- [ ] Angular 14 demo repo loaded in Devin workspace
- [ ] Devin session pre-configured with repo access
- [ ] Pre-completed session as backup (in case live demo stalls)
- [ ] Wiki populated from a previous run (to show institutional knowledge)

**Demo sequence:**
1. **ASK** — type the migration prompt live, show conversational interface
2. **Migration** — Devin reads codebase, makes changes, runs build/tests
3. **Wiki** — show auto-generated documentation from codebase analysis
4. **Desktop/Video** — Devin opens browser, clicks through UI, records video proof

**If demo stalls or takes too long:**
> "Let me show you a completed session from an earlier run — same codebase, same migration. I want to respect your time and show you the full output rather than watch a progress bar."

Switch to pre-completed session. Never apologize for AI timing — reframe as "this is realistic, it takes X minutes for a task that takes humans Y weeks."

---

## TIMING GUARDRAILS

| Segment | Allocated | Hard Stop |
|---------|-----------|-----------|
| Opening | 1.5 min | 1:30 |
| Cognition elevator pitch | 3 min | 4:30 |
| Research + validation | 3.5 min | 8:00 |
| Angular discovery | 6 min | 14:00 |
| Business impact + demo setup | 4 min | 18:00 |
| **Demo: ASK + interface** | **2 min** | **20:00** |
| **Demo: Angular migration** | **7 min** | **27:00** |
| **Demo: Wiki** | **3 min** | **30:00** |
| **Demo: Desktop/video** | **3 min** | **33:00** |
| Itaú + Why Devin + Security | 5 min | 38:00 |
| Next steps + closing discovery | 5 min | 43:00 |
| Q&A buffer | 2 min | 45:00 |

**If running long on discovery (good sign):** Compress Itaú to 60 seconds ("Itaú — $500B bank, 59 migrations at 6×, 70% vulns auto-resolved. Same environment as BofA."). Skip competitive slide. Go straight to next steps.

**If demo runs fast (great sign):** Use extra time to go deeper on Wiki and show how Knowledge compounds across sessions. Or pull up the security architecture slide live.

---

## KEY PHRASES TO LAND

These are the lines that stick with VPs after the meeting:

- *"6 to 8 weeks of manual work — done in hours."*
- *"Your engineers review PRs instead of writing migration code."*
- *"Every month on Angular 14 is compliance exposure."*
- *"Devin works inside your governance framework, not around it."*
- *"The $4 billion innovation budget should fund innovation — not keep the lights on."*
- *"Copilot suggests code. Devin does the work."*
- *"It runs the build, runs the tests, opens the browser, and verifies the UI. No other tool does that."*
- *"Your peers are already here — Goldman, Citi, Itaú, Nubank."*
