"""
train_model.py — GPU-optimised training for BubbleCNN-V2
---------------------------------------------------------
Usage:
    1. python generate_bubble_dataset.py   (creates 30k-image dataset)
    2. python train_model.py               (trains and saves bubble_model.pth)

Improvements over v1:
  - Focal Loss (α=0.25, γ=2.0) — penalises easy samples less, focuses on
    hard / lightly-filled bubbles — the main source of errors.
  - Cosine Annealing LR — smooth decay, better final accuracy.
  - Label smoothing (ε=0.05) — prevents over-confident outputs on extreme cases.
  - Mixed Precision (AMP) — 2× faster on 8 GB NVIDIA GPU, lower VRAM.
  - num_workers=4, pin_memory=True for fast GPU data transfer.
  - Stronger augmentation: RandomErasing + GaussianBlur per-image.
  - 25 epochs, patience=6 early stopping.

Expected GPU time  : ~2–4 minutes (RTX 3060/4060 8 GB)
Expected val accuracy: ≥ 99%
"""

import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
import cv2
import numpy as np
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
DATA_DIR     = Path(__file__).parent / "bubble_dataset"
MODEL_PATH   = Path(__file__).parent / "bubble_model.pth"
EPOCHS       = 25
BATCH_SIZE   = 128          # larger batch benefits from GPU / AMP
LR           = 1e-3
WEIGHT_DECAY = 1e-4
TRAIN_SPLIT  = 0.85
PATIENCE     = 6
LABEL_SMOOTH = 0.05         # label smoothing epsilon
# Focal loss hyper-params
FOCAL_ALPHA  = 0.25
FOCAL_GAMMA  = 2.0

DEVICE       = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_AMP      = (DEVICE.type == "cuda")   # Mixed precision only on CUDA


# ── Focal Loss ────────────────────────────────────────────────────────────────

class FocalLoss(nn.Module):
    """
    Binary Focal Loss: FL(p) = -α (1-p)^γ log(p)
    Focuses training on hard examples (lightly filled / near-threshold bubbles).
    """
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0,
                 label_smooth: float = 0.05):
        super().__init__()
        self.alpha  = alpha
        self.gamma  = gamma
        self.smooth = label_smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # Apply label smoothing
        target_s = target * (1 - self.smooth) + 0.5 * self.smooth

        bce = nn.functional.binary_cross_entropy(pred, target_s, reduction='none')
        p_t = pred * target_s + (1 - pred) * (1 - target_s)
        focal_weight = self.alpha * (1 - p_t) ** self.gamma
        loss = (focal_weight * bce).mean()
        return loss


# ── Dataset ───────────────────────────────────────────────────────────────────

class BubbleDataset(Dataset):
    """
    Loads 28×28 greyscale images:
        bubble_dataset/filled/  → label 1.0
        bubble_dataset/empty/   → label 0.0
    """
    def __init__(self, root: Path, transform=None):
        self.samples   = []
        self.transform = transform

        filled_dir = root / "filled"
        empty_dir  = root / "empty"

        if not filled_dir.exists() or not empty_dir.exists():
            raise FileNotFoundError(
                f"Dataset not found at '{root}'.\n"
                "Run 'python generate_bubble_dataset.py' first."
            )

        for img_path in sorted(filled_dir.glob("*.png")):
            self.samples.append((str(img_path), 1.0))
        for img_path in sorted(empty_dir.glob("*.png")):
            self.samples.append((str(img_path), 0.0))

        if not self.samples:
            raise RuntimeError(f"No images found in '{root}'.")

        n_filled = sum(1 for _, l in self.samples if l == 1.0)
        n_empty  = sum(1 for _, l in self.samples if l == 0.0)
        print(f"Dataset: {len(self.samples)} images ({n_filled} filled, {n_empty} empty)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            img = np.zeros((28, 28), dtype=np.uint8)

        img_tensor = torch.tensor(img.astype(np.float32) / 255.0).unsqueeze(0)  # (1,28,28)

        if self.transform:
            img_tensor = self.transform(img_tensor)

        return img_tensor, torch.tensor([[label]], dtype=torch.float32)


# ── Model Architecture ─────────────────────────────────────────────────────────

class _SEBlock(nn.Module):
    """Squeeze-Excitation channel attention."""
    def __init__(self, channels, reduction=8):
        super().__init__()
        self.se = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels, max(1, channels // reduction)),
            nn.ReLU(inplace=True),
            nn.Linear(max(1, channels // reduction), channels),
            nn.Sigmoid(),
        )
    def forward(self, x):
        w = self.se(x).view(x.size(0), x.size(1), 1, 1)
        return x * w


class BubbleCNNV2(nn.Module):
    """
    3-block CNN with SE attention for binary bubble classification.
    Input:  (B, 1, 28, 28)
    Output: (B, 1) — probability of being FILLED
    """
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 1→32
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
            nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(True),
            nn.MaxPool2d(2, 2),              # → (32, 14, 14)
            nn.Dropout2d(0.15),

            # Block 2: 32→64
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.MaxPool2d(2, 2),              # → (64, 7, 7)
            nn.Dropout2d(0.15),

            # Block 3: 64→128 + SE
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(True),
            _SEBlock(128),
            nn.Dropout2d(0.10),
        )
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),   # → (128, 1, 1)
            nn.Flatten(),              # → 128
            nn.Linear(128, 64), nn.ReLU(True), nn.Dropout(0.3),
            nn.Linear(64, 1), nn.Sigmoid()
        )

    def forward(self, x):
        return self.classifier(self.features(x))


# ── Training ──────────────────────────────────────────────────────────────────

def train():
    print(f"{'='*60}")
    print(f"Training on : {DEVICE}")
    if USE_AMP:
        print(f"Mixed precision (AMP): ENABLED")
    print(f"Model output: {MODEL_PATH}")
    print(f"{'='*60}\n")

    # Augmentation (training only)
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomAffine(degrees=5, translate=(0.05, 0.05)),
        transforms.RandomApply([transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0))], p=0.3),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.08), ratio=(0.5, 2.0)),
    ])

    full_dataset = BubbleDataset(DATA_DIR, transform=None)
    n_train = int(len(full_dataset) * TRAIN_SPLIT)
    n_val   = len(full_dataset) - n_train
    train_ds, val_ds = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(42)
    )

    class AugmentedSubset(Dataset):
        def __init__(self, subset, transform):
            self.subset    = subset
            self.transform = transform
        def __len__(self): return len(self.subset)
        def __getitem__(self, idx):
            img, label = self.subset[idx]
            if self.transform:
                img = self.transform(img)
            return img, label

    # num_workers=4 and pin_memory for fast GPU data loading
    num_workers = 4 if DEVICE.type == "cuda" else 0
    train_loader = DataLoader(
        AugmentedSubset(train_ds, train_transform),
        batch_size=BATCH_SIZE, shuffle=True,
        num_workers=num_workers, pin_memory=USE_AMP,
        persistent_workers=(num_workers > 0)
    )
    val_loader = DataLoader(
        val_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=num_workers, pin_memory=USE_AMP,
        persistent_workers=(num_workers > 0)
    )

    model     = BubbleCNNV2().to(DEVICE)
    criterion = FocalLoss(alpha=FOCAL_ALPHA, gamma=FOCAL_GAMMA, label_smooth=LABEL_SMOOTH)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)

    # Mixed precision scaler (GPU only)
    scaler = torch.amp.GradScaler(enabled=USE_AMP)

    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"BubbleCNN-V2 parameters: {params:,}\n")
    print(f"{'Epoch':>6}  {'Train Loss':>11}  {'Val Loss':>10}  {'Val Acc':>9}  {'LR':>10}")
    print("─" * 65)

    best_val_loss     = float('inf')
    best_val_acc      = 0.0
    patience_counter  = 0

    for epoch in range(1, EPOCHS + 1):
        # ── Train ──────────────────────────────────────────────────────────
        model.train()
        train_loss = 0.0
        for imgs, labels in train_loader:
            imgs   = imgs.to(DEVICE, non_blocking=True)
            labels = labels.to(DEVICE, non_blocking=True).view(-1, 1)

            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast(device_type=DEVICE.type, enabled=USE_AMP):
                preds = model(imgs)
                loss  = criterion(preds, labels)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item() * imgs.size(0)

        train_loss /= n_train
        scheduler.step()

        # ── Validate ──────────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
        correct  = 0
        total    = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs   = imgs.to(DEVICE, non_blocking=True)
                labels = labels.to(DEVICE, non_blocking=True).view(-1, 1)
                with torch.amp.autocast(device_type=DEVICE.type, enabled=USE_AMP):
                    preds = model(imgs)
                    loss  = criterion(preds, labels)
                val_loss += loss.item() * imgs.size(0)
                predicted = (preds > 0.5).float()
                correct   += (predicted == (labels > 0.5).float()).sum().item()
                total     += labels.size(0)

        val_loss /= n_val
        val_acc   = 100.0 * correct / total if total > 0 else 0.0
        current_lr = optimizer.param_groups[0]['lr']

        print(f"{epoch:>6}  {train_loss:>11.5f}  {val_loss:>10.5f}  "
              f"{val_acc:>8.2f}%  {current_lr:>10.6f}")

        # ── Best model save ───────────────────────────────────────────────
        if val_loss < best_val_loss:
            best_val_loss    = val_loss
            best_val_acc     = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"         ✓ Saved (val_loss={best_val_loss:.5f}, val_acc={best_val_acc:.2f}%)")
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"\nEarly stopping (no improvement for {PATIENCE} epochs).")
                break

    print("─" * 65)
    print(f"\nTraining complete.")
    print(f"Best val loss : {best_val_loss:.5f}")
    print(f"Best val acc  : {best_val_acc:.2f}%")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"\nNext: restart the Flask server — it will auto-load the new model.")


if __name__ == "__main__":
    train()
