import datetime
from tzlocal import get_localzone_name
from pytz import timezone
from dateutil.relativedelta import relativedelta
from dateutil.easter import easter

LOCAL_TIMEZONE = timezone(get_localzone_name())


def mothers_day():
    """
    Returns the next occurrence of Mothers' Day (US standard).

    :return: (start, end): (both datetime.datetime) the start and end of next mothers day, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_mothers_day = (datetime.datetime(this_year, 5, 1) +
                             relativedelta(day=1, weekday=6) +
                             datetime.timedelta(days=7))

    if this_year_mothers_day.replace(hour=23, minute=59) > datetime.datetime.now():
        next_mothers_day = this_year_mothers_day.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_mothers_day = (datetime.datetime(this_year + 1, 5, 1) +
                            relativedelta(day=1, weekday=6) +
                            datetime.timedelta(days=7)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_mothers_day, next_mothers_day.replace(hour=23, minute=59)


def thanksgiving():
    """
    Returns the next occurrence of US Thanksgiving.

    :return: (start, end): (both datetime.datetime) the start and end of next thanksgiving, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_thanksgiving = (datetime.datetime(this_year, 11, 1) +
                              relativedelta(day=1, weekday=3) +
                              datetime.timedelta(weeks=3))

    if this_year_thanksgiving.replace(hour=23, minute=59) > datetime.datetime.now():
        next_thanksgiving = this_year_thanksgiving.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_thanksgiving = (datetime.datetime(this_year + 1, 11, 1) +
                             relativedelta(day=1, weekday=3) +
                             datetime.timedelta(weeks=3)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_thanksgiving, next_thanksgiving.replace(hour=23, minute=59)


def carnaval():
    """
    Returns the next occurrence of Carnaval / Mardi Gras.

    :return: (start, end): (both datetime.datetime) the start and end of next carnaval, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_carnaval = datetime.datetime.combine(easter(this_year) - datetime.timedelta(days=47),
                                                   datetime.datetime.min.time())

    if this_year_carnaval.replace(hour=23, minute=59) > datetime.datetime.now():
        next_carnaval = this_year_carnaval.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_carnaval = datetime.datetime.combine(easter(this_year + 1) - datetime.timedelta(days=47),
                                                  datetime.datetime.min.time()).replace(tzinfo=LOCAL_TIMEZONE)

    return next_carnaval, next_carnaval.replace(hour=23, minute=59)


def fathers_day():
    """
    Returns the next occurrence of Fathers' Day (US Standard)

    :return: (start, end): (both datetime.datetime) the start and end of next fathers day, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_fathers_day = (datetime.datetime(this_year, 6, 1) +
                             relativedelta(day=1, weekday=6) +
                             datetime.timedelta(weeks=2))

    if this_year_fathers_day.replace(hour=23, minute=59) > datetime.datetime.now():
        next_fathers_day = this_year_fathers_day.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_fathers_day = (datetime.datetime(this_year + 1, 6, 1) +
                            relativedelta(day=1, weekday=6) +
                            datetime.timedelta(weeks=2)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_fathers_day, next_fathers_day.replace(hour=23, minute=59)


def labor_day():
    """
    Returns the next occurrence of US Labor Day.

    :return: (start, end): (both datetime.datetime) the start and end of next labor day, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_labor_day = (datetime.datetime(this_year, 9, 1) +
                           relativedelta(day=1, weekday=0))

    if this_year_labor_day.replace(hour=23, minute=59) > datetime.datetime.now():
        next_labor_day = this_year_labor_day.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_labor_day = (datetime.datetime(this_year + 1, 9, 1) +
                          relativedelta(day=1, weekday=0)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_labor_day, next_labor_day.replace(hour=23, minute=59)


def memorial_day():
    """
    Returns the next occurrence of US Memorial Day.

    :return: (start, end): (both datetime.datetime) the start and end of next memorial day, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    # first monday in june minus one week
    this_year_memorial_day = (datetime.datetime(this_year, 6, 1) +
                              relativedelta(day=1, weekday=0) -
                              datetime.timedelta(weeks=1))

    if this_year_memorial_day.replace(hour=23, minute=59) > datetime.datetime.now():
        next_memorial_day = this_year_memorial_day.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_memorial_day = (datetime.datetime(this_year + 1, 6, 1) +
                             relativedelta(day=1, weekday=0) -
                             datetime.timedelta(weeks=1)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_memorial_day, next_memorial_day.replace(hour=23, minute=59)


def mlk_day():
    """
    Returns the next occurrence of Dr. Martin Luther King Jr. Day.

    :return: (start, end): (both datetime.datetime) the start and end of next mlk day, referenced to current tz
    """
    this_year = datetime.datetime.now().year
    this_year_mlk_day = (datetime.datetime(this_year, 1, 1) +
                         relativedelta(day=1, weekday=0) +
                         datetime.timedelta(weeks=2))

    if this_year_mlk_day.replace(hour=23, minute=59) > datetime.datetime.now():
        next_mlk_day = this_year_mlk_day.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        next_mlk_day = (datetime.datetime(this_year + 1, 1, 1) +
                        relativedelta(day=1, weekday=0) +
                        datetime.timedelta(weeks=2)).replace(tzinfo=LOCAL_TIMEZONE)

    return next_mlk_day, next_mlk_day.replace(hour=23, minute=59)

