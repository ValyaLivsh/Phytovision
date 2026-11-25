from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def load_params(path: str | Path = ROOT / "params.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
