"""
IRIS Copilot
Button Components
"""

from __future__ import annotations

from .render import render_html


def _build_button(
    label: str,
    variant: str = "primary",
    icon: str | None = None,
    full_width: bool = False,
) -> str:

    classes = ["iris-btn", f"iris-btn-{variant}"]

    if full_width:
        classes.append("iris-btn-full")

    icon_html = f"<span>{icon}</span>" if icon else ""

    return f"""
    <div class="{' '.join(classes)}">
        {icon_html}
        <span>{label}</span>
    </div>
    """


def button(
    label: str,
    icon: str | None = None,
    full_width: bool = False,
) -> None:

    render_html(
        _build_button(
            label=label,
            variant="secondary",
            icon=icon,
            full_width=full_width,
        )
    )


def primary_button(
    label: str,
    icon: str | None = None,
    full_width: bool = False,
) -> None:

    render_html(
        _build_button(
            label=label,
            variant="primary",
            icon=icon,
            full_width=full_width,
        )
    )