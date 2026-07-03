"""
IRIS Copilot
Badge Components
"""

from __future__ import annotations

from .render import render_html

BADGE_VARIANTS = {
    "success": "badge-success",
    "error": "badge-error",
    "warning": "badge-warning",
    "info": "badge-info",
    "danger": "badge-danger",
    "client": "badge-client",
    "generic": "badge-generic",
}


def badge(label: str, variant: str = "generic") -> str:
    """
    Build a badge HTML fragment.

    Parameters
    ----------
    label:
        Badge text.

    variant:
        Badge style variant.

    Returns
    -------
    str
        HTML fragment representing the badge.
    """
    css = BADGE_VARIANTS.get(
        variant.lower(),
        "badge-generic",
    )

    return f"""
    <span class="badge {css}">
        {label}
    </span>
    """


def _build_badge_group(badges: list[str]) -> str:
    """
    Build the HTML for a group of badges.
    """
    return f"""
    <div class="badge-group">
        {''.join(badges)}
    </div>
    """


def badge_group(badges: list[str]) -> None:
    """
    Affiche un groupe de badges.
    """
    group_html = _build_badge_group(badges)
    render_html(group_html)