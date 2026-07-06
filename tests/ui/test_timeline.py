"""
Tests des composants Timeline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.timeline import timeline


@patch("app.ui.timeline.st.info")
def test_timeline_empty(mock_info: MagicMock) -> None:
    """Une timeline vide doit afficher un message d'information."""

    timeline([])

    mock_info.assert_called_once_with("Aucun événement.")


@patch("app.ui.timeline.st.divider")
@patch("app.ui.timeline.st.write")
@patch("app.ui.timeline.st.caption")
@patch("app.ui.timeline.st.markdown")
@patch("app.ui.timeline.st.container")
def test_timeline_events(
    mock_container: MagicMock,
    mock_markdown: MagicMock,
    mock_caption: MagicMock,
    mock_write: MagicMock,
    mock_divider: MagicMock,
) -> None:
    """La timeline doit afficher les événements."""

    mock_container.return_value.__enter__.return_value = MagicMock()

    timeline(
        [
            {
                "title": "Création",
                "timestamp": "09:00",
                "description": "Ticket créé.",
            },
            {
                "title": "Clôture",
                "timestamp": "10:00",
            },
        ]
    )

    assert mock_markdown.call_count == 2
    assert mock_caption.call_count == 2
    assert mock_write.call_count == 1
    assert mock_divider.call_count == 1