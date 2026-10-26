import pytest

from gigapoll.utils import parse_poll_id_from_result_id


@pytest.mark.parametrize(
        'result_id, expected',
        [
            ('share:42', 42),
            ('7:42', 42),
            ('7', None),
            ('share:abc', None),
            ('', None),
        ],
    )
def test_parse_poll_id_from_result_id(
        result_id: str,
        expected: int | None,
) -> None:
    assert parse_poll_id_from_result_id(result_id) == expected
