import pytest

from collections import deque

@pytest.fixture
def example_actions():
    return deque([0, 2, 2, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 6, 0, 0, 0, 6, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1,
                     1, 6, 3, 0, 0, 0, 5, 5, 5, 1, 1, 1, 1, 1, 1, 4, 2, 2, 2, 2, 2, 2, 7, 7, 7, 7])
