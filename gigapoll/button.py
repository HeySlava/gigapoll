from gigapoll.enums import Prefix


class CallbackButton:

    SEP = ':'

    def __init__(self, button_name: str, button_id: int, votes: int) -> None:
        self.button_name = button_name
        self.button_id = button_id
        self.votes = votes
        self._cbdata: str | None = None

    def get_public_name(self) -> str:
        return f'{self.button_name} ({self.votes} votes)'

    def extend_button(self, poll_id: int) -> None:
        self._cbdata = (
                f'{Prefix.VOTE}{self.SEP}{self.button_id}{self.SEP}{poll_id}'
            )

    def get_cbdata(self) -> str:
        if self._cbdata is None:
            raise ValueError('Cbdata is not extended')
        return self._cbdata

    @classmethod
    def parse_cbdata(cls, cbdata: str) -> tuple[int, int]:
        _, button_id, poll_id = cbdata.split(cls.SEP)
        return int(button_id), int(poll_id)
