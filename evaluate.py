"""Оценка на тестовой выборке и проверка порогов ТЗ (Top-1 > 85 %, Top-3 > 95 %).

Дополнительно оценивается политика «вид или род» (ТЗ, раздел 2): если уверенность в виде
ниже порога, система отвечает на уровне рода. Считаются точность на уровне рода и
сводка по порогам (metrics/threshold_sweep.csv).
"""
import json

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix

from .catalog import load_catalog
from .config import ROOT, load_params
from .data import PlantDataset, build_eval_transform, make_loader
from .model import build_model

SWEEP = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def genus_of(classes: list[str]) -> list[str]:
    by_id = {p["id"]: p["genus"] for p in load_catalog()["plants"]}
    return [by_id.get(c, c.split("_")[0]) for c in classes]


@torch.no_grad()
def main() -> None:
    P = load_params()
    dp, tp, ip = P["data"], P["train"], P["infer"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(ROOT / "models/best.pt", map_location=device)
    classes = ckpt["classes"]
    model = build_model(ckpt["backbone"], len(classes), ckpt["dropout"], pretrained=False)
    model.load_state_dict(ckpt["state_dict"]); model.to(device).eval()

    ds = PlantDataset(dp["manifest"], dp["classes"], "test", build_eval_transform(ckpt["image_size"]))
    dl = make_loader(ds, tp["batch_size"], False, tp["num_workers"])
    logits, ys = [], []
    for x, y in dl:
        logits.append(model(x.to(device)).float().cpu()); ys.append(y)
    probs = softmax(torch.cat(logits).numpy())
    y = torch.cat(ys).numpy()

    pred = probs.argmax(1)
    top3 = np.argsort(-probs, axis=1)[:, :3]
    top1 = float((pred == y).mean())
    top3a = float((top3 == y[:, None]).any(axis=1).mean())

    # --- уровень рода ---
    genera_per_class = genus_of(classes)
    genera = sorted(set(genera_per_class))
    gi = {g: i for i, g in enumerate(genera)}
    gidx = np.array([gi[g] for g in genera_per_class])
    G = np.zeros((len(classes), len(genera)), dtype=np.float32)
    G[np.arange(len(classes)), gidx] = 1
    gpred = (probs @ G).argmax(1)
    y_g = gidx[y]
    genus_top1 = float((gpred == y_g).mean())

    conf = probs.max(1)
    rows = []
    for thr in SWEEP:
        sp = conf >= thr
        correct = np.where(sp, pred == y, gpred == y_g)
        rows.append({"threshold": thr, "genus_answer_share": round(float(1 - sp.mean()), 4),
                     "policy_accuracy": round(float(correct.mean()), 4),
                     "species_accuracy_on_species_answers":
                         round(float((pred[sp] == y[sp]).mean()), 4) if sp.any() else None})
    pd.DataFrame(rows).to_csv(ROOT / "metrics/threshold_sweep.csv", index=False)
    thr = ip["confidence_threshold"]
    sp = conf >= thr
    policy_acc = float(np.where(sp, pred == y, gpred == y_g).mean())

    labels = list(range(len(classes)))
    rep = classification_report(y, pred, labels=labels, target_names=classes,
                                output_dict=True, zero_division=0)
    pd.DataFrame(rep).T.to_csv(ROOT / "metrics/per_class_report.csv")
    pd.DataFrame(confusion_matrix(y, pred, labels=labels), index=classes,
                 columns=classes).to_csv(ROOT / "metrics/confusion_matrix.csv")

    res = {"test_top1": top1, "test_top3": top3a, "macro_f1": rep["macro avg"]["f1-score"],
           "genus_top1": genus_top1, "confidence_threshold": thr,
           "genus_answer_share": float(1 - sp.mean()), "policy_accuracy": policy_acc,
           "n_test": int(len(y)), "n_classes": len(classes),
           "meets_tz_top1_gt_0.85": top1 > 0.85, "meets_tz_top3_gt_0.95": top3a > 0.95}
    with open(ROOT / "metrics/test_metrics.json", "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
