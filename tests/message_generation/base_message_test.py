from flip_sign.message_generation import Message


def test_display_always():
    for i in range(10):
        assert Message(1.0)
        assert not Message(1.0).init_failure


def test_display_never():
    for i in range(10):
        assert not Message(0.0)
        assert not Message(0.0).init_failure


def test_display_sometimes():
    total = 0
    for i in range(50):
        if Message(0.5):
            total += 1
    assert total < 40
    assert total > 10
    assert not Message(0.5).init_failure
