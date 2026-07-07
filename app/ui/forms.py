"""
IRIS Copilot
Form Components

Thin wrappers around Streamlit form widgets.

This module provides a consistent, typed and reusable API for
Streamlit form components while remaining fully compatible with
the official Streamlit API.

No business logic should ever be implemented here.
"""

from __future__ import annotations

# ==========================================================
# Standard Library
# ==========================================================

from collections.abc import Callable, Sequence
from datetime import date, time, timedelta
from typing import Any, Literal, TypeVar

# ==========================================================
# Third-Party
# ==========================================================

import streamlit as st

# ==========================================================
# Type Variables
# ==========================================================

OptionT = TypeVar("OptionT")

# ==========================================================
# Public API
# ==========================================================

__all__ = [
    # Text Inputs
    "text_input",
    "text_area",
    # Numeric Inputs
    "number_input",
    "slider",
    # Selection Inputs
    "selectbox",
    "multiselect",
    "radio",
    # Boolean Inputs
    "checkbox",
    "toggle",
    # Date & Time Inputs
    "date_input",
    "time_input",
    # Upload
    "file_uploader",
    # Submission
    "form_submit_button",
]

# ==========================================================
# Text Inputs
# ==========================================================


def text_input(
    label: str,
    value: str = "",
    *,
    max_chars: int | None = None,
    key: str | None = None,
    type: str = "default",
    help: str | None = None,
    autocomplete: str | None = None,
    on_change: callable | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str = "stretch",
) -> str:
    """
    Display a single-line text input widget.

    This is a thin wrapper around ``streamlit.text_input`` that
    preserves the official Streamlit API while providing a
    consistent entry point for the IRIS Copilot UI library.

    Returns
    -------
    str
        The current value of the text input.
    """

    return st.text_input(
        label=label,
        value=value,
        max_chars=max_chars,
        key=key,
        type=type,
        help=help,
        autocomplete=autocomplete,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def text_area(
    label: str,
    value: str = "",
    *,
    height: int | None = None,
    max_chars: int | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: callable | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str = "stretch",
) -> str:
    """
    Display a multi-line text area widget.

    This is a thin wrapper around ``streamlit.text_area`` that
    preserves the official Streamlit API while providing a
    consistent entry point for the IRIS Copilot UI library.

    Returns
    -------
    str
        The current value of the text area.
    """

    return st.text_area(
        label=label,
        value=value,
        height=height,
        max_chars=max_chars,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


# ==========================================================
# Numeric Inputs
# ==========================================================
# ==========================================================
# Numeric Inputs
# ==========================================================


def number_input(
    label: str,
    value: int | float | None = 0,
    *,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    step: int | float | None = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> int | float:
    """
    Display a numeric input widget.

    Thin wrapper around ``streamlit.number_input``.

    Returns
    -------
    int | float
        Current numeric value.
    """
    return st.number_input(
        label=label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        format=format,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def slider(
    label: str,
    *,
    min_value: Any = None,
    max_value: Any = None,
    value: Any = None,
    step: Any = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> Any:
    """
    Display a slider widget.

    Thin wrapper around ``streamlit.slider``.

    Returns
    -------
    Any
        Current slider value.
    """
    return st.slider(
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        format=format,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


# ==========================================================
# Selection Inputs
# ==========================================================


def selectbox(
    label: str,
    options: Sequence[OptionT],
    *,
    index: int | None = 0,
    format_func: Callable[[OptionT], str] = str,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> OptionT | None:
    """
    Display a select box widget.

    Thin wrapper around ``streamlit.selectbox``.

    Returns
    -------
    OptionT | None
        Selected option.
    """
    return st.selectbox(
        label=label,
        options=options,
        index=index,
        format_func=format_func,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def multiselect(
    label: str,
    options: Sequence[OptionT],
    *,
    default: Sequence[OptionT] | None = None,
    format_func: Callable[[OptionT], str] = str,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> list[OptionT]:
    """
    Display a multiselect widget.

    Thin wrapper around ``streamlit.multiselect``.

    Returns
    -------
    list[OptionT]
        Selected options.
    """
    return st.multiselect(
        label=label,
        options=options,
        default=default,
        format_func=format_func,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def radio(
    label: str,
    options: Sequence[OptionT],
    *,
    index: int = 0,
    format_func: Callable[[OptionT], str] = str,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    horizontal: bool = False,
    captions: Sequence[str] | None = None,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "content",
) -> OptionT:
    """
    Display a radio button widget.

    Thin wrapper around ``streamlit.radio``.

    Returns
    -------
    OptionT
        Selected option.
    """
    return st.radio(
        label=label,
        options=options,
        index=index,
        format_func=format_func,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        horizontal=horizontal,
        captions=captions,
        label_visibility=label_visibility,
        width=width,
    )


# ==========================================================
# Boolean Inputs
# ==========================================================


def checkbox(
    label: str,
    value: bool = False,
    *,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["content", "stretch"] = "content",
) -> bool:
    """
    Display a checkbox widget.

    Thin wrapper around ``streamlit.checkbox``.

    Returns
    -------
    bool
        Current checkbox state.
    """
    return st.checkbox(
        label=label,
        value=value,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def toggle(
    label: str,
    value: bool = False,
    *,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["content", "stretch"] = "content",
) -> bool:
    """
    Display a toggle widget.

    Thin wrapper around ``streamlit.toggle``.

    Returns
    -------
    bool
        Current toggle state.
    """
    return st.toggle(
        label=label,
        value=value,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


# ==========================================================
# Date & Time Inputs
# ==========================================================


def date_input(
    label: str,
    value: Any = "today",
    *,
    min_value: date | None = None,
    max_value: date | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    format: str = "YYYY/MM/DD",
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> Any:
    """
    Display a date input widget.

    Thin wrapper around ``streamlit.date_input``.

    Returns
    -------
    Any
        Current selected date or date range.
    """
    return st.date_input(
        label=label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        format=format,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


def time_input(
    label: str,
    value: time | None = None,
    *,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    step: int | timedelta = 900,
    width: Literal["stretch", "content"] = "stretch",
) -> time:
    """
    Display a time input widget.

    Thin wrapper around ``streamlit.time_input``.

    Returns
    -------
    time
        Current selected time.
    """
    return st.time_input(
        label=label,
        value=value,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        label_visibility=label_visibility,
        step=step,
        width=width,
    )


# ==========================================================
# Upload
# ==========================================================


def file_uploader(
    label: str,
    *,
    type: str | Sequence[str] | None = None,
    accept_multiple_files: bool = False,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    disabled: bool = False,
    label_visibility: Literal[
        "visible",
        "hidden",
        "collapsed",
    ] = "visible",
    width: Literal["stretch", "content"] = "stretch",
) -> Any:
    """
    Display a file uploader widget.

    Thin wrapper around ``streamlit.file_uploader``.

    Returns
    -------
    Any
        Uploaded file or list of uploaded files depending on
        ``accept_multiple_files``.
    """
    return st.file_uploader(
        label=label,
        type=type,
        accept_multiple_files=accept_multiple_files,
        key=key,
        help=help,
        on_change=on_change,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        label_visibility=label_visibility,
        width=width,
    )


# ==========================================================
# Submission
# ==========================================================


def form_submit_button(
    label: str = "Submit",
    *,
    help: str | None = None,
    on_click: Callable[..., None] | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    type: Literal["primary", "secondary", "tertiary"] = "primary",
    icon: str | None = None,
    disabled: bool = False,
    width: Literal["stretch", "content"] = "content",
) -> bool:
    """
    Display a form submit button.

    Thin wrapper around ``streamlit.form_submit_button``.

    Returns
    -------
    bool
        ``True`` when the form has been submitted.
    """
    return st.form_submit_button(
        label=label,
        help=help,
        on_click=on_click,
        args=args,
        kwargs=kwargs,
        type=type,
        icon=icon,
        disabled=disabled,
        width=width,
    )
