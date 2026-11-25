import torch


@torch.no_grad()
def topk_correct(logits: torch.Tensor, target: torch.Tensor, ks=(1, 3)) -> dict:
    maxk = min(max(ks), logits.size(1))
    top = logits.topk(maxk, dim=1).indices
    hit = top.eq(target.view(-1, 1))
    return {k: hit[:, :k].any(dim=1).sum().item() for k in ks}
