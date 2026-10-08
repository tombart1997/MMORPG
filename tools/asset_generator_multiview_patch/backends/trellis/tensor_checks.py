"""Tensor validation used by FlexiCubes without Kaolin's compiled package.

Implements the public shape/dtype/device/throw contract. Mesh extraction itself
still uses the unchanged vendored FlexiCubes implementation and trained decoder.
"""
import torch


def check_tensor(tensor, shape=None, dtype=None, device=None, throw=True):
    error = None
    if shape is not None and (len(shape) != tensor.ndim or
            any(n is not None and n != tensor.shape[i] for i,n in enumerate(shape))):
        error = ValueError('Tensor shape does not match ' + str(shape))
    elif dtype is not None and dtype != tensor.dtype:
        error = TypeError('Tensor dtype does not match ' + str(dtype))
    elif device is not None:
        expected = torch.device(device)
        if expected.type != tensor.device.type or (expected.index is not None and expected.index != tensor.device.index):
            error = TypeError('Tensor device does not match ' + str(device))
    if error:
        if throw:
            raise error
        return False
    return True
