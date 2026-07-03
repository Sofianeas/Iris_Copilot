"""
Tests de l'API publique UI.
"""

from app.ui.components import *


def test_import_cards():
    assert callable(metric_card)
    assert callable(info_card)
    assert callable(feature_card)
    assert callable(action_card)
    assert callable(stat_card)


def test_import_layout():
    assert callable(hero)
    assert callable(section)
    assert callable(divider)
    assert callable(page_title)
    assert callable(empty_state)
    assert callable(footer)


def test_import_badges():
    assert callable(badge)
    assert callable(badge_group)