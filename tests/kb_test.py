from gigapoll.button import CallbackButton
from gigapoll.enums import Modes
from gigapoll.kb import get_different_modes_kb
from gigapoll.kb import get_poll_kb


def test_modes_kb_contains_all_modes() -> None:
    kb = get_different_modes_kb()

    callbacks = [
            b.callback_data
            for row in kb.inline_keyboard
            for b in row
        ]
    assert Modes.PLUS_MINUS in callbacks
    assert Modes.MULTI_SELECT in callbacks


def test_poll_kb_button_text_and_cbdata() -> None:
    b = CallbackButton(button_name='opt', button_id=1, votes=0)
    b.extend_button(poll_id=1)

    kb = get_poll_kb([b])

    button = kb.inline_keyboard[0][0]
    assert button.text == 'opt'
    assert button.callback_data == b.get_cbdata()


def test_poll_kb_sorts_buttons_by_id() -> None:
    b1 = CallbackButton(button_name='second', button_id=2, votes=0)
    b2 = CallbackButton(button_name='first', button_id=1, votes=0)
    b1.extend_button(poll_id=1)
    b2.extend_button(poll_id=1)

    kb = get_poll_kb([b1, b2])

    texts = [row[0].text for row in kb.inline_keyboard]
    assert texts == ['first', 'second']
