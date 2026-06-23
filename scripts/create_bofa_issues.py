#!/usr/bin/env python3
"""
Create all 6 BofA demo GitHub Issues for ShieldOps extended task types.

Usage:
    python scripts/create_bofa_issues.py
    # or
    ./scripts/create_bofa_issues.py

Requires: gh CLI authenticated with appropriate repo access.
"""

import subprocess
import sys

ISSUES = [
    # ── UC1: Angular Migration ──────────────────────────────────────
    {
        "repo": "gaurav21/bofa-digital-banking-frontend",
        "title": "[CRITICAL] Angular 14 EOL — Upgrade to Angular 18",
        "label": "shieldops-migration",
        "body": """## Summary
Angular 14 reached End-of-Life in November 2023. The BofA Digital Banking Frontend is still running Angular 14.2.12, which means **zero security patches** for 18+ months. OCC examiners flagged this in the last audit cycle.

## Impact
- **Regulatory Risk**: OCC finding — unsupported framework in customer-facing banking application
- **Security Risk**: 12 known CVEs in Angular 14.x with no patches available
- **Technical Debt**: NgModules pattern blocks adoption of modern Angular features (signals, deferred views)

## Requirements
1. Upgrade from Angular 14.2.12 → Angular 18.x (latest stable)
2. Migrate NgModules → Standalone Components across all 47 feature modules
3. Update Angular Material from Legacy components to MDC-based
4. Update RxJS from v7.5 to v7.8+ (operator deprecations)
5. All 312 existing unit tests must continue to pass
6. Zero visual regressions in customer-facing flows (login, transfers, statements)

## Constraints
- Customer-facing application — zero downtime deployment required
- Must maintain IE11 polyfills until Q3 2026 (compliance requirement)
- No changes to API contracts — backend team is on a separate release cycle
- Mobile-responsive layouts must be preserved exactly

## Affected Paths
- `src/app/` — all feature modules (47 modules, ~180 components)
- `src/styles/` — Material theme customizations
- `angular.json` — build configuration
- `package.json` — dependency tree

## Acceptance Criteria
- [ ] Angular 18.x running in production build mode
- [ ] All NgModules converted to standalone components
- [ ] All MatLegacy* imports replaced with Mat* equivalents
- [ ] `ng build --configuration=production` succeeds with zero warnings
- [ ] `ng test` — all 312 tests pass
- [ ] Lighthouse performance score >= 85 (current: 88)
""",
    },
    {
        "repo": "gaurav21/bofa-digital-banking-frontend",
        "title": "[HIGH] Angular Material Legacy Migration",
        "label": "shieldops-migration",
        "body": """## Summary
Angular Material v15+ deprecated all `MatLegacy*` components in favor of MDC-based replacements. The BofA frontend uses 23 legacy Material components that will be removed in Angular 18.

## Impact
- **Build Breakage**: Angular 18 will not compile with legacy Material imports
- **Accessibility**: MDC-based components have improved WCAG 2.1 AA compliance
- **Visual**: MDC components have subtle styling differences that need QA review

## Components to Migrate
| Legacy Component | Replacement | Usage Count |
|---|---|---|
| MatLegacyButton | MatButton | 156 |
| MatLegacyInput | MatInput | 89 |
| MatLegacySelect | MatSelect | 34 |
| MatLegacyDialog | MatDialog | 21 |
| MatLegacyTable | MatTable | 18 |
| MatLegacyCheckbox | MatCheckbox | 15 |
| MatLegacyRadio | MatRadioButton | 12 |
| MatLegacySlideToggle | MatSlideToggle | 8 |
| MatLegacyPaginator | MatPaginator | 7 |
| MatLegacyTooltip | MatTooltip | 45 |

## Requirements
1. Replace ALL legacy Material imports with MDC equivalents
2. Update component selectors in all templates
3. Fix CSS overrides that depend on legacy Material DOM structure
4. Ensure WCAG 2.1 AA compliance is maintained or improved
5. Visual regression testing on all major flows

## Constraints
- Must be coordinated with Angular 18 upgrade (same release window)
- Custom theme variables may need updating for MDC density settings
- Third-party component libraries (ng-select, ngx-datepicker) may conflict
""",
    },

    # ── UC2: Cloud Migration ────────────────────────────────────────
    {
        "repo": "gaurav21/bofa-enterprise-services",
        "title": "[CRITICAL] Notification Service — Spring Boot to AWS Lambda Migration",
        "label": "shieldops-cloud-migration",
        "body": """## Summary
The Notification Service runs on Spring Boot 2.7 deployed on on-prem WebSphere. As part of BofA's cloud-first mandate, this service must migrate to AWS Lambda with API Gateway, reducing infrastructure cost by ~60% and improving scalability.

## Current Architecture
- **Runtime**: Spring Boot 2.7.18 on WebSphere Liberty 22.x
- **Database**: Oracle 19c (notification templates, delivery logs, preferences)
- **Messaging**: IBM MQ v9.3 (inbound notification triggers, outbound delivery events)
- **Auth**: LDAP (IBM Tivoli Directory Server)
- **Throughput**: ~50K notifications/day, peak 500/minute during statement cycles

## Target Architecture
- **Runtime**: AWS Lambda (Java 21 / GraalVM native-image)
- **API**: Amazon API Gateway (REST)
- **Database**: Amazon Aurora PostgreSQL 15 (Serverless v2)
- **Messaging**: Amazon SQS FIFO (notification triggers) + SNS (fan-out)
- **Auth**: Amazon Cognito (user pools + M2M via client credentials)
- **Monitoring**: CloudWatch + X-Ray distributed tracing

## Requirements
1. Migrate all 12 Spring Boot REST endpoints to Lambda handlers
2. Convert Spring DI patterns to Lambda handler + shared service layer
3. Replace IBM MQ consumers with SQS FIFO event sources
4. Migrate Oracle stored procedures to application logic + Aurora PostgreSQL
5. Replace LDAP auth with Cognito JWT validation
6. Maintain current SLAs: p99 < 200ms, availability > 99.95%

## Constraints
- **Message ordering MUST be preserved** — notification sequence matters for compliance
- Cold start budget: < 3 seconds (use provisioned concurrency for critical paths)
- Data residency: US-East-1 only (regulatory requirement)
- Dual-run period: 2 weeks minimum (both old and new systems processing in parallel)
- No data loss during migration — every notification must be delivered exactly once

## Risk Assessment
- **HIGH**: IBM MQ → SQS message ordering semantics differ significantly
- **MEDIUM**: Spring Boot dependency injection patterns don't map cleanly to Lambda
- **MEDIUM**: Oracle → PostgreSQL SQL dialect differences in stored procedures
- **LOW**: LDAP → Cognito (well-documented migration path)
""",
    },
    {
        "repo": "gaurav21/bofa-enterprise-services",
        "title": "[HIGH] Replace IBM MQ with SQS FIFO — Preserve Message Ordering",
        "label": "shieldops-cloud-migration",
        "body": """## Summary
IBM MQ v9.3 is used for inter-service messaging across 8 enterprise services. Migration to Amazon SQS FIFO must preserve strict message ordering guarantees required by banking regulations.

## Current IBM MQ Setup
- **Queue Manager**: BOFA.PROD.QM01
- **Queues**: 14 queues across 3 queue managers
- **Message Volume**: ~200K messages/day
- **Ordering**: Per-queue FIFO with correlation ID grouping
- **Transactions**: XA distributed transactions spanning MQ + Oracle
- **DLQ**: Backout queues with 3-retry policy

## Key Queues to Migrate
| IBM MQ Queue | Purpose | Ordering Req | Volume/day |
|---|---|---|---|
| NOTIF.TRIGGER.Q | Notification triggers | Strict per-customer | 50K |
| NOTIF.DELIVERY.Q | Delivery confirmations | Strict per-notification | 50K |
| AUDIT.EVENT.Q | Audit trail events | Strict global | 30K |
| ACCOUNT.UPDATE.Q | Account state changes | Strict per-account | 20K |
| PAYMENT.PROCESS.Q | Payment processing | Strict per-transaction | 15K |
| STATEMENT.GEN.Q | Statement generation | Batch ordering | 10K |
| ALERT.DISPATCH.Q | Real-time alerts | Best effort | 20K |
| REPORT.BATCH.Q | Batch report jobs | Batch ordering | 5K |

## SQS FIFO Migration Requirements
1. Map IBM MQ correlation IDs → SQS MessageGroupId for ordering
2. Implement exactly-once processing using MessageDeduplicationId
3. Handle poison messages: IBM MQ backout → SQS DLQ with redrive policy
4. Replace XA transactions with Outbox Pattern + idempotent consumers
5. Preserve message selectors using SQS message attributes
6. Implement dead-letter queue monitoring and alerting

## Constraints
- **ZERO message loss** — every message must be delivered and processed
- **Ordering guarantees** cannot be relaxed for compliance-critical queues
- SQS FIFO throughput: 300 msg/sec per MessageGroupId (sufficient for current load)
- Maximum message size: 256KB (IBM MQ supports 100MB — need chunking strategy for large payloads)
- Message retention: 14 days in SQS vs. unlimited in IBM MQ (adjust consumers accordingly)

## Testing Requirements
- Chaos testing: simulate SQS throttling, DLQ overflow
- Ordering verification: send 10K sequenced messages, verify receipt order
- Exactly-once verification: inject duplicate MessageDeduplicationIds
- Load testing: 3x peak volume sustained for 1 hour
""",
    },

    # ── UC3: Test Coverage ──────────────────────────────────────────
    {
        "repo": "gaurav21/bofa-enterprise-services",
        "title": "[CRITICAL] OCC Exam Prep — Test Coverage for Compliance-Critical Paths",
        "label": "shieldops-coverage",
        "body": """## Summary
OCC examiners require evidence of test coverage for all compliance-critical code paths. Current coverage for the Enterprise Services monorepo is **34%** overall, with several critical paths at **0% coverage**. The next OCC examination is in 8 weeks.

## Current State
- **Overall Coverage**: 34% line, 22% branch
- **Compliance Paths Coverage**: 12% average (5 paths at 0%)
- **Test Count**: 847 tests across 6 services
- **Test Framework**: JUnit 5 + Mockito (Java), pytest (Python utilities)

## Compliance-Critical Paths (Must Cover)
| Path | Current Coverage | Required | Risk |
|---|---|---|---|
| `services/audit/src/main/java/com/bofa/audit/` | 0% | 80% | 🔴 CRITICAL |
| `services/auth/src/main/java/com/bofa/auth/rbac/` | 8% | 80% | 🔴 CRITICAL |
| `services/payment/src/main/java/com/bofa/payment/validation/` | 15% | 80% | 🔴 CRITICAL |
| `services/notification/src/main/java/com/bofa/notification/delivery/` | 22% | 80% | 🟡 HIGH |
| `services/account/src/main/java/com/bofa/account/kyc/` | 0% | 80% | 🔴 CRITICAL |
| `services/reporting/src/main/java/com/bofa/reporting/regulatory/` | 5% | 80% | 🔴 CRITICAL |
| `services/data-access/src/main/java/com/bofa/dal/encryption/` | 0% | 80% | 🔴 CRITICAL |

## Requirements
1. Achieve 80%+ line coverage on ALL compliance-critical paths
2. 70%+ branch coverage on the same paths
3. All tests must be deterministic (no flaky tests)
4. Tests must validate:
   - Audit trail completeness (every state change logged)
   - RBAC enforcement (unauthorized access blocked)
   - Data validation (PII sanitization, input validation)
   - Error handling (no sensitive data in error responses)
   - Encryption (data at rest and in transit)

## Constraints
- 8-week deadline (OCC exam date is fixed)
- Cannot modify production code to improve testability (separate PR if needed)
- Must use existing JUnit 5 + Mockito stack (no framework changes)
- Tests must run in CI in < 15 minutes total
- No external service dependencies in unit tests (all mocked)

## Deliverables
- [ ] Coverage report showing 80%+ on all listed paths
- [ ] Test execution report (all green, no skips)
- [ ] CI pipeline updated with coverage gate
- [ ] TESTING.md documenting test patterns and how to run
""",
    },
    {
        "repo": "gaurav21/bofa-enterprise-services",
        "title": "[HIGH] Bootstrap Test Infrastructure for Audit Service",
        "label": "shieldops-coverage",
        "body": """## Summary
The Audit Service (`services/audit/`) has **zero test infrastructure** — no test directory, no test dependencies, no CI test stage. This service handles all regulatory audit trail logging and is the #1 compliance risk in the upcoming OCC examination.

## Current State
- **Test Files**: 0
- **Test Framework**: None configured
- **Coverage**: 0%
- **CI Test Stage**: None
- **Last Modified**: Active development (12 commits in last 30 days)

## Service Overview
The Audit Service is a Java 17 / Spring Boot 3.x microservice that:
- Records all state changes across the enterprise services platform
- Generates immutable audit logs for regulatory examination
- Provides audit trail search and export APIs for compliance team
- Integrates with Splunk for long-term audit log retention
- Handles ~30K audit events/day

## Key Classes Requiring Tests
| Class | Responsibility | Priority |
|---|---|---|
| `AuditEventService` | Core audit event creation and validation | P0 |
| `AuditTrailRepository` | Persistence layer with immutability guarantees | P0 |
| `AuditExportController` | REST API for compliance team exports | P0 |
| `AuditEventValidator` | Input validation and sanitization | P0 |
| `ImmutabilityEnforcer` | Prevents modification of committed audit records | P0 |
| `RetentionPolicyService` | 7-year retention policy enforcement | P1 |
| `AuditSearchService` | Full-text search across audit logs | P1 |
| `SplunkForwarder` | Async forwarding to Splunk | P2 |

## Requirements
1. **Bootstrap JUnit 5 + Mockito + JaCoCo** in the audit service module
2. Create test directory structure: `src/test/java/com/bofa/audit/`
3. Write unit tests for ALL P0 classes (target: 80%+ coverage)
4. Write integration tests for the REST API endpoints
5. Configure JaCoCo with 80% minimum coverage gate
6. Add test stage to the service's CI pipeline
7. Create `services/audit/TESTING.md` with runbook for writing new tests

## Constraints
- Must use the same test framework as other services (JUnit 5 + Mockito)
- Integration tests must use H2 in-memory database (not real PostgreSQL)
- Splunk integration tests should mock the Splunk HEC endpoint
- All tests must be idempotent and isolated
- Test execution time budget: < 3 minutes for unit tests, < 5 minutes for integration

## Acceptance Criteria
- [ ] `mvn test -pl services/audit` runs successfully
- [ ] JaCoCo report shows 80%+ coverage on P0 classes
- [ ] CI pipeline includes test stage with coverage gate
- [ ] No test depends on external services or network
- [ ] TESTING.md exists with clear instructions
""",
    },
]


def create_issue(issue: dict) -> bool:
    """Create a single GitHub issue using gh CLI."""
    cmd = [
        "gh", "issue", "create",
        "--repo", issue["repo"],
        "--title", issue["title"],
        "--label", issue["label"],
        "--body", issue["body"],
    ]

    print(f"\n{'='*60}")
    print(f"Creating: {issue['title']}")
    print(f"Repo:     {issue['repo']}")
    print(f"Label:    {issue['label']}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"✅ Created: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {result.stderr.strip()}")
            # If label doesn't exist, try creating it first
            if "label" in result.stderr.lower():
                print("   Attempting to create label...")
                label_cmd = [
                    "gh", "label", "create", issue["label"],
                    "--repo", issue["repo"],
                    "--color", "0E8A16",
                    "--description", f"ShieldOps {issue['label'].replace('shieldops-', '')} task",
                    "--force",
                ]
                subprocess.run(label_cmd, capture_output=True, text=True)
                # Retry issue creation
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ Created (after label fix): {result.stdout.strip()}")
                    return True
                print(f"❌ Still failed: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout creating issue")
        return False
    except FileNotFoundError:
        print("❌ gh CLI not found — install from https://cli.github.com/")
        return False


def main():
    print("🛡️ ShieldOps — BofA Demo Issue Creator")
    print("Creating 6 issues across 2 repositories...\n")

    success = 0
    failed = 0

    for issue in ISSUES:
        if create_issue(issue):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {success} created, {failed} failed")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
