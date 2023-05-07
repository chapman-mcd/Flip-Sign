import flip_sign.helpers as hlp


def test_great_circle():
    # arbitrary test cases from online great-circle calculator
    # allowing 10km slack due to different earth radius assumption

    assert (hlp.great_circle_distance(27.0, 28.0, 29.0, 30.0) - 296.34) < 10

    assert (hlp.great_circle_distance(20.0, 30.0, -40.0, -50.0) - 10603.28) < 10
