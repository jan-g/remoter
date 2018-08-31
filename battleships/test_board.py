import pytest
from battleships.board import Board


def test_board():
    b = Board()
    b.add_counter(0, 0)
    b.add_counter(9, 9)

    b.display()

    assert not b.defeated()


def test_hit():
    b = Board()
    b.add_counter(5, 5)

    assert b.potshot(5, 5) == Board.HIT
    assert b.defeated()
    b.display()


def test_miss():
    b = Board()
    b.add_counter(3, 3)

    assert Board.MISS == b.potshot(1,2)
    assert not b.defeated()


def test_near_miss():
    b = Board()
    b.add_counter(3, 3)

    assert Board.NEAR == b.potshot(2, 2)
    assert not b.defeated()


def test_ship_must_lie_on_board():
    b = Board()

    with pytest.raises(ValueError):
        b.add_ship(0, 0, -1, 0, 2)

    with pytest.raises(ValueError):
        b.add_ship(1, 1, 0, -1, 3)

    with pytest.raises(ValueError):
        b.add_ship(9, 9, 1, 0, 2)

    with pytest.raises(ValueError):
        b.add_ship(0, 0, 0, 1, 11)


def test_ship_must_not_be_adjacent_to_another():
    b = Board()
    b.add_ship(5, 5, 0, 0, 1)

    for dx in -1, 0, 1:
        for dy in -1, 0, 1:
            with pytest.raises(ValueError):
                b.add_ship(5 + dx, 5 + dy, 0, 0, 1)
