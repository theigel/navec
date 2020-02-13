# encoding: utf8

from __future__ import absolute_import, unicode_literals

from tempfile import NamedTemporaryFile

import numpy as np
import pytest

from navec import Navec
from navec.meta import Meta
from navec.vocab import Vocab
from navec.pq import PQ


@pytest.fixture
def emb():
    meta = Meta(
        id='test_1B_3k_6d_2q'
    )
    pq = PQ(
        vectors=3,
        dim=6,
        qdim=2,
        # 1 0 0 | 1 0 0
        # 0 1 1 | 0 0 0
        # 0 0 0 | 0 1 0
        centroids=3,
        indexes=np.array([  # vectors x qdim
            [0, 1],
            [1, 0],
            [2, 2]
        ]).astype(np.uint8),
        codes=np.array([  # qdim x centroids x chunk
            [[1, 0, 0], [0, 1, 1], [0, 0, 0]],
            [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        ]).astype(np.float32),
    )
    vocab = Vocab(
        words=['a', 'b', 'c'],
        counts=[1, 2, 3]
    )
    return Navec(meta, vocab, pq)


def test_dump_load(emb):
    with NamedTemporaryFile() as file:
        path = file.name
        emb.dump(path)
        Navec.load(path)


def test_get(emb):
    assert np.array_equal(
        emb.get('a'),
        np.array([1., 0., 0., 1., 0., 0.])
    )
    assert emb.get('d') is None


def test_sim(emb):
    assert emb.sim('a', 'b') == 0.


def test_gensim(emb):
    model = emb.as_gensim
    assert model.most_similar('a') == [
        ('b', 0.),
        ('c', 0.)
    ]


def test_gzip():
    # check python versions return use same compression
    from .gzip import compress, decompress

    bytes = 'навек'.encode('utf8')
    data = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\xbb\xb0\xf7\xc2\x86\x0b\x9b.l\xbd\xb0\x0b\x00\xfd\xa4\xac\x14\n\x00\x00\x00'
    assert compress(bytes) == data
    assert decompress(data) == bytes


def test_top(emb):
    words = emb.vocab.top(2)
    sample = emb.sampled(words)
    assert len(sample.pq.indexes) == 2
    assert sample.sim('b', 'c') == emb.sim('b', 'c')
    assert sample.vocab.get('a') is None


def test_shape(emb):
    assert emb.pq.shape == (emb.pq.vectors, emb.pq.dim)
