from app.combo import Combo, combo_from_key, combo_key


def test_combo_key_generation() -> None:
    assert combo_key(3, 0, 4, 1, 177) == "3-0-4-1-177"


def test_combo_from_key() -> None:
    assert combo_from_key("3-0-4-1-177") == Combo(3, 0, 4, 1, 177)

