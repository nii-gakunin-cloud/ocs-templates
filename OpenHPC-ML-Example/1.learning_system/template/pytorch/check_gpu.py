import torch


if not torch.cuda.is_available():
    raise RuntimeError("GPU device not found.")
