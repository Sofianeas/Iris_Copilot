"""
Tests des composants Tables.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.ui.tables import data_table


@patch("app.ui.tables.st.dataframe")
def test_data_table_calls_streamlit(mock_dataframe: MagicMock) -> None:
    """data_table() doit appeler st.dataframe()."""

    df = pd.DataFrame(
        {
            "A": [1, 2],
            "B": [3, 4],
        }
    )

    data_table(df)

    mock_dataframe.assert_called_once_with(
    df,
    width="stretch",
    hide_index=True,
    )