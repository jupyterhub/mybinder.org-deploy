from collections import Counter

from app import rendezvous_rank


def test_50_50_split():
    # check that two buckets with equal weight get used roughly the
    # same number of times
    result = Counter(
        [rendezvous_rank([("a", 1.0), ("b", 1.0)], "key-%i" % i)[0] for i in range(100)]
    )
    # as there is no randomness involved the result should always be the same
    assert result["a"] == 52
    assert result["b"] == 48


def test_80_20_split():
    # check that two buckets with a 80-20 weighting work
    result = Counter(
        [rendezvous_rank([("a", 0.8), ("b", 0.2)], "key-%i" % i)[0] for i in range(100)]
    )
    # as there is no randomness involved the result should always be the same
    assert result["a"] == 75
    assert result["b"] == 25


def test_100_0_split():
    # check that a bucket with zero weight never gets selected
    # the weight of bucket "a" doesn't matter
    result = Counter(
        [rendezvous_rank([("a", 0.8), ("b", 0.)], "key-%i" % i)[0] for i in range(100)]
    )
    assert Counter({"a": 100}) == result
