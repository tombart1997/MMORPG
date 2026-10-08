"""Exact attention with bounded query memory; compatible with Pascal CUDA GPUs."""
import torch
from torch.nn.functional import scaled_dot_product_attention


def dense_attention(q, k, v, chunk=256):
    # Input [B,L,H,C]. Every query still attends to ALL keys; no window approximation.
    q, k, v = (x.transpose(1, 2) for x in (q, k, v))
    return torch.cat([
        scaled_dot_product_attention(q[:, :, i:i+chunk], k, v)
        for i in range(0, q.shape[2], chunk)
    ], dim=2).transpose(1, 2)


def packed_attention(q, k, v, q_lengths, kv_lengths):
    # Variable-length sparse batches stay separate, matching BlockDiagonalMask.
    outputs = []
    qo = ko = 0
    for ql, kl in zip(q_lengths, kv_lengths):
        outputs.append(dense_attention(q[qo:qo+ql][None], k[ko:ko+kl][None],
                                       v[ko:ko+kl][None])[0])
        qo += ql
        ko += kl
    return torch.cat(outputs)
