from flip_sign.helpers import is_timezone_naive
import datetime
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())


def test_timezone_naivete():
    assert is_timezone_naive(datetime.datetime.now())

    assert not is_timezone_naive(datetime.datetime.now().astimezone())

    assert not is_timezone_naive(datetime.datetime(1999, 12, 31).replace(tzinfo=LOCAL_TIMEZONE))

    assert not is_timezone_naive(datetime.datetime.fromisoformat('1999-12-31T23:59:59-10:00'))
