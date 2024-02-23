from typing import NamedTuple


class ButtonDTO(NamedTuple):
    description: str
    name: str
    button_name: str
    button_cbdata: str
    votes: int

    @property
    def public_name(self) -> str:
        return f'{self.button_name} ({self.votes} votes)'


class CntPerValue(NamedTuple):
    button_name: str
    button_cbdata: str
    cnt: int


class UserChoiceDTO(NamedTuple):
    first_name: str
    last_name: str | None
    username: str | None
    choice: str


class AggUsersByButton(NamedTuple):
    button_value: str
    users: list[str]
