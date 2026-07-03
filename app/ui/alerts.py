"""
IRIS Copilot
Alert Components
"""

from __future__ import annotations

from .constants import (
    SUCCESS,
    WARNING,
    ERROR,
    INFO,
    SUCCESS_ICON,
    WARNING_ICON,
    ERROR_ICON,
    INFO_ICON,
)

from .render import render_html


_ICONS = {
    SUCCESS: SUCCESS_ICON,
    WARNING: WARNING_ICON,
    ERROR: ERROR_ICON,
    INFO: INFO_ICON,
}


def alert(
    title: str,
    description: str = "",
    variant: str = INFO,
    icon: bool = True,
) -> None:
    """
    Affiche une alerte du Design System.
    """

    icon_html = ""

    if icon:
        icon_html = f"""
        <div class="iris-alert-icon">
            {_ICONS.get(variant, INFO_ICON)}
        </div>
        """

    description_html = ""

    if description:
        description_html = f"""
        <div class="iris-alert-description">
            {description}
        </div>
        """

    render_html(
        f"""
        <div class="iris-alert iris-alert-{variant}">

            {icon_html}

            <div class="iris-alert-content">

                <div class="iris-alert-title">
                    {title}
                </div>

                {description_html}

            </div>

        </div>
        """
    )