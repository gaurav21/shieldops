"""Tests for src/webhooks/github_webhook.py — signature verification."""

from __future__ import annotations

import hashlib
import hmac

import pytest

from src.webhooks.github_webhook import _verify_signature


class TestVerifySignature:
    def test_valid_signature(self):
        secret = "my-secret-key"
        payload = b'{"action": "labeled"}'
        expected_sig = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        assert _verify_signature(payload, expected_sig, secret) is True

    def test_invalid_signature(self):
        secret = "my-secret-key"
        payload = b'{"action": "labeled"}'
        assert _verify_signature(payload, "sha256=invalid", secret) is False

    def test_empty_secret_skips_verification(self):
        payload = b'{"action": "labeled"}'
        assert _verify_signature(payload, "sha256=anything", "") is True

    def test_different_payload_fails(self):
        secret = "my-secret-key"
        payload = b'{"action": "labeled"}'
        other_payload = b'{"action": "unlabeled"}'
        sig = "sha256=" + hmac.new(
            secret.encode(), other_payload, hashlib.sha256
        ).hexdigest()
        assert _verify_signature(payload, sig, secret) is False

    def test_empty_payload(self):
        secret = "key"
        payload = b""
        sig = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        assert _verify_signature(payload, sig, secret) is True
