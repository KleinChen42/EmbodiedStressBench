import numpy as np

from embodied_stressbench.perception.depth_lifting import backproject_pixel


def test_backproject_center_pixel():
    k = np.array([[100.0, 0.0, 64.0], [0.0, 100.0, 64.0], [0.0, 0.0, 1.0]])
    p = backproject_pixel(64.0, 64.0, 0.5, k)
    assert np.allclose(p, np.array([0.0, 0.0, 0.5]))
