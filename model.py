"""Перенос знаний (ТЗ п. 5.1): бэкбон с весами ImageNet + новая голова."""
import torch.nn as nn
from torchvision import models


def build_model(backbone: str, num_classes: int, dropout: float = 0.3,
                pretrained: bool = True) -> nn.Module:
    weights = models.get_model_weights(backbone).DEFAULT if pretrained else None
    model = models.get_model(backbone, weights=weights)
    _replace_head(model, num_classes, dropout)
    return model


def _replace_head(model: nn.Module, num_classes: int, dropout: float) -> None:
    if hasattr(model, "fc"):                      # ResNet и др.
        model.fc = nn.Sequential(nn.Dropout(dropout),
                                 nn.Linear(model.fc.in_features, num_classes))
    elif hasattr(model, "classifier"):            # EfficientNet, ConvNeXt
        seq = model.classifier
        if isinstance(seq, nn.Sequential):
            idx = max(i for i, m in enumerate(seq) if isinstance(m, nn.Linear))
            seq[idx] = nn.Linear(seq[idx].in_features, num_classes)
            for m in seq:
                if isinstance(m, nn.Dropout):
                    m.p = dropout
        else:
            model.classifier = nn.Sequential(
                nn.Dropout(dropout), nn.Linear(seq.in_features, num_classes))
    else:
        raise ValueError("Не удалось определить голову классификатора")


def head_parameters(model: nn.Module):
    head = model.fc if hasattr(model, "fc") else model.classifier
    return list(head.parameters())


def set_backbone_trainable(model: nn.Module, trainable: bool) -> None:
    head_ids = {id(p) for p in head_parameters(model)}
    for p in model.parameters():
        if id(p) not in head_ids:
            p.requires_grad = trainable
