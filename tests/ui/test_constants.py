from app.ui.constants import *


def test_variants():

    assert SUCCESS == "success"
    assert WARNING == "warning"
    assert ERROR == "error"
    assert INFO == "info"


def test_badge_variants():

    assert SUCCESS in BADGE_VARIANTS
    assert CLIENT in BADGE_VARIANTS