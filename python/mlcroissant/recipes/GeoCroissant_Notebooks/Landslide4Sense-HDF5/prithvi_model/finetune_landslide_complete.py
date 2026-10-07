#!/usr/bin/env python3
"""Complete fine-tuning script for Prithvi-EO-1.0-100M on Landslide4Sense dataset."""

import json
from pathlib import Path
import random
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
from prithvi_mae import PrithviMAE
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_recall_fscore_support
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import torchvision.transforms.functional as F
from tqdm import tqdm
import wandb

# Add the current directory to path to import prithvi_mae
sys.path.append(".")


class MultispectralTransforms:
    """Custom transforms for multispectral data (14 channels).

    This class provides transformation utilities specifically designed for working with
    multispectral image data containing 14 channels, such as that used in the
    Landslide4Sense dataset.
    """

    @staticmethod
    def random_horizontal_flip(img, p=0.5):
        """Random horizontal flip for multispectral images."""
        if random.random() < p:
            return torch.flip(img, [2])  # Flip width dimension
        return img

    @staticmethod
    def random_vertical_flip(img, p=0.5):
        """Random vertical flip for multispectral images."""
        if random.random() < p:
            return torch.flip(img, [1])  # Flip height dimension
        return img

    @staticmethod
    def random_rotation(img, max_angle=10):
        """Random rotation for multispectral images."""
        angle = random.uniform(-max_angle, max_angle)
        # Apply rotation to each channel
        rotated = torch.zeros_like(img)
        for i in range(img.shape[0]):
            rotated[i] = F.rotate(
                img[i : i + 1], angle, interpolation=F.InterpolationMode.BILINEAR
            ).squeeze(0)
        return rotated

    @staticmethod
    def random_brightness_contrast(img, brightness_factor=0.1, contrast_factor=0.1):
        """Random brightness and contrast adjustment for multispectral data."""
        # Apply to each channel independently
        adjusted = torch.zeros_like(img)
        for i in range(img.shape[0]):
            channel = img[i : i + 1]
            # Brightness adjustment
            if random.random() < 0.5:
                brightness = random.uniform(
                    1 - brightness_factor, 1 + brightness_factor
                )
                channel = channel * brightness
            # Contrast adjustment
            if random.random() < 0.5:
                contrast = random.uniform(1 - contrast_factor, 1 + contrast_factor)
                mean = channel.mean()
                channel = (channel - mean) * contrast + mean
            adjusted[i] = channel.squeeze(0)
        return adjusted


class LandslideDataset(Dataset):
    """Landslide4Sense dataset loader using proper metadata paths."""

    def __init__(self, metadata_path, split="train", transform=None):
        """Initialize the Landslide4Sense dataset.

        Args:
            metadata_path: Path to the metadata JSON file
            split: Dataset split to use ('train', 'val', or 'test')
            transform: Optional transforms to apply to the data
        """
        self.metadata_path = metadata_path
        self.split = split
        self.transform = transform

        # Load metadata
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

        # Get repo path from metadata
        self.repo_path = Path(self.metadata["distribution"][0]["path"])

        # Get file listings from metadata
        self.image_files = self.metadata["geocr:fileListing"]["images"][split]
        self.annotation_files = self.metadata["geocr:fileListing"]["annotations"][split]

        print(
            "Found {len(self.image_files)} images and {len(self.annotation_files)}"
            " annotations for {split} split"
        )

    def __len__(self):
        """Get the total number of samples in the dataset.

        Returns:
            int: Number of samples in the dataset
        """
        return len(self.image_files)

    def __getitem__(self, idx):
        """Get a sample from the dataset.

        Args:
            idx: Index of the sample to retrieve

        Returns:
            dict: Dictionary containing image and label tensors, with any transformations applied
        """
        # Get file paths from metadata
        image_file = self.repo_path / self.image_files[idx]
        annotation_file = self.repo_path / self.annotation_files[idx]

        # Load image data using h5py
        try:
            with h5py.File(image_file, "r") as f:
                # Get the 'img' dataset
                data = f["img"][:]

                # Check shape and transpose if needed
                # Usually HDF5 gives (bands, H, W)
                if data.shape[0] <= 20:  # heuristic for (bands, H, W)
                    image_data = np.transpose(data, (1, 2, 0))  # (H, W, bands)
                else:
                    image_data = data  # already (H, W, bands)

        except Exception:
            print("Error loading image {image_file}: {e}")
            image_data = np.zeros((128, 128, 14))

        # Load annotation data using h5py
        try:
            with h5py.File(annotation_file, "r") as f:
                # Get the 'mask' dataset
                mask_data = f["mask"][:]
        except Exception as e:
            print(f"Error loading annotation {annotation_file}: {e}")
            mask_data = np.zeros((128, 128))

        # Convert to torch tensors
        # Image: (H, W, C) -> (C, H, W) for PyTorch
        image_tensor = torch.from_numpy(image_data).float().permute(2, 0, 1)

        # Normalize image data per band
        for i in range(image_tensor.shape[0]):
            band = image_tensor[i]
            if band.std() > 0:
                image_tensor[i] = (band - band.mean()) / band.std()

        # Annotation: (H, W) -> binary classification
        # Convert to binary: any pixel > 0 is landslide
        annotation_tensor = torch.from_numpy(mask_data).float()
        is_landslide = torch.any(annotation_tensor > 0).float()

        # Apply transforms if specified
        if self.transform:
            image_tensor = self.transform(image_tensor)

        return {
            "image": image_tensor,
            "label": is_landslide,
            "image_path": str(image_file),
            "annotation_path": str(annotation_file),
        }


class PrithviLandslideClassifier(nn.Module):
    """Prithvi-based classifier for landslide detection using the actual Prithvi model."""

    def __init__(self, prithvi_model, num_classes=2):
        """Initialize the Prithvi-based landslide classifier.

        Args:
            prithvi_model: Pre-trained Prithvi model to use as feature extractor
            num_classes: Number of classification classes (default: 2 for binary classification)
        """
        super().__init__()

        # Use the actual Prithvi model as feature extractor
        self.prithvi = prithvi_model

        # Freeze Prithvi parameters for feature extraction
        for param in self.prithvi.parameters():
            param.requires_grad = False

        # Select optimal 6 bands for landslide detection:
        # B02 (Blue), B03 (Green), B04 (Red), B07 (NIR), B10 (SWIR), B12 (Slope)
        # These bands provide the most relevant information for landslide detection
        self.band_indices = torch.tensor([1, 2, 3, 7, 10, 12])  # 0-indexed

        # Add classification head
        self.classifier = nn.Sequential(
            nn.Linear(768, 512),  # 768 is embed_dim from config
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        """Forward pass of the landslide classifier model.

        Args:
            x: Input tensor of shape [B, 14, H, W] containing multispectral satellite data

        Returns:
            torch.Tensor: Classification logits of shape [B, num_classes]
        """
        # Select the optimal 6 bands for landslide detection
        # x shape: [B, 14, H, W] -> [B, 6, H, W]
        x = x[:, self.band_indices, :, :]

        # Add time dimension if needed (Prithvi expects 5D: B, C, T, H, W)
        if len(x.shape) == 4:
            x = x.unsqueeze(2)  # Add time dimension

        # Get features from Prithvi encoder
        features = self.prithvi.forward_features(x)

        # Use the last layer features (CLS token)
        cls_features = features[-1][:, 0, :]  # [B, 1, 768] -> [B, 768]

        # Classify
        output = self.classifier(cls_features)
        return output


def load_pretrained_prithvi(checkpoint_path, config):
    """Load pre-trained Prithvi model from checkpoint.

    Args:
        checkpoint_path: Path to the Prithvi model checkpoint file
        config: Dictionary containing model configuration parameters

    Returns:
        PrithviMAE: Initialized Prithvi model with pre-trained weights
    """
    print("Loading pre-trained Prithvi model from: {checkpoint_path}")

    # Create model with config
    model = PrithviMAE(**config)

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    # Remove pos_embed keys as they are fixed
    for k in list(checkpoint.keys()):
        if "pos_embed" in k:
            del checkpoint[k]

    # Load state dict
    model.load_state_dict(checkpoint, strict=False)
    print("Pre-trained weights loaded successfully!")

    return model


def train_model(model, train_loader, val_loader, num_epochs=10, device="cuda"):
    """Train the landslide classifier model.

    Args:
        model: The PrithviLandslideClassifier model to train
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        num_epochs: Number of training epochs (default: 10)
        device: Device to train on ('cuda' or 'cpu', default: 'cuda')

    Returns:
        float: Best validation F1 score achieved during training
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    best_f1 = 0.0
    train_losses = []
    val_losses = []
    train_f1s = []
    val_f1s = []

    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_preds = []
        train_labels = []

        pbar = tqdm(train_loader, desc="Epoch {epoch+1}/{num_epochs} [Train]")
        for batch in pbar:
            images = batch["image"].to(device)
            labels = batch["label"].long().to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_preds.extend(predicted.cpu().numpy())
            train_labels.extend(labels.cpu().numpy())

            pbar.set_postfix({"loss": loss.item()})

        scheduler.step()

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_preds = []
        val_labels = []

        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Epoch {epoch+1}/{num_epochs} [Val]"):
                images = batch["image"].to(device)
                labels = batch["label"].long().to(device)

                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                val_preds.extend(predicted.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())

        # Calculate metrics
        train_f1 = f1_score(train_labels, train_preds, average="weighted")
        val_f1 = f1_score(val_labels, val_preds, average="weighted")
        train_acc = accuracy_score(train_labels, train_preds)
        val_acc = accuracy_score(val_labels, val_preds)

        # Store metrics for plotting
        train_losses.append(train_loss / len(train_loader))
        val_losses.append(val_loss / len(val_loader))
        train_f1s.append(train_f1)
        val_f1s.append(val_f1)

        print("Epoch {epoch+1}/{num_epochs}:")
        print(
            "  Train Loss: {train_loss/len(train_loader):.4f}, Train F1:"
            " {train_f1:.4f}, Train Acc: {train_acc:.4f}"
        )
        print(
            f"  Val Loss: {val_loss / len(val_loader):.4f}, Val F1: {val_f1:.4f}, Val"
            f" Acc: {val_acc:.4f}"
        )

        # Save best model
        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_f1": best_f1,
                    "config": {"num_bands": 14, "num_classes": 2},
                },
                "best_landslide_model.pth",
            )
            print(f"  New best model saved with F1: {best_f1:.4f}")

        # Log to wandb
        if wandb.run:
            wandb.log({
                "epoch": epoch,
                "train_loss": train_loss / len(train_loader),
                "val_loss": val_loss / len(val_loader),
                "train_f1": train_f1,
                "val_f1": val_f1,
                "train_acc": train_acc,
                "val_acc": val_acc,
                "learning_rate": scheduler.get_last_lr()[0],
            })

    # Plot training curves
    plot_training_curves(train_losses, val_losses, train_f1s, val_f1s)

    return best_f1


def plot_training_curves(train_losses, val_losses, train_f1s, val_f1s):
    """Plot training and validation loss and F1 score curves.

    Args:
        train_losses: List of training loss values per epoch
        val_losses: List of validation loss values per epoch
        train_f1s: List of training F1 scores per epoch
        val_f1s: List of validation F1 scores per epoch
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Loss curves
    ax1.plot(train_losses, label="Train Loss", color="blue")
    ax1.plot(val_losses, label="Val Loss", color="red")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Training and Validation Loss")
    ax1.legend()
    ax1.grid(True)

    # F1 curves
    ax2.plot(train_f1s, label="Train F1", color="blue")
    ax2.plot(val_f1s, label="Val F1", color="red")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("F1 Score")
    ax2.set_title("Training and Validation F1 Score")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("training_curves.png", dpi=150, bbox_inches="tight")
    print("Training curves saved to: training_curves.png")


def evaluate_model(model, test_loader, device):
    """Evaluate the model on test set.

    Args:
        model: The trained PrithviLandslideClassifier model to evaluate
        test_loader: DataLoader for test data
        device: Device to evaluate on ('cuda' or 'cpu')

    Returns:
        dict: Dictionary containing test metrics (accuracy, F1 score, precision, recall)
    """
    model.eval()
    test_preds = []
    test_labels = []
    test_probs = []

    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating on test set"):
            images = batch["image"].to(device)
            labels = batch["label"].long().to(device)

            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs.data, 1)

            test_preds.extend(predicted.cpu().numpy())
            test_labels.extend(labels.cpu().numpy())
            test_probs.extend(probs.cpu().numpy())

    # Calculate metrics
    test_f1 = f1_score(test_labels, test_preds, average="weighted")
    test_acc = accuracy_score(test_labels, test_preds)
    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels, test_preds, average="weighted"
    )

    print("\nTest Set Results:")
    print("  Accuracy: {test_acc:.4f}")
    print("  F1 Score: {test_f1:.4f}")
    print("  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")

    return {
        "accuracy": test_acc,
        "f1": test_f1,
        "precision": precision,
        "recall": recall,
    }


def main():
    """Execute the complete fine-tuning process.

    This function orchestrates the complete fine-tuning process:
    1. Sets up wandb logging and device configuration
    2. Creates datasets and data loaders with transforms
    3. Initializes the Prithvi model and landslide classifier
    4. Trains the model and evaluates on validation data
    5. Evaluates best model on test set and saves results
    """
    print("Starting Prithvi-EO-1.0-100M fine-tuning on Landslide4Sense dataset")
    print("=" * 70)

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device: {device}")

    # Initialize wandb
    try:
        wandb.init(
            project="prithvi-landslide-finetuning",
            config={
                "model_type": "prithvi_eo_100m",
                "dataset": "landslide4sense",
                "num_bands": 14,
                "num_classes": 2,
                "img_size": 128,
                "batch_size": 16,
            },
            name="prithvi-eo-100m-landslide4sense",
        )
    except Exception as e:
        print(f"Wandb not available ({str(e)}), continuing without logging")
        wandb.run = None

    # Data transforms for multispectral data
    def get_multispectral_transforms():
        """Get transforms for multispectral data.

        Returns:
            callable: Transform function that applies the following augmentations:
                - Random horizontal flip (p=0.5)
                - Random vertical flip (p=0.5)
                - Random rotation (±10 degrees)
                - Random brightness/contrast adjustments
        """

        def transform(img):
            # Apply custom multispectral transforms
            img = MultispectralTransforms.random_horizontal_flip(img, p=0.5)
            img = MultispectralTransforms.random_vertical_flip(img, p=0.5)
            img = MultispectralTransforms.random_rotation(img, max_angle=10)
            img = MultispectralTransforms.random_brightness_contrast(img)
            return img

        return transform

    transform = get_multispectral_transforms()

    # Create datasets using proper metadata path
    print("\nCreating datasets...")
    metadata_path = "/teamspace/studios/this_studio/Landslide4sense.json"

    train_dataset = LandslideDataset(metadata_path, split="train", transform=transform)
    val_dataset = LandslideDataset(metadata_path, split="validation")
    test_dataset = LandslideDataset(metadata_path, split="test")

    # Create data loaders
    batch_size = 16
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=2
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=2
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=2
    )

    print("Train samples: {len(train_dataset)}")
    print("Validation samples: {len(val_dataset)}")
    print("Test samples: {len(test_dataset)}")

    # Initialize model
    print("\nInitializing model...")

    # Load pre-trained Prithvi model using the downloaded weights
    prithvi_config = {
        "img_size": 128,
        "patch_size": (1, 16, 16),  # (temporal, height, width)
        "num_frames": 1,  # Single frame for static images
        "in_chans": 6,  # Pre-trained model expects 6 bands
        "embed_dim": 768,
        "depth": 12,
        "num_heads": 12,
        "decoder_embed_dim": 512,
        "decoder_depth": 8,
        "decoder_num_heads": 16,
        "mlp_ratio": 4.0,
        "norm_layer": nn.LayerNorm,
        "norm_pix_loss": False,
        "coords_encoding": None,
        "coords_scale_learn": False,
        "encoder_only": True,  # Only use encoder for feature extraction
    }

    # Use the downloaded Prithvi model file
    prithvi_checkpoint_path = "Prithvi_EO_V1_100M.pt"
    prithvi_model = load_pretrained_prithvi(prithvi_checkpoint_path, prithvi_config)

    # Create the classifier
    model = PrithviLandslideClassifier(prithvi_model, num_classes=2)
    model = model.to(device)

    print("Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(
        "Trainable parameters: {sum(p.numel() for p in model.parameters() if"
        " p.requires_grad):,}"
    )

    # Train the model
    print("\nStarting training...")
    best_f1 = train_model(model, train_loader, val_loader, num_epochs=15, device=device)

    # Load best model for evaluation
    print("\nLoading best model (F1: {best_f1:.4f})...")
    checkpoint = torch.load("best_landslide_model.pth")
    model.load_state_dict(checkpoint["model_state_dict"])

    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_results = evaluate_model(model, test_loader, device)

    # Save final results
    results = {
        "best_f1": best_f1,
        "test_results": test_results,
        "model_config": checkpoint["config"],
    }

    with open("fine_tuning_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nFine-tuning completed!")
    print("Best validation F1: {best_f1:.4f}")
    print("Test F1: {test_results['f1']:.4f}")
    print("Results saved to: fine_tuning_results.json")


if __name__ == "__main__":
    main()
