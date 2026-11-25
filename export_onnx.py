"""Экспорт в переносимый формат ONNX (ТЗ п. 5.5) и проверка эквивалентности."""
import json

import numpy as np
import onnxruntime as ort
import torch

from .catalog import load_catalog, plants_by_id
from .config import IMAGENET_MEAN, IMAGENET_STD, ROOT, load_params
from .model import build_model


def main() -> None:
    P = load_params()
    ckpt = torch.load(ROOT / "models/best.pt", map_location="cpu")
    classes, size = ckpt["classes"], ckpt["image_size"]
    model = build_model(ckpt["backbone"], len(classes), ckpt["dropout"], pretrained=False)
    model.load_state_dict(ckpt["state_dict"]); model.eval()

    out = ROOT / "models/plant_classifier.onnx"
    dummy = torch.randn(1, 3, size, size)
    kwargs = dict(input_names=["image"], output_names=["logits"],
                  dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
                  opset_version=17)
    try:  # новые версии PyTorch: используем классический экспортёр
        torch.onnx.export(model, dummy, out, dynamo=False, **kwargs)
    except TypeError:  # старые версии не знают аргумент dynamo
        torch.onnx.export(model, dummy, out, **kwargs)

    sess = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
    x = torch.randn(2, 3, size, size)
    ref = model(x).detach().numpy()
    got = sess.run(None, {"image": x.numpy()})[0]
    diff = float(np.abs(ref - got).max())
    assert diff < 1e-3, f"ONNX расходится с PyTorch: {diff}"
    print(f"ONNX OK, max|diff|={diff:.2e}")

    by_id = plants_by_id()
    unknown = [c for c in classes if c not in by_id]
    assert not unknown, f"Классы отсутствуют в catalog/plants.yaml: {unknown}"
    genera = load_catalog()["genera"]
    meta = {"classes": classes, "image_size": size, "backbone": ckpt["backbone"],
            "mean": IMAGENET_MEAN, "std": IMAGENET_STD,
            "top_k": P["infer"]["top_k"],
            "confidence_threshold": P["infer"]["confidence_threshold"],
            "latin": {c: by_id[c]["latin"] for c in classes},
            "names_ru": {c: by_id[c]["ru"] for c in classes},
            "genus": {c: by_id[c]["genus"] for c in classes},
            "genera_ru": {g: genera[g]["ru"] for g in sorted({by_id[c]["genus"] for c in classes})}}
    with open(ROOT / "models/model_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
