from typing import NamedTuple


class ButtonDTO(NamedTuple):
    button_name: str
    button_cbdata: str
    votes: int

    @property
    def public_name(self) -> str:
        return f'{self.button_name} ({self.votes} votes)'


class UserDTO(NamedTuple):
    user_id: int
    first_name: str
    last_name: str | None
    username: str | None

    @property
    def full_name(self) -> str:
        return (
                f'{self.first_name} {self.last_name}'
                if self.last_name
                else self.first_name
            )

    @property
    def inline_user_html(self) -> str:
        return f'<a href="tg://user?id={self.user_id}">{self.full_name}</a>'


class UserWithChoiceDTO(NamedTuple):
    user: UserDTO
    choice: str
