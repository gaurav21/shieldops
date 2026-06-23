"""
Prompt templates for migration and cloud-migration task types.

These prompts instruct Devin to perform framework upgrades and
cloud infrastructure migrations with enterprise-grade rigor.
"""


def angular_upgrade_prompt(
    from_version: str,
    to_version: str,
    repo_context: str,
) -> str:
    """
    Generate a Devin prompt for Angular major-version upgrades.

    Covers: NgModules → standalone, MatLegacy → Mat, RxJS operator
    changes, Zone.js updates, and full test validation.
    """
    return f"""You are upgrading an Angular application from v{from_version} to v{to_version}.

## Repository Context
{repo_context}

## Upgrade Strategy

### 1. Read Changelogs & Migration Guides
- Read the official Angular update guide: https://update.angular.io/?v={from_version}.0-{to_version}.0
- Review EVERY breaking change between v{from_version} and v{to_version}
- Document each breaking change that affects this codebase

### 2. Breaking Pattern Detection & Fix
Apply these transformations across ALL call sites (not just the first match):

**NgModules → Standalone Components (v{from_version} < 15 → v{to_version} >= 15):**
- Convert `@NgModule` declarations to standalone components where possible
- Add `standalone: true` to component decorators
- Replace module imports with direct component imports
- Update routing to use `loadComponent` instead of `loadChildren` with modules

**Angular Material Legacy Migration:**
- Replace ALL `MatLegacy*` imports with `Mat*` equivalents
- `@angular/material/legacy-button` → `@angular/material/button`
- `@angular/material/legacy-input` → `@angular/material/input`
- Update ALL template selectors: `mat-legacy-*` → `mat-*`
- Fix any styling regressions from MDC-based components

**RxJS Updates:**
- Replace deprecated operators with current equivalents
- `pluck` → `map` with destructuring
- Ensure `pipe()` usage everywhere (no legacy chained operators)
- Update `subscribe` patterns to use observer objects where applicable

**Zone.js & Change Detection:**
- Update Zone.js to compatible version
- Consider `OnPush` change detection where beneficial
- Update `async` pipe usage if needed

### 3. Dependency Resolution
- Run `ng update @angular/core@{to_version} @angular/cli@{to_version}`
- Resolve ALL peer dependency conflicts
- Update third-party Angular libraries to compatible versions
- Do NOT leave any `--force` or `--legacy-peer-deps` flags

### 4. Validation
- Run `ng build --configuration=production` — must succeed with zero errors
- Run `ng test` — all existing tests must pass
- Run `ng lint` — fix any new lint violations
- Verify the app starts without console errors

### 5. Structured Output
Report back with:
- files_touched: list of all modified files
- breaking_changes_detected: true/false
- breaking_changes_notes: what patterns were found and fixed
- tests_passed: true/false
- confidence: 0.0-1.0 (how confident you are in the migration)
- changes_summary: brief description of all changes made
"""


def cloud_migration_prompt(
    source_stack: str,
    target_stack: str,
    constraints: str,
) -> str:
    """
    Generate a Devin prompt for cloud infrastructure migrations.

    Covers: messaging (IBM MQ → SQS), database (Oracle → RDS),
    auth (LDAP → Cognito), compute (Spring Boot → Lambda),
    with strict SLA preservation.
    """
    return f"""You are migrating enterprise services from legacy infrastructure to cloud-native AWS.

## Source Stack
{source_stack}

## Target Stack
{target_stack}

## Constraints
{constraints}

## Migration Strategy

### 1. Service Mapping & Impact Analysis
Before writing any code, document the complete mapping:

**Messaging: IBM MQ → Amazon SQS FIFO**
- Map each MQ queue to an SQS FIFO queue
- Preserve message ordering using MessageGroupId (map from MQ correlation IDs)
- Implement exactly-once processing using MessageDeduplicationId
- Handle poison pill / DLQ patterns (map IBM MQ backout queues → SQS DLQ)
- Preserve message selectors using SQS message attributes + filtering
- Transaction boundaries: MQ XA transactions → SQS + idempotency patterns

**Database: Oracle → Amazon RDS (PostgreSQL/Aurora)**
- Map Oracle-specific SQL (CONNECT BY, ROWNUM, NVL) to PostgreSQL equivalents
- Convert PL/SQL stored procedures to application-level logic or PL/pgSQL
- Migrate sequences, synonyms, materialized views
- Preserve referential integrity and constraint naming

**Authentication: LDAP → Amazon Cognito**
- Map LDAP groups to Cognito groups
- Preserve role-based access control (RBAC) mappings
- Implement Cognito user pool with matching password policies
- Handle service-to-service auth via Cognito M2M or IAM roles

**Compute: Spring Boot → AWS Lambda**
- Identify stateless request handlers suitable for Lambda
- Keep stateful/long-running services on ECS/Fargate
- Handle cold start latency (provisioned concurrency for critical paths)
- Convert Spring dependency injection to Lambda handler patterns
- Preserve health check and circuit breaker patterns

### 2. SLA Preservation
- Current SLAs must be maintained or improved
- Document latency impact of each migration component
- Implement circuit breakers and fallback patterns
- Ensure message ordering guarantees are preserved end-to-end

### 3. Implementation Order
1. Infrastructure as Code (CDK/Terraform) for target resources
2. Adapter/Anti-corruption layer for each integration point
3. Dual-write pattern for data migration (write to both during cutover)
4. Canary deployment with traffic splitting
5. Validation and cutover

### 4. Structured Output
Report back with:
- files_touched: list of all modified files
- breaking_changes_detected: true/false
- breaking_changes_notes: any compatibility concerns
- tests_passed: true/false
- confidence: 0.0-1.0
- changes_summary: what was migrated and how
- migration_risks: identified risks and mitigations
"""
