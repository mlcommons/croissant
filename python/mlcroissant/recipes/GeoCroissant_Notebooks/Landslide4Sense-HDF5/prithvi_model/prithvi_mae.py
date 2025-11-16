# Copyright (c) IBM Corp. 2024. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,

"""Prithvi MAE (Masked Autoencoder) Model Implementation.

This module implements the Prithvi Masked Autoencoder model architecture,
a deep learning model designed for self-supervised learning on remote sensing data.
The model uses a transformer-based architecture with masking strategies for
pretraining on satellite imagery.
"""
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------
# References:
# timm: https://github.com/rwightman/pytorch-image-models/tree/master/timm
# transformers: https://github.com/huggingface/transformers
# --------------------------------------------------------

import logging
from functools import partial
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
from einops import rearrange
from timm.layers import to_2tuple
from timm.models.vision_transformer import Block


def get_3d_sincos_pos_embed(embed_dim, grid_size, add_cls_token=False):
    """Create 3D sin/cos positional embeddings.

    Args:
        embed_dim (int): Embedding dimension for positional encodings.
        grid_size (tuple[int, int, int] | list[int]):
            The grid depth, height and width.
        add_cls_token (bool, *optional*, defaults to False):
            Whether or not to add a classification (CLS) token.

    Returns:
        (`torch.FloatTensor` of shape (grid_size[0]*grid_size[1]*grid_size[2], embed_dim) or
        (1+grid_size[0]*grid_size[1]*grid_size[2], embed_dim): the position embeddings (with or without cls token)
    """
    assert embed_dim % 16 == 0

    t_size, h_size, w_size = grid_size

    w_embed_dim = embed_dim // 16 * 6
    h_embed_dim = embed_dim // 16 * 6
    t_embed_dim = embed_dim // 16 * 4
    w_pos_embed = get_1d_sincos_pos_embed_from_grid(w_embed_dim, np.arange(w_size))
    h_pos_embed = get_1d_sincos_pos_embed_from_grid(h_embed_dim, np.arange(h_size))
    t_pos_embed = get_1d_sincos_pos_embed_from_grid(t_embed_dim, np.arange(t_size))

    w_pos_embed = np.tile(w_pos_embed, (t_size * h_size, 1))
    h_pos_embed = np.tile(np.repeat(h_pos_embed, w_size, axis=0), (t_size, 1))
    t_pos_embed = np.repeat(t_pos_embed, h_size * w_size, axis=0)

    pos_embed = np.concatenate((w_pos_embed, h_pos_embed, t_pos_embed), axis=1)

    if add_cls_token:
        pos_embed = np.concatenate([np.zeros([1, embed_dim]), pos_embed], axis=0)
    return pos_embed


def get_1d_sincos_pos_embed_from_grid(embed_dim, pos):
    """Generate 1D sinusoidal positional embeddings from a grid.

    Args:
        embed_dim: Output dimension for each position.
        pos: A list of positions to be encoded, size (M,).

    Returns:
        Tensor of shape (M, D) containing positional embeddings.
    """
    if embed_dim % 2 != 0:
        raise ValueError("embed_dim must be even")

    omega = np.arange(embed_dim // 2, dtype=float)
    omega /= embed_dim / 2.0
    omega = 1.0 / 10000**omega  # (D/2,)

    pos = pos.reshape(-1)  # (M,)
    out = np.einsum("m,d->md", pos, omega)  # (M, D/2), outer product

    emb_sin = np.sin(out)  # (M, D/2)
    emb_cos = np.cos(out)  # (M, D/2)

    emb = np.concatenate([emb_sin, emb_cos], axis=1)  # (M, D)
    return emb


def _get_1d_sincos_embed_from_grid_torch(embed_dim: int, pos: torch.Tensor):
    """Get 1D sincos positional embedding from grid using torch operations.

    embed_dim: output dimension for each position
    pos: a list of positions to be encoded: size (M,) - must be float dtype!
    out: (M, D)
    """
    assert embed_dim % 2 == 0
    assert pos.dtype in [torch.float32, torch.float16, torch.bfloat16]

    omega = torch.arange(embed_dim // 2, dtype=pos.dtype).to(pos.device)
    omega /= embed_dim / 2.0
    omega = 1.0 / 10000**omega  # (D/2,)

    pos = pos.reshape(-1)  # (M,)
    out = torch.einsum("m,d->md", pos, omega)  # (M, D/2), outer product

    emb_sin = torch.sin(out)  # (M, D/2)
    emb_cos = torch.cos(out)  # (M, D/2)

    emb = torch.cat([emb_sin, emb_cos], dim=1)  # (M, D)

    return emb


def _init_weights(module):
    """Initialize the weights."""
    if isinstance(module, nn.Linear):
        nn.init.xavier_uniform_(module.weight)
        if module.bias is not None:
            module.bias.data.zero_()
    elif isinstance(module, nn.LayerNorm):
        module.bias.data.zero_()
        module.weight.data.fill_(1.0)


class PatchEmbed(nn.Module):
    """3D version of timm.models.vision_transformer.PatchEmbed.

    This class handles the initial processing of the input by splitting it into patches
    and linearly embedding them.
    """

    def __init__(
        self,
        input_size: Tuple[int, int, int] = (1, 224, 224),
        patch_size: Tuple[int, int, int] = (1, 16, 16),
        in_chans: int = 3,
        embed_dim: int = 768,
        norm_layer: nn.Module | None = None,
        flatten: bool = True,
        bias: bool = True,
    ):
        """Initialize the PatchEmbed module.

        Args:
            input_size: Size of input tensor (time, height, width).
            patch_size: Size of patches to split input into.
            in_chans: Number of input channels.
            embed_dim: Dimension of patch embeddings.
            norm_layer: Optional normalization layer.
            flatten: Whether to flatten patch embeddings.
            bias: Whether to use bias in linear projection.
        """
        super().__init__()
        self.input_size = input_size
        self.patch_size = patch_size
        self.grid_size = [s // p for s, p in zip(self.input_size, self.patch_size)]
        self.num_patches = self.grid_size[0] * self.grid_size[1] * self.grid_size[2]
        self.flatten = flatten

        self.proj = nn.Conv3d(
            in_chans, embed_dim, kernel_size=patch_size, stride=patch_size, bias=bias
        )
        self.norm = norm_layer(embed_dim) if norm_layer else nn.Identity()

    def forward(self, x):
        """Forward pass of the patch embedding layer.

        Args:
            x: Input tensor of shape (B, C, T, H, W).

        Returns:
            Embedded patches tensor.
        """
        B, C, T, H, W = x.shape

        if (
            T / self.patch_size[0] % 1
            or H / self.patch_size[1] % 1
            or W / self.patch_size[2] % 1
        ):
            logging.warning(
                "Input {x.shape[-3:]} is not divisible by patch size {self.patch_size}."
                "The border will be ignored, add backbone_padding for pixel-wise tasks."
            )

        x = self.proj(x)
        if self.flatten:
            x = x.flatten(2).transpose(1, 2)  # B,C,T,H,W -> B,C,L -> B,L,C
        x = self.norm(x)
        return x


class TemporalEncoder(nn.Module):
    """Temporal encoding module for handling time-based features.

    This module encodes temporal information using sinusoidal embeddings
    with optional trainable scaling.
    """

    def __init__(self, embed_dim: int, trainable_scale: bool = False):
        """Initialize the temporal encoder.

        Args:
            embed_dim: Dimension of the embeddings.
            trainable_scale: Whether to use trainable scaling factors.
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.year_embed_dim = embed_dim // 2
        self.julian_day_embed_dim = embed_dim - self.year_embed_dim

        # If trainable, initialize scale with small number
        if trainable_scale:
            self.scale = nn.Parameter(torch.full((1,), 0.1))
        else:
            self.register_buffer("scale", torch.ones(1))

    def forward(
        self, temporal_coords: torch.Tensor, tokens_per_frame: int | None = None
    ):
        """Forward pass for temporal embeddings.

        Args:
            temporal_coords: Year and day-of-year info with shape (B, T, 2).
            tokens_per_frame: Number of tokens for each frame in the sample. If provided,
                embeddings will be repeated over T dimension, and final shape is
                (B, T*tokens_per_frame, embed_dim).

        Returns:
            Tensor containing temporal embeddings.
        """
        shape = temporal_coords.shape[:2] + (-1,)  # B, T, -1

        year = _get_1d_sincos_embed_from_grid_torch(
            self.year_embed_dim, temporal_coords[:, :, 0].flatten()
        ).reshape(shape)
        julian_day = _get_1d_sincos_embed_from_grid_torch(
            self.julian_day_embed_dim, temporal_coords[:, :, 1].flatten()
        ).reshape(shape)

        embedding = self.scale * torch.cat([year, julian_day], dim=-1)

        if tokens_per_frame is not None:
            embedding = torch.repeat_interleave(embedding, tokens_per_frame, dim=1)

        return embedding  # B, T*tokens_per_frame, embed_dim


class LocationEncoder(nn.Module):
    """Encoder for spatial location information.

    This module handles the encoding of positional information for spatial coordinates,
    converting them into learned embeddings that can be used by the transformer model.
    """

    def __init__(self, embed_dim: int, trainable_scale: bool = False):
        """Initialize the LocationEncoder.

        Args:
            embed_dim (int): Dimension of the location embedding.
            trainable_scale (bool): If True, scale is trainable.
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.lat_embed_dim = embed_dim // 2
        self.lon_embed_dim = embed_dim - self.lat_embed_dim

        # If trainable, initialize scale with small number
        if trainable_scale:
            self.scale = nn.Parameter(torch.full((1,), 0.1))
        else:
            self.register_buffer("scale", torch.ones(1))

    def forward(self, location_coords: torch.Tensor):
        """Compute location embeddings from latitude and longitude.

        Args:
            location_coords (torch.Tensor): lat and lon info with shape (B, 2).

        Returns:
            torch.Tensor: Location embedding of shape (B, 1, embed_dim).
        """
        shape = location_coords.shape[:1] + (1, -1)  # B, 1, -1

        lat = _get_1d_sincos_embed_from_grid_torch(
            self.lat_embed_dim, location_coords[:, 0].flatten()
        ).reshape(shape)
        lon = _get_1d_sincos_embed_from_grid_torch(
            self.lon_embed_dim, location_coords[:, 1].flatten()
        ).reshape(shape)

        embedding = self.scale * torch.cat([lat, lon], dim=-1)

        return embedding  # B, 1, embed_dim


class PrithviViT(nn.Module):
    """Prithvi ViT Encoder."""

    def __init__(
        self,
        img_size: int | Tuple[int, int] = 224,
        patch_size: int | Tuple[int, int, int] = (1, 16, 16),
        num_frames: int = 1,
        in_chans: int = 3,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        norm_layer: nn.Module = partial(torch.nn.LayerNorm, eps=1e-6),
        coords_encoding: List[str] | None = None,
        coords_scale_learn: bool = False,
        encoder_only: bool = True,  # needed for timm
        **kwargs,
    ):
        """Initialize Prithvi Vision Transformer encoder.

        Args:
            img_size: Input image size (H=W) or tuple (H,W)
            patch_size: Size of patches to embed (T,H,W)
            num_frames: Number of input frames (time dimension)
            in_chans: Number of input channels
            embed_dim: Dimension of transformer embedding
            depth: Number of transformer layers
            num_heads: Number of attention heads
            mlp_ratio: MLP hidden dimension expansion ratio
            norm_layer: Normalization layer to use
            coords_encoding: Types of coordinate encodings to use
            coords_scale_learn: Whether coordinate scales should be learnable
            encoder_only: Whether to use encoder only mode
        """
        super().__init__()

        self.feature_info = []
        self.encoder_only = encoder_only
        self.in_chans = in_chans
        self.num_frames = num_frames
        self.embed_dim = embed_dim
        self.img_size = to_2tuple(img_size)
        if isinstance(patch_size, int):
            patch_size = (1, patch_size, patch_size)

        # 3D patch embedding
        self.patch_embed = PatchEmbed(
            input_size=(num_frames,) + self.img_size,
            patch_size=patch_size,
            in_chans=in_chans,
            embed_dim=embed_dim,
        )

        # Optional temporal and location embedding
        coords_encoding = coords_encoding or []
        self.temporal_encoding = "time" in coords_encoding
        self.location_encoding = "location" in coords_encoding
        if self.temporal_encoding:
            assert patch_size[0] == 1, (
                "With temporal encoding, patch_size[0] must be 1, received"
                " {patch_size[0]}"
            )
            self.temporal_embed_enc = TemporalEncoder(embed_dim, coords_scale_learn)
        if self.location_encoding:
            self.location_embed_enc = LocationEncoder(embed_dim, coords_scale_learn)

        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.register_buffer(
            "pos_embed", torch.zeros(1, self.patch_embed.num_patches + 1, embed_dim)
        )

        # Transformer layers
        self.blocks = []
        for i in range(depth):
            self.blocks.append(
                Block(
                    embed_dim,
                    num_heads,
                    mlp_ratio,
                    qkv_bias=True,
                    norm_layer=norm_layer,
                )
            )
            self.feature_info.append({
                "num_chs": embed_dim * self.patch_embed.patch_size[0],
                "reduction": 1,
                "module": "blocks.{i}",
            })
        self.blocks = nn.ModuleList(self.blocks)

        self.norm = norm_layer(embed_dim)

        self.initialize_weights()

    def initialize_weights(self):
        """Initialize encoder weights with proper initialization schemes.

        Performs:
        1. Initializing position embeddings with sin-cos embedding
        2. Initializing patch embedding projection with Xavier uniform
        3. Initializing CLS token with small normal values
        4. Applying default weight initialization to remaining parameters
        """
        # initialize (and freeze) position embeddings by sin-cos embedding
        pos_embed = get_3d_sincos_pos_embed(
            self.pos_embed.shape[-1], self.patch_embed.grid_size, add_cls_token=True
        )
        self.pos_embed.data.copy_(torch.from_numpy(pos_embed).float().unsqueeze(0))

        # initialize patch_embeddings like nn.Linear (instead of nn.Conv2d)
        w = self.patch_embed.proj.weight.data
        torch.nn.init.xavier_uniform_(w.view([w.shape[0], -1]))

        # timm's trunc_normal_(std=.02) is effectively normal_(std=0.02) as cutoff is too big (2.)
        torch.nn.init.normal_(self.cls_token, std=0.02)
        self.apply(_init_weights)

    def random_masking(self, sequence, mask_ratio, noise=None):
        """Perform per-sample random masking by per-sample shuffling.

        Per-sample shuffling is done by argsort random noise to ensure uniform masking.

        Args:
            sequence: Input sequence tensor of shape [batch_size, sequence_length, dim]
            mask_ratio: Ratio of tokens to mask in range [0, 1)
            noise: Optional tensor of shape [batch_size, sequence_length] for shuffling,
                  if not provided use normal noise. Used for reproducible testing.

        Returns:
            tuple: Contains:
                - sequence_unmasked: Unmasked sequence [batch_size, int(L*(1-mask_ratio)), dim]
                - mask: Binary mask tensor [batch_size, sequence_length] (1=masked)
                - ids_restore: Index tensor to restore original sequence order
        """
        batch_size, seq_length, dim = sequence.shape
        len_keep = int(seq_length * (1 - mask_ratio))

        if noise is None:
            noise = torch.rand(
                batch_size, seq_length, device=sequence.device
            )  # noise in [0, 1]

        # sort noise for each sample
        ids_shuffle = torch.argsort(noise, dim=1).to(
            sequence.device
        )  # ascend: small is keep, large is remove
        ids_restore = torch.argsort(ids_shuffle, dim=1).to(sequence.device)

        # keep the first subset
        ids_keep = ids_shuffle[:, :len_keep]
        sequence_unmasked = torch.gather(
            sequence, dim=1, index=ids_keep.unsqueeze(-1).repeat(1, 1, dim)
        )

        # generate the binary mask: 0 is keep, 1 is remove
        mask = torch.ones([batch_size, seq_length], device=sequence.device)
        mask[:, :len_keep] = 0
        # unshuffle to get the binary mask
        mask = torch.gather(mask, dim=1, index=ids_restore)

        return sequence_unmasked, mask, ids_restore

    def _get_pos_embed(self, x):
        t, h, w = x.shape[-3:]

        pos_embed = (
            torch.from_numpy(
                get_3d_sincos_pos_embed(
                    self.embed_dim,
                    (
                        t // self.patch_embed.patch_size[0],
                        h // self.patch_embed.patch_size[1],
                        w // self.patch_embed.patch_size[2],
                    ),
                    add_cls_token=True,
                )
            )
            .float()
            .unsqueeze(0)
            .to(x)
        )

        return pos_embed

    def forward(
        self,
        x: torch.Tensor,
        temporal_coords: None | torch.Tensor = None,
        location_coords: None | torch.Tensor = None,
        mask_ratio=0.75,
    ):
        """Forward pass through Prithvi Vision Transformer encoder.

        Args:
            x: Input image tensor of shape [batch_size, channels, time, height, width]
            temporal_coords: Optional temporal coordinates for each frame
            location_coords: Optional location coordinates
            mask_ratio: Ratio of patches to mask during training

        Returns:
            tuple: Contains:
                - sequence: Encoded sequence with CLS token
                - mask: Binary mask indicating masked positions
                - ids_restore: Indices to restore original sequence order
        """
        if x.shape[-3:] != self.patch_embed.input_size:
            # changed input size
            pos_embed = self._get_pos_embed(x)
        else:
            pos_embed = self.pos_embed

        # embed patches
        x = self.patch_embed(x)

        # add pos embed w/o cls token
        x = x + pos_embed[:, 1:, :]

        if self.temporal_encoding:
            num_tokens_per_frame = x.shape[1] // self.num_frames
            temporal_encoding = self.temporal_embed_enc(
                temporal_coords, num_tokens_per_frame
            )
            x = x + temporal_encoding
        if self.location_encoding:
            location_encoding = self.location_embed_enc(location_coords)
            x = x + location_encoding

        # masking: length -> length * mask_ratio
        x, mask, ids_restore = self.random_masking(x, mask_ratio)

        # append cls token
        cls_token = self.cls_token + pos_embed[:, :1, :]
        cls_tokens = cls_token.expand(x.shape[0], -1, -1)
        x = torch.cat((cls_tokens, x), dim=1)

        # apply Transformer blocks
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)

        return x, mask, ids_restore

    def forward_features(
        self,
        x: torch.Tensor,
        temporal_coords: None | torch.Tensor = None,
        location_coords: None | torch.Tensor = None,
    ) -> list[torch.Tensor]:
        """Extract features from each transformer layer without masking.

        Args:
            x: Input image tensor of shape [batch_size, channels, time, height, width]
            temporal_coords: Optional temporal coordinates for each frame
            location_coords: Optional location coordinates

        Returns:
            list[torch.Tensor]: List of features from each transformer layer,
                              including CLS token embeddings
        """
        if len(x.shape) == 4 and self.patch_embed.input_size[0] == 1:
            # add time dim
            x = x.unsqueeze(2)

        if x.shape[-3:] != self.patch_embed.input_size:
            pos_embed = self._get_pos_embed(x)
        else:
            pos_embed = self.pos_embed

        # embed patches
        x = self.patch_embed(x)

        # add pos embed w/o cls token
        x = x + pos_embed[:, 1:, :]

        if self.temporal_encoding:
            num_tokens_per_frame = x.shape[1] // self.patch_embed.num_frames
            temporal_encoding = self.temporal_embed_enc(
                temporal_coords, num_tokens_per_frame
            )
            x = x + temporal_encoding
        if self.location_encoding:
            location_encoding = self.location_embed_enc(location_coords)
            x = x + location_encoding

        # append cls token
        cls_token = self.cls_token + pos_embed[:, :1, :]
        cls_tokens = cls_token.expand(x.shape[0], -1, -1)
        x = torch.cat((cls_tokens, x), dim=1)

        # apply Transformer blocks
        out = []
        for block in self.blocks:
            x = block(x)
            out.append(x.clone())

        x = self.norm(x)
        out[-1] = x
        return out

    def prepare_features_for_image_model(
        self, features: list[torch.Tensor]
    ) -> list[torch.Tensor]:
        """Prepare features for image model.

        Args:
            features (list[torch.Tensor]): List of feature tensors.

        Returns:
            list[torch.Tensor]: List of processed feature tensors.
        """
        out = []
        effective_time_dim = (
            self.patch_embed.input_size[0] // self.patch_embed.patch_size[0]
        )
        for x in features:
            x_no_token = x[:, 1:, :]
            number_of_tokens = x_no_token.shape[1]
            tokens_per_timestep = number_of_tokens // effective_time_dim
            h = int(np.sqrt(tokens_per_timestep))
            encoded = rearrange(
                x_no_token,
                "batch (t h w) e -> batch (t e) h w",
                e=self.embed_dim,
                t=effective_time_dim,
                h=h,
            )
            out.append(encoded)
        return out


class MAEDecoder(nn.Module):
    """Transformer Decoder used in the Prithvi MAE."""

    def __init__(
        self,
        patch_size: int | Tuple[int, int, int] = (1, 16, 16),
        grid_size: List[int] | Tuple[int, int, int] = (3, 14, 14),
        in_chans: int = 3,
        encoder_embed_dim: int = 1024,
        decoder_embed_dim: int = 512,
        depth: int = 8,
        num_heads: int = 16,
        mlp_ratio: float = 4.0,
        norm_layer: nn.Module = nn.LayerNorm,
        coords_encoding: List[str] | None = None,
        coords_scale_learn: bool = False,
    ):
        """Initialize MAE decoder.

        Args:
            patch_size: Size of patches to decode (T,H,W)
            grid_size: Size of output grid (T,H,W)
            in_chans: Number of input channels
            encoder_embed_dim: Dimension of encoder embedding
            decoder_embed_dim: Dimension of decoder embedding
            depth: Number of transformer decoder layers
            num_heads: Number of attention heads
            mlp_ratio: MLP hidden dimension expansion ratio
            norm_layer: Normalization layer to use
            coords_encoding: Types of coordinate encodings to use
            coords_scale_learn: Whether coordinate scales should be learnable
        """
        super().__init__()

        self.decoder_embed = nn.Linear(encoder_embed_dim, decoder_embed_dim, bias=True)
        self.decoder_embed_dim = decoder_embed_dim
        self.grid_size = grid_size
        if isinstance(patch_size, int):
            patch_size = (1, patch_size, patch_size)
        self.patch_size = patch_size
        self.num_frames = self.grid_size[0] * patch_size[0]
        num_patches = self.grid_size[0] * self.grid_size[1] * self.grid_size[2]

        # Optional temporal and location embedding
        coords_encoding = coords_encoding or []
        self.temporal_encoding = "time" in coords_encoding
        self.location_encoding = "location" in coords_encoding
        if self.temporal_encoding:
            self.temporal_embed_dec = TemporalEncoder(
                decoder_embed_dim, coords_scale_learn
            )
        if self.location_encoding:
            self.location_embed_dec = LocationEncoder(
                decoder_embed_dim, coords_scale_learn
            )

        self.mask_token = nn.Parameter(torch.zeros(1, 1, decoder_embed_dim))

        self.register_buffer(
            "decoder_pos_embed", torch.zeros(1, num_patches + 1, decoder_embed_dim)
        )

        self.decoder_blocks = nn.ModuleList([
            Block(
                decoder_embed_dim,
                num_heads,
                mlp_ratio,
                qkv_bias=True,
                norm_layer=norm_layer,
            )
            for _ in range(depth)
        ])

        self.decoder_norm = norm_layer(decoder_embed_dim)
        self.decoder_pred = nn.Linear(
            decoder_embed_dim,
            patch_size[0] * patch_size[1] * patch_size[2] * in_chans,
            bias=True,
        )

        self.initialize_weights()

    def initialize_weights(self):
        """Initialize decoder weights with proper initialization schemes.

        Includes:
        1. Initializing position embeddings with sin-cos embedding
        2. Initializing mask token with small normal values
        3. Applying weight initialization to all other parameters
        """
        # initialize (and freeze) position embeddings by sin-cos embedding
        decoder_pos_embed = get_3d_sincos_pos_embed(
            self.decoder_pos_embed.shape[-1], self.grid_size, add_cls_token=True
        )
        self.decoder_pos_embed.data.copy_(
            torch.from_numpy(decoder_pos_embed).float().unsqueeze(0)
        )

        # timm's trunc_normal_(std=.02) is effectively normal_(std=0.02) as cutoff is too big (2.)
        torch.nn.init.normal_(self.mask_token, std=0.02)
        self.apply(_init_weights)

    def forward(
        self,
        hidden_states: torch.Tensor,
        ids_restore: torch.Tensor,
        temporal_coords: None | torch.Tensor = None,
        location_coords: None | torch.Tensor = None,
        input_size: list[int] = None,
    ):
        """Forward pass for the decoder. Add detailed docstring as needed."""
        # embed tokens
        x = self.decoder_embed(hidden_states)

        t, h, w = input_size[-3:]
        decoder_pos_embed = torch.from_numpy(
            get_3d_sincos_pos_embed(
                self.decoder_embed_dim,
                (
                    t // self.patch_size[0],
                    h // self.patch_size[1],
                    w // self.patch_size[2],
                ),
                add_cls_token=True,
            )
        ).to(x)

        # append mask tokens to sequence
        mask_tokens = self.mask_token.repeat(
            x.shape[0], ids_restore.shape[1] + 1 - x.shape[1], 1
        )
        x_ = torch.cat([x[:, 1:, :], mask_tokens], dim=1)  # no cls token
        # unshuffle
        x_ = torch.gather(
            x_,
            dim=1,
            index=ids_restore.unsqueeze(-1).repeat(1, 1, x.shape[2]).to(x_.device),
        )
        x = torch.cat([x[:, :1, :], x_], dim=1)  # append cls token
        # add pos embed
        x = x + decoder_pos_embed

        # remove cls token
        x_ = x[:, 1:, :]

        if self.temporal_encoding:
            num_tokens_per_frame = x_.shape[1] // self.num_frames
            temporal_encoding = self.temporal_embed_dec(
                temporal_coords, num_tokens_per_frame
            )
            # Add temporal encoding w/o cls token
            x_ = x_ + temporal_encoding
        if self.location_encoding:
            location_encoding = self.location_embed_dec(location_coords)
            # Add location encoding w/o cls token
            x_ = x_ + location_encoding

        # append cls token
        x = torch.cat([x[:, :1, :], x_], dim=1)

        # apply Transformer layers (blocks)
        for block in self.decoder_blocks:
            x = block(x)
        x = self.decoder_norm(x)

        # predictor projection
        pred = self.decoder_pred(x)

        # remove cls token
        pred = pred[:, 1:, :]

        return pred


class PrithviMAE(nn.Module):
    """Prithvi Masked Autoencoder."""

    def __init__(
        self,
        img_size: int | Tuple[int, int] = 224,
        patch_size: int | Tuple[int, int, int] = (1, 16, 16),
        num_frames: int = 3,
        in_chans: int = 3,
        embed_dim: int = 1024,
        depth: int = 24,
        num_heads: int = 16,
        decoder_embed_dim: int = 512,
        decoder_depth: int = 8,
        decoder_num_heads: int = 16,
        mlp_ratio: float = 4.0,
        norm_layer: nn.Module = partial(torch.nn.LayerNorm, eps=1e-6),
        norm_pix_loss: bool = False,
        coords_encoding: List[str] | None = None,
        coords_scale_learn: bool = False,
        encoder_only: bool = False,
        **kwargs,
    ):
        """Initialize Prithvi MAE model.

        Args:
            img_size: Input image size (H=W) or tuple (H,W)
            patch_size: Size of patches to embed (T,H,W)
            num_frames: Number of input frames (time dimension)
            in_chans: Number of input channels
            embed_dim: Dimension of encoder embedding
            depth: Number of transformer encoder layers
            num_heads: Number of attention heads in encoder
            decoder_embed_dim: Dimension of decoder embedding
            decoder_depth: Number of transformer decoder layers
            decoder_num_heads: Number of attention heads in decoder
            mlp_ratio: MLP hidden dimension expansion ratio
            norm_layer: Normalization layer to use
            norm_pix_loss: Whether to normalize targets in pixel loss
            coords_encoding: Types of coordinate encodings to use
            coords_scale_learn: Whether coordinate scales should be learnable
            encoder_only: Whether to use encoder only (no decoder)
        """
        super().__init__()

        self.encoder = PrithviViT(
            img_size=img_size,
            num_frames=num_frames,
            patch_size=patch_size,
            in_chans=in_chans,
            embed_dim=embed_dim,
            depth=depth,
            num_heads=num_heads,
            mlp_ratio=mlp_ratio,
            norm_layer=norm_layer,
            coords_encoding=coords_encoding,
            coords_scale_learn=coords_scale_learn,
        )

        self.encoder_only = encoder_only

        if not encoder_only:
            self.decoder = MAEDecoder(
                patch_size=patch_size,
                grid_size=self.encoder.patch_embed.grid_size,
                in_chans=in_chans,
                encoder_embed_dim=embed_dim,
                decoder_embed_dim=decoder_embed_dim,
                depth=decoder_depth,
                num_heads=decoder_num_heads,
                mlp_ratio=mlp_ratio,
                norm_layer=norm_layer,
                coords_encoding=coords_encoding,
                coords_scale_learn=coords_scale_learn,
            )
        else:
            self.decoder = nn.Identity()

        self.norm_pix_loss = norm_pix_loss

    def patchify(self, pixel_values):
        """Convert pixel values to patchified format.

        Args:
            pixel_values (torch.FloatTensor of shape `(batch_size, num_channels, time, height, width)`):
                Pixel values.

        Returns:
            torch.FloatTensor of shape `(batch_size, num_patches, patch_size[0]*patch_size[1]*patch_size[2] * num_channels)`:
                Patchified pixel values.
        """
        patch_size_t, patch_size_h, patch_size_w = self.encoder.patch_embed.patch_size
        num_channels = self.encoder.in_chans

        # patchify
        patchified_pixel_values = rearrange(
            pixel_values,
            "b c (t s) (h p) (w q) -> b (t h w) (s p q c)",
            c=num_channels,
            s=patch_size_t,
            p=patch_size_h,
            q=patch_size_w,
        )

        return patchified_pixel_values

    def unpatchify(
        self, patchified_pixel_values, image_size: Tuple[int, int] | None = None
    ):
        """Convert patchified tensor back to regular image tensor.

        Args:
            patchified_pixel_values: Tensor of shape [batch_size, num_patches,
                patch_size[0]*patch_size[1]*patch_size[2]*num_channels] containing
                patchified pixel values
            image_size: Optional tuple of (height, width) for output image size.
                If not provided, uses model's default image size.

        Returns:
            torch.Tensor: Reconstructed image tensor of shape
                [batch_size, num_channels, time*patch_size[0], height, width]
        """
        patch_size_t, patch_size_h, patch_size_w = self.encoder.patch_embed.patch_size
        image_size = (
            to_2tuple(image_size) if image_size is not None else self.encoder.img_size
        )
        original_height, original_width = image_size
        num_patches_h = original_height // patch_size_h
        num_patches_w = original_width // patch_size_w
        num_channels = self.encoder.in_chans

        pixel_values = rearrange(
            patchified_pixel_values,
            "b (t h w) (s p q c) -> b c (t s) (h p) (w q)",
            c=num_channels,
            h=num_patches_h,
            w=num_patches_w,
            s=patch_size_t,
            p=patch_size_h,
            q=patch_size_w,
        )
        return pixel_values

    def forward_loss(self, pixel_values, pred, mask):
        """Compute the loss for forward pass.

        Args:
            pixel_values (`torch.FloatTensor` of shape `(batch_size, num_channels, time, height, width)`):
                Pixel values.
            pred (`torch.FloatTensor` of shape `(batch_size, num_patches, patch_size[0]*patch_size[1]*patch_size[2] * num_channels)`:
                Predicted pixel values.
            mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`):
                Tensor indicating which patches are masked (1) and which are not (0).

        Returns:
            `torch.FloatTensor`: Pixel reconstruction loss.
        """
        target = self.patchify(pixel_values)
        if self.norm_pix_loss:
            mean = target.mean(dim=-1, keepdim=True)
            var = target.var(dim=-1, keepdim=True)
            target = (target - mean) / (var + 1.0e-6) ** 0.5

        loss = (pred - target) ** 2
        loss = loss.mean(dim=-1)  # [N, L], mean loss per patch
        loss = (loss * mask).sum() / mask.sum()  # mean loss on removed patches
        return loss

    def forward(
        self,
        pixel_values: torch.Tensor,
        temporal_coords: None | torch.Tensor = None,
        location_coords: None | torch.Tensor = None,
        mask_ratio: float = 0.75,
    ):
        """Forward pass through the full MAE model.

        Args:
            pixel_values: Input image tensor of shape [B,C,T,H,W]
            temporal_coords: Optional temporal coordinates for each frame
            location_coords: Optional location coordinates
            mask_ratio: Ratio of patches to mask during training

        Returns:
            tuple: Contains:
                - loss: MAE reconstruction loss
                - pred: Model predictions
                - mask: Generated mask indicating which patches were masked
        """
        if len(pixel_values.shape) == 4 and self.encoder.patch_embed.input_size[0] == 1:
            # add time dim
            pixel_values = pixel_values.unsqueeze(2)

        latent, mask, ids_restore = self.encoder(
            pixel_values, temporal_coords, location_coords, mask_ratio
        )
        pred = self.decoder(
            latent,
            ids_restore,
            temporal_coords,
            location_coords,
            input_size=pixel_values.shape,
        )
        loss = self.forward_loss(pixel_values, pred, mask)
        return loss, pred, mask

    def forward_features(
        self,
        x: torch.Tensor,
        temporal_coords: None | torch.Tensor = None,
        location_coords: None | torch.Tensor = None,
    ) -> List[torch.Tensor]:
        """Extract features from input using Prithvi encoder.

        Args:
            x: Input image tensor of shape [B,C,T,H,W]
            temporal_coords: Optional temporal coordinates for each frame
            location_coords: Optional location coordinates

        Returns:
            List[torch.Tensor]: List of encoded features from each transformer layer
        """
        return self.encoder.forward_features(x, temporal_coords, location_coords)
