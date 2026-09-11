import pytest

from gigapoll.button import CallbackButton
from gigapoll.enums import Prefix


def test_cbdata_roundtrip() -> None:
    b = CallbackButton(button_name='opt', button_id=5, votes=0)
    b.extend_button(poll_id=7)

    assert b.get_cbdata() == f'{Prefix.VOTE}:5:7'
    assert CallbackButton.parse_cbdata(b.get_cbdata()) == (5, 7)


def test_cbdata_raises_when_not_extended() -> None:
    b = CallbackButton(button_name='opt', button_id=1, votes=0)
    with pytest.raises(ValueError):
        b.get_cbdata()
