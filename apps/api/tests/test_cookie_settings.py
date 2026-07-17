"""Pruebas de atributos de cookie de sesion (cross-site vs local)."""
from __future__ import annotations

from app.config import Settings


def test_cookie_samesite_defaults_to_lax_in_development():
    s = Settings(ENVIRONMENT="development", COOKIE_SAMESITE="")
    assert s.cookie_samesite == "lax"
    assert s.cookie_secure is False


def test_cookie_samesite_defaults_to_none_in_production():
    s = Settings(ENVIRONMENT="production", COOKIE_SAMESITE="", COOKIE_SECURE=False)
    assert s.cookie_samesite == "none"
    # SameSite=None obliga Secure aunque COOKIE_SECURE sea false.
    assert s.cookie_secure is True


def test_cookie_samesite_explicit_override():
    s = Settings(ENVIRONMENT="production", COOKIE_SAMESITE="lax", COOKIE_SECURE=True)
    assert s.cookie_samesite == "lax"
    assert s.cookie_secure is True
