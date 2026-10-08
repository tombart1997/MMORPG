"""Numerical checks for the actual Pascal attention port, run in its environment."""
import torch
from sdpa import dense_attention, packed_attention
from tensor_checks import check_tensor


def test_query_chunking_preserves_full_attention():
    torch.manual_seed(11)
    q,k,v = (torch.randn(2,n,3,8) for n in (37,41,41))
    expected = torch.nn.functional.scaled_dot_product_attention(q.transpose(1,2),k.transpose(1,2),v.transpose(1,2)).transpose(1,2)
    assert torch.allclose(dense_attention(q,k,v,chunk=7),expected,rtol=1e-5,atol=1e-6)


def test_packed_attention_never_mixes_sparse_batches():
    torch.manual_seed(12)
    q,k,v = (torch.randn(n,2,8) for n in (12,16,16))
    expected = torch.cat([dense_attention(q[:5][None],k[:7][None],v[:7][None])[0],
                          dense_attention(q[5:][None],k[7:][None],v[7:][None])[0]])
    assert torch.allclose(packed_attention(q,k,v,[5,7],[7,9]),expected)
    modified = v.clone(); modified[7:] += 100
    assert torch.allclose(packed_attention(q,k,modified,[5,7],[7,9])[:5],expected[:5])


def test_real_flexicubes_validator_rejects_wrong_shapes():
    assert check_tensor(torch.zeros(2,3),(None,3),throw=False)
    assert not check_tensor(torch.zeros(2,4),(None,3),throw=False)
    assert not check_tensor(torch.zeros(2,3),(2,3),dtype=torch.int32,throw=False)
