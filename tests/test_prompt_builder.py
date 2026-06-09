"""Tests for src/orchestrator/prompt_builder.py — prompt generation per vulnerability type."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.orchestrator.prompt_builder import PromptBuilder, STRUCTURED_OUTPUT_INSTRUCTION
from src.scanner.models import Severity, Vulnerability, VulnerabilityType


class TestPromptBuilder:
    def setup_method(self):
        self.builder = PromptBuilder(
            repo_url="https://github.com/testorg/testrepo",
            repo_name="testrepo",
        )

    def test_python_dep_prompt_contains_key_info(self, sample_vuln):
        prompt = self.builder.build_prompt(sample_vuln)
        assert "requests" in prompt
        assert "2.28.0" in prompt
        assert "2.31.0" in prompt
        assert "CVE-2023-0001" in prompt
        assert "pip-audit" not in prompt or "requirements" in prompt
        assert "CHANGELOG" in prompt
        assert STRUCTURED_OUTPUT_INSTRUCTION in prompt

    def test_npm_dep_prompt(self, npm_vuln):
        prompt = self.builder.build_prompt(npm_vuln)
        assert "lodash" in prompt
        assert "superset-frontend" in prompt
        assert "npm" in prompt
        assert STRUCTURED_OUTPUT_INSTRUCTION in prompt

    def test_sast_prompt_includes_file_location(self, sast_vuln):
        prompt = self.builder.build_prompt(sast_vuln)
        assert "superset/sql_lab.py" in prompt
        assert "line 42" in prompt
        assert "SQL injection" in prompt or "security" in prompt.lower()
        assert STRUCTURED_OUTPUT_INSTRUCTION in prompt

    def test_container_prompt(self, container_vuln):
        prompt = self.builder.build_prompt(container_vuln)
        assert "openssl" in prompt
        assert "Dockerfile" in prompt
        assert "docker" in prompt.lower()
        assert STRUCTURED_OUTPUT_INSTRUCTION in prompt

    def test_code_quality_uses_sast_prompt(self):
        vuln = Vulnerability(
            id="cq1", title="Code quality issue",
            description="Dead code detected",
            severity=Severity.MEDIUM,
            vuln_type=VulnerabilityType.CODE_QUALITY,
            package_name="dead-code-rule",
            current_version="N/A",
            file_path="src/utils.py",
            line_number=10,
            scanner="semgrep",
            discovered_at=datetime(2024, 1, 1),
        )
        prompt = self.builder.build_prompt(vuln)
        assert "src/utils.py" in prompt
        assert STRUCTURED_OUTPUT_INSTRUCTION in prompt

    def test_generic_prompt_for_unknown_type(self, sample_vuln):
        # Force an unrecognized vuln_type by directly calling _generic_prompt
        prompt = self.builder._generic_prompt(sample_vuln)
        assert "requests" in prompt
        assert "https://github.com/testorg/testrepo" in prompt

    def test_structured_output_instruction_always_appended(self, sample_vuln, npm_vuln,
                                                            sast_vuln, container_vuln):
        for vuln in [sample_vuln, npm_vuln, sast_vuln, container_vuln]:
            prompt = self.builder.build_prompt(vuln)
            assert "Structured Output Required" in prompt
            assert "confidence" in prompt
            assert "breaking_changes_detected" in prompt

    def test_repo_url_in_prompts(self, sample_vuln):
        prompt = self.builder.build_prompt(sample_vuln)
        assert "https://github.com/testorg/testrepo" in prompt

    def test_no_advisory_url_shows_na(self):
        vuln = Vulnerability(
            id="x", title="test", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="pkg", current_version="1.0",
            advisory_url=None,
            discovered_at=datetime(2024, 1, 1),
        )
        prompt = self.builder.build_prompt(vuln)
        assert "N/A" in prompt

    def test_no_fixed_version_shows_latest(self):
        vuln = Vulnerability(
            id="x", title="test", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="pkg", current_version="1.0",
            fixed_version=None,
            discovered_at=datetime(2024, 1, 1),
        )
        prompt = self.builder.build_prompt(vuln)
        assert "latest" in prompt.lower()

    def test_sast_prompt_without_line_number(self):
        vuln = Vulnerability(
            id="x", title="test", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.SAST,
            package_name="rule", current_version="N/A",
            file_path="src/app.py",
            line_number=None,
            scanner="semgrep",
            discovered_at=datetime(2024, 1, 1),
        )
        prompt = self.builder.build_prompt(vuln)
        assert "src/app.py" in prompt
        assert "line None" not in prompt
