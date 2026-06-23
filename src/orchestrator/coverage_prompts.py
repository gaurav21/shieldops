"""
Prompt templates for test coverage task types.

These prompts instruct Devin to analyze coverage gaps, generate tests
for compliance-critical paths, and bootstrap test infrastructure.
"""


def coverage_analysis_prompt(
    repo_path: str,
    compliance_paths: list[str],
) -> str:
    """
    Generate a Devin prompt to analyze current test coverage gaps,
    focusing on compliance-critical code paths.
    """
    paths_list = "\n".join(f"- `{p}`" for p in compliance_paths)

    return f"""You are analyzing test coverage for a compliance-critical codebase.

## Repository
{repo_path}

## Compliance-Critical Paths
These paths MUST have test coverage for regulatory audit readiness:
{paths_list}

## Analysis Steps

### 1. Current Coverage Assessment
- Run existing test suite and generate coverage report
- Identify which compliance-critical paths have ZERO coverage
- Identify paths with partial coverage (< 80% line coverage)
- Map untested code paths to business risk

### 2. Coverage Gap Report
For each compliance-critical path, report:
- Current line coverage percentage
- Current branch coverage percentage
- Number of untested functions/methods
- Risk assessment: CRITICAL (0%), HIGH (< 50%), MEDIUM (< 80%), LOW (>= 80%)

### 3. Test Generation Priority
Rank gaps by:
1. Regulatory risk (audit-facing code first)
2. Complexity (more complex = more likely to have bugs)
3. Change frequency (frequently changed code needs tests most)

### 4. Structured Output
Report back with:
- coverage_report: dict of path → coverage percentage
- critical_gaps: list of paths with 0% coverage
- high_gaps: list of paths with < 50% coverage
- recommended_test_count: estimated tests needed
- confidence: 0.0-1.0
- changes_summary: analysis findings
"""


def test_generation_prompt(
    service: str,
    target_paths: list[str],
    coverage_target: int = 80,
) -> str:
    """
    Generate a Devin prompt to write tests for specific compliance-critical paths.
    """
    paths_list = "\n".join(f"- `{p}`" for p in target_paths)

    return f"""You are generating tests for compliance-critical paths in the {service} service.

## Target Paths
{paths_list}

## Coverage Target: {coverage_target}%

## Test Generation Rules

### 1. Test Strategy
- Write unit tests for all public methods in target paths
- Write integration tests for cross-service interactions
- Include edge cases: null inputs, boundary values, error conditions
- Include negative tests: invalid inputs, unauthorized access, malformed data

### 2. Compliance-Specific Tests
- **Audit trail**: Verify all state changes are logged with timestamps and actor
- **Data validation**: Verify input sanitization on all user-facing endpoints
- **Access control**: Verify RBAC enforcement on every protected endpoint
- **Data retention**: Verify PII handling follows retention policies
- **Error handling**: Verify no sensitive data leaks in error responses

### 3. Test Quality Standards
- Each test must have a clear, descriptive name explaining what it validates
- Use AAA pattern: Arrange → Act → Assert
- Mock external dependencies (databases, APIs, message queues)
- No test interdependencies — each test runs in isolation
- Include both happy path and failure path tests

### 4. Validation
- Run the full test suite — all new AND existing tests must pass
- Generate coverage report — target paths must reach {coverage_target}%+ coverage
- No flaky tests — run suite 3x to verify consistency

### 5. Structured Output
Report back with:
- files_touched: list of all test files created/modified
- tests_added: number of new test cases
- coverage_before: coverage percentage before changes
- coverage_after: coverage percentage after changes
- tests_passed: true/false
- confidence: 0.0-1.0
- changes_summary: what tests were added and why
"""


def test_infra_setup_prompt(
    service: str,
    language: str,
) -> str:
    """
    Generate a Devin prompt to bootstrap test infrastructure where none exists.
    """
    framework_map = {
        "java": ("JUnit 5 + Mockito + JaCoCo", "mvn test", "target/site/jacoco/index.html"),
        "kotlin": ("JUnit 5 + MockK + JaCoCo", "gradle test jacocoTestReport", "build/reports/jacoco/test/html/index.html"),
        "python": ("pytest + pytest-cov + unittest.mock", "pytest --cov --cov-report=html", "htmlcov/index.html"),
        "javascript": ("Jest + Istanbul", "npm test -- --coverage", "coverage/lcov-report/index.html"),
        "typescript": ("Jest + ts-jest + Istanbul", "npm test -- --coverage", "coverage/lcov-report/index.html"),
        "go": ("testing + testify + go tool cover", "go test -coverprofile=coverage.out ./...", "coverage.html"),
    }

    framework, cmd, report = framework_map.get(
        language.lower(),
        ("appropriate test framework", "test command", "coverage report"),
    )

    return f"""You are bootstrapping test infrastructure for the {service} service ({language}).

This service currently has NO test framework configured.

## Setup Requirements

### 1. Framework Installation
- Install {framework}
- Configure test runner in build config (pom.xml / build.gradle / package.json / etc.)
- Set up coverage reporting with minimum threshold of 80%

### 2. Test Directory Structure
Create standard test directory layout:
- Unit tests: `tests/unit/` or `src/test/`
- Integration tests: `tests/integration/`
- Test fixtures/factories: `tests/fixtures/`
- Test configuration: `tests/conftest` or equivalent

### 3. CI Integration
- Add test stage to existing CI pipeline (if exists)
- Configure coverage report generation: `{cmd}`
- Coverage report output: `{report}`
- Set CI to fail if coverage drops below threshold

### 4. Starter Tests
Write initial tests to validate the setup:
- At least 1 unit test per major service class
- At least 1 integration test for the main API endpoint
- Verify test runner works: all starter tests must pass

### 5. Documentation
- Add `TESTING.md` with:
  - How to run tests locally
  - How to generate coverage reports
  - Test writing guidelines
  - Mocking patterns used

### 6. Structured Output
Report back with:
- files_touched: list of all files created/modified
- framework_installed: name and version of test framework
- tests_added: number of starter tests
- tests_passed: true/false
- confidence: 0.0-1.0
- changes_summary: what was set up and how to use it
"""
