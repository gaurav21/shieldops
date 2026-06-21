# IOH Talk Track — 40-Minute Presentation

## How to Use This

- **~4 min per slide** — don't rush, this is a conversation not a lecture
- **Bold text** = key phrases to hit naturally
- **[PAUSE]** = deliberate beat, let it land
- **[CLICK]** = advance to next slide
- Hindsight callouts on each slide are there for a reason — weave them into your narration when they feel natural, or save them for Q&A ammunition

---

## Slide 1 · Title (30 seconds)

> "This is the story of how we won **Indosat Ooredoo Hutchison** — Indonesia's second-largest telco, 95 million subscribers — with a **16-module Datadog deployment** across their entire hybrid estate. Full-stack observability and embedded DevSecOps."

> "I'll walk you through the architecture, the technical decisions, and — honestly — what I'd do differently."

**[CLICK]**

---

## Slide 2 · Customer + Challenge (~4 min)

> "Context first. IOH is the result of a **$6 billion merger** between Indosat and Tri. Their stated ambition: become an **AI Technology Company**."

> "But the reality on the ground was... messy. Post-merger, they had **three cloud providers** — AWS, GCP, Azure — plus on-prem data centres. **Four database engines.** Legacy middleware like Siebel and Tibco. Jenkins and GitLab CI running in parallel. And — critically — **zero correlated telemetry.**"

> "Every Sev1 was a fire drill. MTTR was measured in **hours**, not minutes. Different teams used different tools for different layers. The infrastructure team couldn't see what the app team saw. Security was bolted on after the fact, if at all."

> "That's the environment I walked into."

**If asked about the hindsight:** "One thing I'd do differently — I should have aligned with their internal IS function earlier. They controlled procurement timelines and I underestimated how much influence they had on the decision process. We were engaging the platform engineering team while IS was running a parallel evaluation track."

**[CLICK]**

---

## Slide 3 · My Role + MEDDIC (~4 min)

> "My role: I was the **Datadog-side technical lead and executive sponsor**. I owned the win strategy, the solution architecture, and the CIO relationship. Every major technical decision in this talk was mine."

> "Execution was partner-led — **PT MII**, Datadog's Advanced Partner in Indonesia, handled the hands-on instrumentation. IOH's managed services team would operate it day-to-day. I architected and strategised."

**[Gesture to MEDDIC grid]**

> "Let me walk through how we qualified this deal."

> "**Metrics** — MTTR from hours to under 15 minutes. We estimated **$2.1 million in annual outage costs** at their subscriber scale. AI root cause in under a minute. And zero critical vulnerabilities reaching production."

> "**Economic Buyer** — the CIO. Post-merger mandate: consolidate fragmented tooling, reduce operational risk, and position IOH as an AI Tech Company."

> "**Decision Criteria** — they needed a single pane across hybrid infrastructure, embedded DevSecOps in the pipeline, ServiceNow integration, and AI-powered root cause analysis."

> "**Pain** — reactive operations, no signal correlation, and Sev1 incidents that directly translated to revenue loss at telco scale."

> "**Champion** — the VP of Platform Engineering. He drove internal alignment and wanted to prove autonomous operations for a TM Forum Catalyst submission. He validated our architecture decisions internally."

**If asked about the hindsight:** "Honestly, those metrics — the MTTR target, the outage cost — were assumptions early on. I should have benchmarked them with IOH's actual incident data before the proposal. We got lucky that the numbers held up, but it could have been a credibility risk."

**[CLICK]**

---

## Slide 4 · Solution Architecture (~5 min)

> "This is the architecture we designed — and this is the slide I'd spend the most time on if I were explaining this to a technical audience."

**[Walk through each layer top to bottom]**

> "**Top layer: IOH's hybrid environment.** Bare metal, VMs, Kubernetes on-prem, plus three clouds — AWS with EC2, EKS, Lambda; GCP with GKE and Cloud Run; Azure with AKS and VM Scale Sets. Databases across all of them — Oracle, PostgreSQL, MySQL, Redis. Network devices via SNMP. And browser/mobile endpoints."

> "**Collection layer.** Datadog Agent v7+ on hosts. Cluster Agent plus DaemonSet on Kubernetes — the Cluster Agent is important because it centralises metadata and reduces API Server load. RUM SDK for browsers. Native cloud integrations. And we kept the door open for **OpenTelemetry** where needed."

> "**CI/CD layer.** GitLab CI and Jenkins for pipelines. Argo CD and Flux for GitOps deployments. Datadog Pipeline Visibility and Workflow Automation sitting on top."

> "**Secure transport.** Everything over HTTPS 443. AWS PrivateLink for AWS workloads, Azure Private Endpoint, GCP Private Service Connect. For air-gapped segments, an optional Private Agent Gateway on TCP 10516."

> "**The Datadog platform itself** — 12 modules visible here: Infrastructure, APM Enterprise, Log Management, NPM/NDM, RUM, Session Replay, Synthetics, DBM, Bits AI SRE, SAST/SCA, IAST/RASP, and Workflow Automation. **16 modules total** when you count sub-capabilities."

> "**Consumers** — IOH SRE and NOC, DevOps teams, security team, management dashboards, and ServiceNow as the ITSM backbone."

> "The key architectural principle: **one platform, one trace ID, across every signal.** Metrics, traces, logs, security findings, user sessions — all correlated. That's not a feature list, that's a design decision."

**If asked about the hindsight:** "16 modules is a lot to land. Phased rollout was absolutely the right call. But I should have insisted on **adoption gates** — not just deployment gates — from Phase 1. Deploying a module is easy. Getting the ops team to actually use it is the real work."

**[CLICK]**

---

## Slide 5 · Infra + APM + DB + Logs (~4 min)

> "This slide covers the observability stack — the core of what we deployed."

> "**Infrastructure and Kubernetes.** Host agents on every VM. On Kubernetes, the Cluster Agent acts as a proxy between node agents and the Datadog backend — it centralises metadata, reduces API Server load, and manages auto-discovery for new pods. NDM via SNMP for network devices. **First time IOH had network and application telemetry correlated.**"

> "**APM Enterprise.** This was arguably the biggest win. Distributed tracing with a single trace ID following a request from Nginx through Tomcat to the database to external APIs. Service Map auto-discovered all dependencies. Continuous Profiler for code-level CPU and memory hotspots — zero overhead in production. Error Tracking auto-groups exceptions across services."

> "The key insight: **click a slow API response, see the database lock, see the container resource constraint, see the network blip.** Every signal connected by trace ID. IOH had APM before — but it couldn't do this correlation. Every signal was isolated."

> "**Database Monitoring** across four engines — Oracle, PostgreSQL, MySQL, Redis — plus managed cloud databases. Query-level performance, explain plans, lock analysis. The Cluster Agent ensures one agent per DB instance — no duplicates, no extra connections."

> "**Log Management** — multi-source ingestion from the Agent, Fluentd, CloudWatch, Pub/Sub, Event Hub. Grok parsers for custom formats. Every log carries `dd.trace_id`. Click a log, see the trace. Click a trace, see every log line. 7-day online retention plus archive."

**If asked about the hindsight:** "I should have triaged COTS instrumentability before the PoV. Siebel and Tibco are closed binaries — you can't inject a tracer. We figured that out mid-PoV and had to scope down. Lesson: be honest about what can and can't be instrumented upfront."

**[CLICK]**

---

## Slide 6 · RUM + Synthetics (~3 min)

> "User experience at 95 million subscribers."

> "**RUM — Real User Monitoring.** Browser SDK captures Core Web Vitals — LCP, FCP, CLS, INP. Error tracking, resource waterfall, performance segmented by geography, device, browser. **Real data from real users, not assumptions.**"

> "**Session Replay** — full session capture with privacy controls. You can reproduce a user-reported bug visually, then click through to the backend trace. Visual proof meets technical depth."

> "**Synthetics** — API tests and browser journeys running from global locations. SSL certificate expiry, DNS resolution, multi-step user flows. The key here: **proactive monitoring**. Catches outages before users report them."

> "The connection between these three is what matters. RUM tells you **what** users experience. Synthetics tells you what's broken **before** they complain. APM tells you **why**. Logs give you the detail. And they're all connected by one trace ID."

**If asked about the hindsight:** "I should have pushed for mobile SDK earlier. 95 million subscribers are overwhelmingly mobile-first. We led with browser RUM because it was easier to deploy, but the real user pain was in the mobile app experience. Mobile should have been Phase 1."

**[CLICK]**

---

## Slide 7 · DevSecOps + Security (~5 min)

> "This is where the deal got interesting — and where we differentiated from every other vendor in the evaluation."

**[Point to pipeline flow]**

> "The DevSecOps pipeline. Developer pushes code from their IDE — we have plugins for IntelliJ, VS Code, Cursor. Code goes to GitLab. **SAST and SCA** run as pipeline stages — static code analysis plus dependency vulnerability scanning."

> "Then the critical piece: **Datadog's policy engine evaluates the findings.** This is a gate. If there's a critical finding — the **pipeline stops**. It doesn't warn. It doesn't create a ticket and hope someone reads it. **It stops the build.**"

> "If it passes, GitLab builds and deploys via GitOps — Argo CD or Flux. In production, **IAST and RASP** provide runtime protection. IAST instruments the running application during testing. RASP blocks attacks in production — SQLi, XSS, SSRF, path traversal."

> "And when findings are detected at any stage, **ServiceNow tickets are auto-created**. Developer pushes a fix, re-scan passes, ticket auto-closes."

**[Point to four security layers]**

> "Four layers of application security, mapped to the software lifecycle. SAST at pre-commit. SCA at build-time. IAST during testing. RASP in production. **Continuous coverage from code to production.**"

> "The decision to embed security in the same platform as observability — **that was my recommendation.** IOH evaluated standalone SAST tools. My argument: one agent, one trace ID. A SAST finding should correlate to an APM trace which correlates to a RUM error. Security and observability on the same platform means you can go from 'we found a vulnerability' to 'here's the user impact' in one click."

**If asked about the hindsight:** "SAST false-positive rate was higher than expected initially. I should have set accuracy expectations proactively and had a tuning plan ready for the first 30 days. Instead, we were reactive to complaints. Lesson: when you're gating the pipeline on security findings, false positives aren't just noise — they stop deployments."

**[CLICK]**

---

## Slide 8 · RCA Decision + Closed Loop (~5 min)

> "This was the most important architecture decision in the entire engagement."

> "The proposal from one of the IOH teams: take a **general-purpose LLM**, give it Datadog access via MCP tool calls, have it query metrics, logs, and traces, and produce a root cause analysis in **45 seconds**."

> "The intent was right. The implementation had real gaps." 

**[Point to the four gap cards]**

> "**Not trained for RCA** — a general model can't distinguish root cause from correlated symptom. **No eval framework** — no accuracy target, no wrong-answer detection. If the model is confident and wrong, engineers go down the wrong path. **RAG doesn't equal reasoning** — retrieving a similar past incident is not the same as understanding this incident. And the **45-second claim was never benchmarked** — it was an assumption."

> [PAUSE]

> "My call: **don't build the agent. Build the system around one.**"

> "Use **Bits AI SRE** — purpose-built for observability, trained on over a trillion datapoints. Redirect the engineering effort to what genuinely needed to be custom-built."

**[Point to closed-loop architecture]**

> "This is the closed-loop architecture I designed. Eight steps."

> "**Detect** — Datadog Event Management correlates and deduplicates. **Ticket** — ServiceNow P1 auto-created with CMDB mapping. **Bits AI** — investigates across all signals, under one minute. **Root Cause** — finding posted as a structured work note. **Remediate** — DD Workflow fires, either auto-approved or human-gated. **Verify** — monitor confirms recovery. **Close Both** — Datadog alert and ServiceNow ticket resolved bidirectionally. **Learn** — outcome feeds back to tune accuracy."

> "The important detail: `sys_id` routes the finding to the exact ServiceNow ticket. `u_datadog_monitor_id` closes the exact Datadog alert. **Bidirectional — no orphaned tickets, no orphaned alerts.**"

> "The senior move on AI was not building the model — it was **owning the integration and governance around a validated one.**"

**If asked about the hindsight:** "The 45-second claim was never benchmarked by the proposing team. I could have used that gap more aggressively to reframe the architecture conversation earlier. Instead, I let it go through several rounds before I pushed back."

**[CLICK]**

---

## Slide 9 · ServiceNow + Automation + Adoption (~4 min)

> "This slide is about **operationalising** everything we built."

> "**ServiceNow integration — bidirectional, not just a webhook.** Datadog to ServiceNow: monitor triggers, webhook fires, incident created with severity mapped to priority, service mapped to CMDB CI. Custom fields for `u_datadog_monitor_id` and the Datadog URL. Deduplication — same alert updates the existing ticket, doesn't create a new one."

> "ServiceNow back to Datadog: ticket resolved, Business Rule fires, resolves the Datadog alert. Work notes sync both ways. **No orphaned tickets, no orphaned alerts.**"

> "And here's a decision I'm particularly proud of: **the same integration handles security tickets too.** SAST and SCA findings auto-create ServiceNow issues. Developer pushes a fix, re-scan passes, ticket auto-closes. Same bidirectional plumbing for both ops incidents and security findings. That reduced the integration surface by **50%**."

> "**Auto-remediation** — pre-approved playbooks for known failure modes. Restart service, scale pod, clear cache, rotate credentials. Approved upfront, executed at alert time. Every action audited and reversible. These workflows encode institutional knowledge."

> "That last point matters for IOH specifically. Their operations are **managed-services-led** — partner teams, subcontractors, follow-the-sun rotations. You can't rely on a single SRE who knows the system. The platform needs to remember what to do, even when the person on call has never seen this failure before."

> "**Three-year adoption ramp.** Phase 1: core infra plus APM. Phase 2: security plus RUM. Phase 3: AIOps plus full autonomy. Each phase has adoption gates — not just deployment gates. Because deploying a module doesn't mean anyone's using it."

**If asked about the hindsight:** "Workflow playbooks need ops team buy-in from day 1. We designed them with the platform team — but the managed services team who'd actually run them wasn't in the room early enough. They had their own processes and weren't thrilled about changing them."

**[CLICK]**

---

## Slide 10 · Outcome + Ask Me About (~3 min)

> "The outcome." [PAUSE]

> "**Multiple Closed-Won** — across three workstreams: Software Delivery Excellence, Operations, and Security."

> "Won the **observability partner seat** for the TM Forum Catalyst programme — which validated the architecture at an industry level."

> "**Expansion pipeline** into LLM Observability and Incident Response — the relationship is growing."

> "And Datadog is now positioned as the **single observability and security platform** for Indonesia's second-largest telco."

> [PAUSE]

> "Happy to go deeper on any of these — the architecture, the MEDDIC qualification, DevSecOps pipeline design, the RCA build-vs-buy decision, how the partner model worked, or the adoption strategy."

> "What would you like to dig into?"

---

# Potential Questions & Answers

## Architecture & Technical

### Q: "Why Datadog over competitors? What was the competitive landscape?"

**A:** "The main competitors were Dynatrace and a combination of open-source tools (Prometheus/Grafana + ELK + standalone SAST). Dynatrace is strong on APM but doesn't have embedded DevSecOps — they'd need a separate security toolchain. The open-source path was appealing on cost but terrifying on operational overhead for a managed-services team. Our differentiator was **one platform for both observability and security**, which meant one integration surface, one trace ID, and one team to manage it. At IOH's scale, reducing operational complexity was worth more than licensing savings."

### Q: "How did you handle the Kubernetes Cluster Agent architecture? Why not just DaemonSets?"

**A:** "DaemonSets alone work, but at scale they create noise. Every node agent independently polls the API Server for metadata — that's a lot of redundant traffic. The Cluster Agent centralises that: it gathers cluster-level metadata once, then distributes it to node agents. It also handles leader election for checks that should only run once per cluster — like kube_state_metrics. For IOH's multi-cluster environment across on-prem and three clouds, this reduced API Server load significantly and made monitoring more efficient."

### Q: "What about OpenTelemetry? Why not go OTel-native?"

**A:** "We kept OTel support via OTLP ingestion — so if IOH has services already instrumented with OpenTelemetry, those traces flow into Datadog. But going fully OTel-native would mean losing Continuous Profiler, auto-instrumentation, and some of the deeper integrations. The pragmatic choice was: Datadog tracers where we can, OTel where we must. IOH had too many technologies to bet on one instrumentation approach."

### Q: "How did you handle network monitoring for a telco?"

**A:** "NDM via SNMP for routers and switches — that gives device-level metrics. NPM for flow-level visibility between services and pods. DNS monitoring for resolution performance. The combination was important: NDM tells you the device is healthy, NPM tells you the traffic is flowing correctly, and when they disagree, that's where the problem is. For a telco, network issues are revenue issues, so having this correlated with application metrics was a first for IOH."

### Q: "Walk me through the database monitoring architecture."

**A:** "The key design principle: one agent monitors one database instance. The Cluster Agent ensures this — it assigns monitoring responsibilities and prevents duplicate connections, which matters for production databases where every connection counts. We covered four engines: Oracle, PostgreSQL, MySQL, Redis, plus managed cloud databases across AWS RDS, GCP Cloud SQL, and Azure Database. Query-level performance, explain plans, wait event analysis, lock detection — all correlated back to APM traces so you can go from 'this query is slow' to 'this API endpoint is affected' in one click."

### Q: "How does the Private Agent Gateway work for air-gapped segments?"

**A:** "Some of IOH's infrastructure can't reach the public internet directly — regulatory and security requirements. The Private Agent Gateway sits inside their network and acts as a proxy. Agents send telemetry to the gateway on TCP 10516, and the gateway forwards to Datadog's backend over HTTPS. It can also dual-ship — sending to both Datadog SaaS and a local store. For cloud workloads, we used PrivateLink/Private Endpoints instead, which keeps traffic entirely on the cloud provider's backbone."

---

## DevSecOps & Security

### Q: "What happens when SAST has too many false positives and blocks deployments?"

**A:** "This is exactly what happened initially — and it's in my hindsight callout. The enforcement gate is binary: critical finding = pipeline stops. When SAST false-positive rate is high, that means legitimate deployments are blocked. The fix is tuning: custom rulesets that reflect IOH's actual risk profile, suppression rules for known false positives, and a severity recalibration exercise. We should have had a 30-day tuning plan ready on day one. What we actually did was react to complaints, which cost us credibility with the dev team."

### Q: "How does RASP work without impacting application performance?"

**A:** "RASP runs inside the application runtime — it's the same agent and tracer that handles APM. It monitors request patterns and blocks known attack signatures (SQLi, XSS, SSRF, path traversal) at the application layer, not the network layer. The overhead is minimal because it's pattern matching on requests that are already being traced for APM. The key: we tested RASP in UAT/staging first before enabling blocking in production. In monitoring mode, it logs without blocking, so you can validate accuracy before turning on enforcement."

### Q: "Why embed security in the observability platform instead of using best-of-breed SAST/DAST tools?"

**A:** "Three reasons. First, **correlation**: a SAST finding in Datadog can be linked to the APM trace that exercises that code path, and to the RUM session where a user hit the vulnerable endpoint. Standalone SAST tools can't do that — they exist in isolation. Second, **integration surface**: one platform means one webhook to ServiceNow, one RBAC model, one SSO integration. With standalone tools, you're maintaining parallel integrations. Third, **developer experience**: developers are already in Datadog for APM and logs. Adding security findings to the same platform means they don't need to context-switch. The tradeoff: dedicated SAST tools may have deeper language-specific analysis. But for IOH's use case, the correlation advantage outweighed the depth advantage."

### Q: "How did you handle the ServiceNow integration technically?"

**A:** "Datadog to ServiceNow: webhook-triggered incident creation via the ServiceNow REST API. Field mapping — Datadog severity to ServiceNow priority, Datadog service tags to CMDB Configuration Items. Custom fields on the incident record: `u_datadog_monitor_id` stores the monitor ID, `u_datadog_url` links back to the investigation. Deduplication via monitor ID — if an alert fires for the same monitor, it updates the existing incident instead of creating a new one. ServiceNow to Datadog: a Business Rule on the incident table fires when status changes to Resolved, calling the Datadog API to resolve the corresponding alert. Work notes sync bidirectionally. The same integration handles security tickets — SAST/SCA findings create a different ticket type but use the same plumbing."

---

## RCA & AI

### Q: "Why not build a custom RCA agent? Aren't you limiting yourself to what Bits AI can do?"

**A:** "The question isn't whether a custom agent could eventually be better — it's whether the team had the infrastructure to build, evaluate, and maintain one reliably. Building an LLM agent for RCA requires: training data labelled with actual root causes (they didn't have this), an evaluation framework to measure accuracy (they didn't have this), a feedback loop to improve over time (they didn't have this), and an operational team to maintain it (they didn't have this). Bits AI SRE is purpose-built — trained on over a trillion observability datapoints. The ROI of building a custom agent that might reach 60% accuracy versus using a validated one at 85%+ accuracy is negative. The right call was to invest engineering effort in the **integration and governance** — the event routing, ticket creation, human-in-the-loop, and feedback loop — because that's what was genuinely custom to IOH."

### Q: "What if Bits AI gives a wrong root cause?"

**A:** "It will. Every AI system does. The architecture accounts for this. First, the finding is posted as a structured work note on the ServiceNow ticket — it's a recommendation, not an automated action. The on-call engineer reviews it. Second, for auto-remediation workflows, we have two tiers: pre-approved actions (restart, scale) that execute automatically, and sensitive actions (config changes, failovers) that require human approval. Third, the feedback loop: when an incident is resolved, the outcome is fed back to Bits AI — was the diagnosis correct? This tunes accuracy over time, specifically for IOH's topology. Wrong answers are expected; wrong answers without a correction mechanism are dangerous."

### Q: "How does Bits AI actually investigate? What data does it look at?"

**A:** "Bits AI SRE receives a trigger — typically an alert or anomaly detection event. It then queries across all correlated signals: infrastructure metrics (CPU, memory, disk, network), APM traces (latency, error rates, dependency maps), logs (error patterns, stack traces), network flows (NPM data), and recent changes (deploy events, config changes). It uses a combination of correlation analysis, dependency graph traversal, and learned patterns from similar incidents. The output is a structured finding: probable root cause, supporting evidence, confidence level, and recommended next steps. All of this happens in under a minute, which is the critical advantage over a human triaging across multiple dashboards."

---

## Deal Strategy & Soft Skills

### Q: "How did you work with the partner (PT MII) without disintermediating them?"

**A:** "This was a deliberate strategy. MII is Datadog's Advanced Partner in Indonesia — they have the relationship capital and local credibility that I don't. Disintermediating them would have been faster for some decisions, but it would have killed the deal. I positioned myself as the **technical authority** — architecture, product strategy, CIO-level conversations — while MII handled the implementation, commercial negotiation, and local project management. Clear swim lanes. When there were technical disagreements, I led. When there were relationship or process questions, MII led. The RACI model on slide 3 reflects this: I'm Consulted, MII Responsible, IOH Accountable."

### Q: "How did you handle stakeholder alignment across CIO, VP Platform Eng, and security?"

**A:** "Different messages for different audiences. For the CIO: **reactive to proactive operations**, with metrics in business terms (outage cost, MTTR, risk reduction). For the VP Platform Engineering (our champion): **autonomous operations and TM Forum Catalyst** — he wanted to showcase IOH's technical maturity at an industry level. For security: **shift-left without slowing down developers** — the enforcement gate was controversial but the argument was clear: would you rather find a critical vuln in prod or in the pipeline? The key was that our champion — the VP — carried our message internally to audiences we couldn't reach directly."

### Q: "What was the procurement process like? How long did it take?"

**A:** "Q4 2024 to Q2 2026. RFP, technical proposal, PoV (proof of value), commercial negotiation, and award. Multi-stakeholder: CIO office, SDE team, Operations, Security, and the IS function (which controlled procurement timelines — hence my hindsight about engaging them earlier). Partner-led procurement through MII, which simplified some of the commercial dynamics but added a coordination layer. The 3-year adoption ramp was part of the commercial structure — it de-risked the deal for IOH and gave us expansion opportunities."

### Q: "You mentioned a TM Forum Catalyst. What is that and why did it matter?"

**A:** "TM Forum is the telecom industry body — they run Catalyst projects where telcos showcase innovative approaches to common industry challenges. IOH wanted to submit a Catalyst demonstrating autonomous operations — detect, diagnose, remediate without human intervention. Winning the observability partner seat for this Catalyst was strategically important because it validated our architecture at an industry level and gave IOH's VP Platform Engineering a showcase for his team's work. It also created a reference that's valuable for other telco deals in the region."

### Q: "What's the expansion pipeline?"

**A:** "Two areas. **LLM Observability** — IOH is building AI-powered customer service and operations tools, and they need to monitor LLM performance, token usage, hallucination rates, and cost. We're positioned for this because we're already the observability platform. **Incident Response** — deeper integration between Bits AI SRE and ServiceNow for fully autonomous incident management, including auto-remediation for a broader set of scenarios. The relationship is growing because we delivered on the initial scope and earned trust."

---

## Adoption & Operations

### Q: "How do you measure adoption vs just deployment?"

**A:** "Deployment is 'the agent is installed.' Adoption is 'the ops team uses the dashboard during an incident instead of SSH-ing into the box.' We track adoption through: active dashboard views, monitor configurations created by IOH teams (not just us), mean time to acknowledge alerts, and — most importantly — whether ServiceNow tickets reference Datadog findings. If tickets still say 'manually investigated' instead of citing a Datadog root cause analysis, adoption hasn't happened yet. Each phase of the 3-year ramp should have adoption gates tied to these metrics. I should have pushed for this in Phase 1."

### Q: "How do you handle the overhead of agents at telco scale?"

**A:** "Every agent configuration was reviewed for overhead. CPU overhead target: under 1% for the host agent. APM tracer overhead: under 5ms per trace. We ran mandatory performance testing during the PoV to validate these numbers. In production, you have to be disciplined — debug logs off, profiler sampling configured appropriately, DogStatsD batching tuned. At 95 million subscribers, even small overhead multiplied across thousands of hosts adds up. The Cluster Agent helps here too — it reduces redundant API calls that would otherwise consume resources."

### Q: "What was the training plan for IOH's teams?"

**A:** "Structured training across three tiers: Platform administration (agent management, pipeline configuration, RBAC), Day-2 operations (dashboard usage, monitor creation, incident investigation with Datadog), and Advanced capabilities (APM trace analysis, custom metrics, workflow automation). MII delivered the hands-on training as part of their SI scope. But the real training is operational — the first few Sev1 incidents handled with Datadog instead of legacy tools is where adoption actually happens."

---

## Curveball / Stress-Test Questions

### Q: "What would you have done if the customer insisted on building the custom RCA agent?"

**A:** "I would have asked three questions: What's your accuracy target? How will you measure it? And what's your plan when the model is confidently wrong and sends engineers down the wrong path for 45 minutes? If they had good answers, I'd support it — and propose a parallel evaluation against Bits AI SRE with measurable criteria. If they didn't have good answers — which was the case — then my job is to redirect them to a path that actually works, even if it's not the most technically exciting one."

### Q: "Is this just a vendor lock-in play? 16 modules from one vendor?"

**A:** "Fair question. The counter-argument: what's the alternative? 16 different tools from 16 different vendors, each with their own agent, their own data silo, their own integration to ServiceNow? For a managed-services-led organisation, the operational overhead of that approach is worse than vendor concentration risk. We mitigated lock-in risk with OpenTelemetry support (OTLP ingestion), standard data formats, and contractual data portability. But I'll be honest — at 16 modules, switching costs are real. That's by design. The value has to justify the commitment, and so far it has."

### Q: "What's the biggest risk in this engagement going forward?"

**A:** "Adoption. The deployment is done, but **adoption is the product**. If the managed services teams revert to legacy workflows because the new ones feel unfamiliar, we've deployed 16 modules that nobody uses. The 3-year ramp exists for this reason, but it needs active guidance — training, champions within each team, and measurable adoption targets. The second risk: scope creep. IOH's estate keeps growing with the merger integration, and every new application is a potential instrumentation gap. We need a process for onboarding new services that's repeatable, not ad hoc."

### Q: "If you were doing this deal again from scratch, what's the one thing you'd change?"

**A:** "Engage the IS function from day one. We spent months building technical alignment with the platform engineering team and the CIO, but the IS function controlled procurement timelines and had their own evaluation criteria. We were nearly blindsided by a parallel workstream we didn't know about. In complex enterprise deals, technical win is necessary but not sufficient — you have to map the procurement process and engage every stakeholder, even the ones who seem administrative."

---

# What Went Well — Technical Capability Deep Dive

These are the things that worked and why. The hindsight callouts in the deck cover what I'd change — this section covers what I'd repeat.

## 1. Single Trace ID as the Architectural Foundation

The decision to anchor everything on **one trace ID across metrics, traces, logs, RUM sessions, and security findings** was the single most impactful technical choice. It meant:

- An APM trace ID shows up in every log line (`dd.trace_id`), every RUM session, every security finding.
- Engineers click from a slow API response → database lock → container resource constraint → network blip in one flow. No tab-switching, no mental correlation.
- When Bits AI SRE investigates, it traverses this same graph — it's not stitching together separate data stores.

**Why it worked:** IOH's previous tooling had APM in one place, logs in another, infra metrics in a third. The correlation gap wasn't a feature gap — it was an architecture problem. Solving it at the trace ID level meant every module we added automatically inherited correlation.

## 2. Cluster Agent Architecture for Kubernetes

The **Cluster Agent + DaemonSet** pattern was the right call at IOH's scale:

- **Reduced API Server load** — instead of every node agent independently polling for metadata, the Cluster Agent centralises it and distributes to node agents.
- **Leader election for singleton checks** — kube_state_metrics, external metrics, custom checks that should only run once per cluster.
- **Auto-discovery** — new pods get instrumented automatically. No manual config per deployment.
- **DBM coordination** — the Cluster Agent assigns one agent per database instance across the cluster. No duplicate connections, no duplicate metrics.

**Why it worked:** Multi-cluster (on-prem + EKS + GKE + AKS) meant the alternative — manual DaemonSet configs per cluster — would have been an operational nightmare. The Cluster Agent abstracted that away.

## 3. Embedded DevSecOps (Not Bolted On)

The decision to **embed SAST/SCA/IAST/RASP into the same platform as observability** — rather than using standalone security tools — created compounding advantages:

- **One agent** collects APM traces AND runtime security telemetry. No second agent, no second deployment.
- **SAST finding → APM trace → RUM error** — a vulnerability found in code can be linked to the production trace that exercises it, and to the user session that hit it. Standalone SAST tools can't do this.
- **One ServiceNow integration** for both ops incidents and security findings. Two ticket queues, same bidirectional plumbing. Cut integration surface by 50%.
- **Enforcement gate in CI/CD** — Datadog's policy engine evaluates SAST/SCA findings and blocks the GitLab pipeline on critical findings. Not a dashboard warning — a hard stop.

**Why it worked:** IOH evaluated standalone SAST/DAST tools. The argument that won: "your security team already lives in Datadog for incident investigation — adding security findings to the same platform means zero context-switching and automatic correlation to production impact."

## 4. Bits AI SRE Over Custom Agent

Choosing a **purpose-built AI system** over building a custom LLM agent was the most consequential architecture decision:

- **Accuracy from day one** — trained on 1T+ observability datapoints (verify figure), purpose-built for root cause analysis. A general LLM with MCP tool calls couldn't match this without months of fine-tuning and evaluation framework development.
- **Testable target** — Bits AI has measurable accuracy benchmarks. A custom agent would have been "we think it works" with no eval framework.
- **Credible TM Forum submission** — IOH's champion needed a validated, defensible AI capability for the Catalyst programme. "We built our own agent in 3 months" wouldn't have passed scrutiny.
- **Team effort redirected productively** — instead of building a model, the team built the **integration and governance layer**: event routing, ServiceNow bidirectional sync, human-in-the-loop approvals, feedback loops. That's where the genuinely custom work was.

**Why it worked:** The senior move on AI wasn't building the model — it was recognising that the model was a commodity and the integration/governance around it was the differentiator.

## 5. Closed-Loop Incident Architecture

The **8-step closed loop** (detect → ticket → diagnose → root cause → remediate → verify → close → learn) worked because of two technical details:

- **`sys_id` routing** — Bits AI's finding is posted to the exact ServiceNow ticket via the incident's `sys_id`. No ambiguity, no matching by title string.
- **`u_datadog_monitor_id` back-reference** — when ServiceNow resolves the ticket, the Business Rule uses this custom field to close the exact Datadog alert. Bidirectional, deterministic.
- **No orphans** — the same alert can't create duplicate tickets (deduplication by monitor ID), and a resolved ticket always closes its Datadog counterpart.

**Why it worked:** Previous ITSM integrations at IOH were one-way webhooks — Datadog → ServiceNow, fire and forget. Tickets stayed open after alerts resolved. Alerts stayed open after tickets closed. The bidirectional sync eliminated this entirely.

## 6. Secure Transport Design

The **multi-path egress architecture** addressed IOH's regulatory and security requirements without compromising telemetry flow:

- **HTTPS 443** as default for internet-reachable segments.
- **AWS PrivateLink** for AWS workloads — traffic stays on Amazon's backbone, never touches the public internet.
- **Azure Private Endpoint** and **GCP Private Service Connect** — same principle, per-cloud.
- **Private Agent Gateway** (TCP 10516) for air-gapped on-prem segments — agents send to an internal proxy, the proxy forwards to Datadog SaaS.

**Why it worked:** A telco handling 95M subscribers has regulatory obligations around data egress. Offering multiple transport paths — with private connectivity as the default for cloud workloads — de-risked the security conversation and avoided a multi-month InfoSec review that could have stalled deployment.

## 7. RUM + Synthetics Combination

Deploying **both RUM and Synthetics** (not just one) gave IOH two complementary signals:

- **RUM** = real user data. Actual Core Web Vitals from real devices, real networks, real geographies. This is ground truth — but it's reactive (you see problems after users hit them).
- **Synthetics** = proactive probes. API tests and browser journeys running from global locations on a schedule. Catches outages, SSL expiry, DNS failures, broken user flows **before any user reports them**.
- **Both linked to APM** — a synthetic test failure triggers the same investigation path as a RUM error. Trace ID connects them to the backend.

**Why it worked:** At 95M subscribers, even 30 seconds of downtime before detection is thousands of affected users. Synthetics bought IOH detection speed; RUM bought them accuracy. Together: fast detection + real user validation.

## 8. ServiceNow as Single ITSM Surface

Using **one ServiceNow integration for both observability incidents and security findings** was an architecture simplification that paid dividends:

- Same webhook, same field mapping, same Business Rules — just different ticket categories.
- Security teams and ops teams use the same ITSM workflows. No separate security ticketing system.
- Vulnerability lifecycle (found → ticketed → fixed → re-scanned → auto-closed) uses the same bidirectional sync as incident lifecycle.

**Why it worked:** IOH's managed services team was already trained on ServiceNow workflows. Adding a separate security ticketing tool would have meant separate training, separate integrations, separate SLAs. Consolidating onto one ITSM surface reduced operational overhead and adoption friction.

## 9. Phased 3-Year Adoption Ramp

The **phased rollout** (P1: Infra + APM → P2: Security + RUM → P3: AIOps + autonomy) was a technical risk mitigation strategy:

- **P1 establishes the data foundation** — you can't do AI-driven root cause analysis without correlated metrics, traces, and logs. P1 builds the data lake.
- **P2 adds security and user experience** — these depend on P1's instrumentation being stable and adopted.
- **P3 enables autonomy** — auto-remediation and Bits AI SRE only work when the underlying data is trusted and the team knows how to validate AI findings.

**Why it worked:** Deploying 16 modules simultaneously would have overwhelmed the ops team and created alert fatigue from day one. Phasing meant each module got proper tuning, threshold calibration, and team training before the next layer was added.

---

# Summary: Technical Capability Wins

| Capability | What Went Well | Compounding Effect |
|---|---|---|
| Single trace ID | Unified correlation across all signals | Every new module inherits correlation automatically |
| Cluster Agent | Scalable K8s monitoring, no duplicates | Multi-cluster across 4 environments, zero manual config |
| Embedded DevSecOps | One agent, one integration, one platform | 50% less integration surface, automatic security↔observability correlation |
| Bits AI SRE | Accuracy from day one, credible for TM Forum | Team effort redirected to genuinely custom integration work |
| Closed-loop incident | Deterministic routing via sys_id | Zero orphaned tickets/alerts, measurable MTTR |
| Secure transport | Multi-path egress, PrivateLink/PSC | De-risked InfoSec review, no deployment delays |
| RUM + Synthetics | Proactive + reactive user experience | Fast detection + real user validation |
| ServiceNow consolidation | One ITSM for ops + security | Lower adoption friction, unified workflow |
| Phased rollout | Data foundation → security → autonomy | Each phase builds trust for the next |
