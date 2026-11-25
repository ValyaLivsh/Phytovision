"""Обучение: тонкая настройка в две фазы (голова -> вся сеть)."""
import copy
import json
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import default_collate
from torchvision.transforms import v2
from tqdm import tqdm

from .config import ROOT, load_params
from .data import PlantDataset, build_eval_transform, build_train_transform, make_loader
from .metrics import topk_correct
from .model import build_model, head_parameters, set_backbone_trainable


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def make_mix_collate(num_classes: int, tp: dict):
    mixers = []
    if tp["mixup_alpha"] > 0:
        mixers.append(v2.MixUp(alpha=tp["mixup_alpha"], num_classes=num_classes))
    if tp["cutmix_alpha"] > 0:
        mixers.append(v2.CutMix(alpha=tp["cutmix_alpha"], num_classes=num_classes))
    if not mixers:
        return default_collate
    mix = v2.RandomChoice(mixers)

    def collate(batch):
        if random.random() < tp["mix_prob"]:
            return mix(*default_collate(batch))
        x, y = default_collate(batch)
        return x, nn.functional.one_hot(y, num_classes).float()
    return collate


@torch.no_grad()
def evaluate(model, loader, device) -> dict:
    model.eval()
    n, c1, c3, loss_sum = 0, 0, 0, 0.0
    ce = nn.CrossEntropyLoss()
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            out = model(x)
        loss_sum += ce(out.float(), y).item() * len(y)
        hits = topk_correct(out, y)
        c1 += hits[1]; c3 += hits[3]; n += len(y)
    return {"loss": loss_sum / n, "top1": c1 / n, "top3": c3 / n}


def run_phase(name, model, epochs, lr, tl, vl, tp, device, state):
    if epochs <= 0:
        return
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=tp["weight_decay"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    crit = nn.CrossEntropyLoss(label_smoothing=tp["label_smoothing"])
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    bad = 0
    for ep in range(1, epochs + 1):
        model.train()
        run = 0.0
        for x, y in tqdm(tl, desc=f"{name} {ep}/{epochs}", leave=False):
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                loss = crit(model(x).float(), y)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            nn.utils.clip_grad_norm_(params, 1.0)
            scaler.step(opt); scaler.update()
            run += loss.item()
        sched.step()
        m = evaluate(model, vl, device)
        m.update(phase=name, epoch=ep, train_loss=run / len(tl))
        state["history"].append(m)
        print(f"[{name}] ep{ep}: loss={m['train_loss']:.3f} "
              f"val top1={m['top1']:.4f} top3={m['top3']:.4f}")
        if m["top1"] > state["best"]["top1"]:
            state["best"] = m
            state["weights"] = copy.deepcopy(model.state_dict())
            bad = 0
        else:
            bad += 1
            if bad >= tp["patience"]:
                print("Ранняя остановка"); break


def main() -> None:
    P = load_params()
    dp, mp, tp = P["data"], P["model"], P["train"]
    seed_everything(tp["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    size = mp["image_size"]
    train_ds = PlantDataset(dp["manifest"], dp["classes"], "train", build_train_transform(size))
    val_ds = PlantDataset(dp["manifest"], dp["classes"], "val", build_eval_transform(size))
    nc = len(train_ds.classes)
    tl = make_loader(train_ds, tp["batch_size"], True, tp["num_workers"],
                     make_mix_collate(nc, tp))
    vl = make_loader(val_ds, tp["batch_size"], False, tp["num_workers"])

    model = build_model(mp["backbone"], nc, mp["dropout"]).to(device)
    state = {"history": [], "best": {"top1": -1.0}, "weights": None}

    set_backbone_trainable(model, False)
    run_phase("head", model, tp["epochs_head"], tp["lr_head"], tl, vl, tp, device, state)
    set_backbone_trainable(model, True)
    run_phase("finetune", model, tp["epochs_finetune"], tp["lr_backbone"], tl, vl, tp, device, state)

    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "metrics").mkdir(exist_ok=True)
    torch.save({"state_dict": state["weights"], "classes": train_ds.classes,
                "backbone": mp["backbone"], "image_size": size,
                "dropout": mp["dropout"]}, ROOT / "models/best.pt")
    pd.DataFrame(state["history"]).to_csv(ROOT / "metrics/train_history.csv", index=False)
    b = state["best"]
    with open(ROOT / "metrics/train_metrics.json", "w") as f:
        json.dump({"best_val_top1": b["top1"], "best_val_top3": b["top3"],
                   "best_epoch": b["epoch"], "best_phase": b["phase"],
                   "num_classes": nc}, f, indent=2)


if __name__ == "__main__":
    main()
