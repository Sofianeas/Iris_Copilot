"""
Tests des composants Metrics.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.metrics import metric, metric_row


@patch("app.ui.metrics.st.metric")
def test_metric_calls_streamlit(mock_metric: MagicMock) -> None:
    """metric() doit appeler st.metric()."""

    metric(
        label="Tickets",
        value=42,
        delta="+2",
        help="Aide",
    )

    mock_metric.assert_called_once_with(
        label="Tickets",
        value=42,
        delta="+2",
        help="Aide",
    )


@patch("app.ui.metrics.st.columns")
@patch("app.ui.metrics.st.metric")
def test_metric_row(mock_metric: MagicMock, mock_columns: MagicMock) -> None:
    """metric_row() doit afficher une métrique par colonne."""

    columns = [MagicMock(), MagicMock(), MagicMock()]

    mock_columns.return_value = columns

    metric_row(
        [
            {"label": "A", "value": 1},
            {"label": "B", "value": 2},
            {"label": "C", "value": 3},
        ]
    )

    mock_columns.assert_called_once_with(3)

    assert mock_metric.call_count == 3


@patch("app.ui.metrics.st.columns")
def test_metric_row_empty(mock_columns: MagicMock) -> None:
    """Aucune colonne ne doit être créée si la liste est vide."""

    metric_row([])

    mock_columns.assert_not_called()