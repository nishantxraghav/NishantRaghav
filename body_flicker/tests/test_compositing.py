import numpy as np

from flicker.compositing import over, over_premultiplied, premultiply


def solid(value):
    return np.full((40, 60, 3), value, dtype=np.uint8)


def alpha_patch(value):
    alpha = np.zeros((40, 60), dtype=np.uint8)
    alpha[10:20, 15:30] = value
    return alpha


def test_over_only_changes_pixels_the_alpha_covers():
    result = over(solid(10), solid(200), alpha_patch(255))
    assert (result[10:20, 15:30] == 200).all()
    result[10:20, 15:30] = 10
    assert np.array_equal(result, solid(10))


def test_over_blends_partial_alpha():
    result = over(solid(0), solid(200), alpha_patch(128))
    assert abs(int(result[15, 20, 0]) - 100) <= 1


def test_empty_alpha_returns_an_equal_copy():
    base = solid(10)
    result = over(base, solid(200), np.zeros((40, 60), dtype=np.uint8))
    assert np.array_equal(result, base)
    assert result is not base


def test_blending_never_writes_to_the_inputs():
    base, colour = solid(10), solid(200)
    over(base, colour, alpha_patch(255))
    over_premultiplied(base, premultiply(colour, alpha_patch(128)), alpha_patch(128))
    assert np.array_equal(base, solid(10))
    assert np.array_equal(colour, solid(200))


def test_premultiplied_matches_plain_blending():
    alpha = alpha_patch(128)
    plain = over(solid(40), solid(200), alpha)
    fast = over_premultiplied(solid(40), premultiply(solid(200), alpha), alpha)
    assert np.abs(plain.astype(int) - fast.astype(int)).max() <= 1
