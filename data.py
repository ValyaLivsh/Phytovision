"""Датасет и расширенная синтетическая аугментация (ТЗ п. 5.2).

Имитируются условия полевой съёмки: гетерогенный фон (RandomResizedCrop,
RandomErasing), свет (ColorJitter, Gamma), смазывание (Gaussian/Motion blur),
ракурс (Perspective, Rotation), шум сенсора, JPEG-артефакты.
"""
import io
import json
import math
import random

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader, Dataset, default_collate
from torchvision.transforms import v2

from .config import IMAGENET_MEAN, IMAGENET_STD, ROOT


class MotionBlur:
    """Линейное смазывание (дрожание камеры) со случайным углом.

    Реализовано через усреднение сдвинутых копий (PIL.ImageFilter.Kernel
    поддерживает только ядра 3x3 и 5x5).
    """
    def __init__(self, max_size: int = 15, p: float = 0.2):
        self.max_size, self.p = max_size, p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        k = random.choice(range(5, self.max_size + 1, 2))
        c = k // 2
        angle = random.uniform(0, math.pi)
        dx, dy = math.cos(angle), math.sin(angle)
        taps = {(round(t * dy), round(t * dx)) for t in np.linspace(-c, c, 4 * k)}
        arr = np.asarray(img, dtype=np.float32)
        h, w = arr.shape[:2]
        pad = np.pad(arr, ((c, c), (c, c), (0, 0)), mode="reflect")
        acc = np.zeros_like(arr)
        for oy, ox in taps:
            acc += pad[c + oy:c + oy + h, c + ox:c + ox + w]
        acc /= len(taps)
        return Image.fromarray(acc.clip(0, 255).astype(np.uint8))


class RandomJPEG:
    """Артефакты сжатия (снимки со смартфонов/мессенджеров)."""
    def __init__(self, quality=(30, 90), p: float = 0.3):
        self.quality, self.p = quality, p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=random.randint(*self.quality))
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class GaussianNoise:
    def __init__(self, sigma=(0.01, 0.06), p: float = 0.3):
        self.sigma, self.p = sigma, p

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        if random.random() > self.p:
            return x
        return (x + torch.randn_like(x) * random.uniform(*self.sigma)).clamp(0, 1)


def build_train_transform(size: int) -> v2.Compose:
    return v2.Compose([
        v2.RandomResizedCrop(size, scale=(0.4, 1.0), ratio=(0.75, 1.33),
                             interpolation=v2.InterpolationMode.BICUBIC),
        v2.RandomHorizontalFlip(),
        v2.RandomApply([v2.RandomRotation(25)], p=0.5),
        v2.RandomPerspective(distortion_scale=0.3, p=0.3),
        v2.ColorJitter(brightness=0.5, contrast=0.4, saturation=0.4, hue=0.05),
        v2.RandomAdjustSharpness(sharpness_factor=0.2, p=0.2),
        v2.RandomApply([v2.GaussianBlur(9, (0.1, 3.0))], p=0.25),
        MotionBlur(p=0.15),
        RandomJPEG(p=0.3),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        GaussianNoise(p=0.3),
        v2.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        v2.RandomErasing(p=0.25, scale=(0.02, 0.2), value="random"),
    ])


def build_eval_transform(size: int) -> v2.Compose:
    return v2.Compose([
        v2.Resize(int(size * 1.14), interpolation=v2.InterpolationMode.BICUBIC),
        v2.CenterCrop(size),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class PlantDataset(Dataset):
    def __init__(self, manifest: str, classes_path: str, split: str, transform):
        df = pd.read_csv(ROOT / manifest)
        self.df = df[df["split"] == split].reset_index(drop=True)
        with open(ROOT / classes_path, encoding="utf-8") as f:
            self.classes = json.load(f)
        self.idx = {c: i for i, c in enumerate(self.classes)}
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, i: int):
        row = self.df.iloc[i]
        img = Image.open(ROOT / row["path"]).convert("RGB")
        return self.transform(img), self.idx[row["label"]]


def make_loader(ds: Dataset, batch_size: int, shuffle: bool, workers: int,
                collate=None) -> DataLoader:
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle,
                      num_workers=workers, pin_memory=torch.cuda.is_available(),
                      drop_last=shuffle, collate_fn=collate or default_collate,
                      persistent_workers=workers > 0)
