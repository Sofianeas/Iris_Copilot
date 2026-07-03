"""
Tests des composants Alert.
"""

from app.ui.alerts import (
    _build_alert,
)


def test_success_alert():

    html = _build_alert(
        title="OK",
        description="Everything works",
        variant="success",
        show_icon=True,
    )

    assert "iris-alert-success" in html
    assert "OK" in html
    assert "Everything works" in html


def test_warning_alert():

    html = _build_alert(
        title="Warning",
        description="Check SLA",
        variant="warning",
        show_icon=True,
    )

    assert "iris-alert-warning" in html


def test_error_alert():

    html = _build_alert(
        title="Error",
        description="API down",
        variant="error",
        show_icon=True,
    )

    assert "iris-alert-error" in html


def test_info_alert():

    html = _build_alert(
        title="Info",
        description="Cache updated",
        variant="info",
        show_icon=False,
    )

    assert "iris-alert-info" in html