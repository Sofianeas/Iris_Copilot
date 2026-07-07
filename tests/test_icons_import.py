from app.ui import (
    add,
    analytics,
    arrow_back,
    arrow_forward,
    attachment,
    calendar,
    cancel,
    check,
    close,
    dashboard,
    delete,
    download,
    edit,
    error,
    expand_less,
    expand_more,
    file,
    filter,
    folder,
    group,
    help,
    home,
    info,
    lock,
    mail,
    pause,
    person,
    phone,
    play,
    refresh,
    save,
    schedule,
    search,
    settings,
    stop,
    support,
    ticket,
    unlock,
    upload,
    visibility,
    warning,
)


def test_icons_import() -> None:
    """Ensure all icon helpers are importable."""

    assert callable(add)
    assert callable(search)
    assert callable(ticket)
    assert callable(settings)
    assert callable(home)

def test_icons_return_strings() -> None:
    """Ensure icon helpers return Material icon identifiers."""

    assert add() == ":material/add:"
    assert search() == ":material/search:"
    assert warning() == ":material/warning:"
    assert ticket() == ":material/confirmation_number:"