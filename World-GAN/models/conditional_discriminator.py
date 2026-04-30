"""
Conditional Discriminator with Biome Classification

This discriminator learns to distinguish real from fake samples AND
classify the biome type, providing additional training signal.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .conv_block import ConvBlock
from .biome_embedding import BiomeEmbedding, BiomeConditioner


class Level_ConditionalWDiscriminator(nn.Module):
    """
    Conditional Wasserstein Discriminator with biome classification head.
    
    Outputs:
    1. Real/Fake score (standard Wasserstein)
    2. Biome class prediction (auxiliary classifier)
    """
    def __init__(self, opt, embedding_dim=64, num_biomes=11):
        super().__init__()
        self.is_cuda = torch.cuda.is_available()
        self.embedding_dim = embedding_dim
        self.num_biomes = num_biomes
        
        N = int(opt.nfc)
        dim = len(opt.level_shape)
        kernel = tuple(opt.ker_size for _ in range(dim))
        
        # Main discriminator path
        self.head = ConvBlock(opt.nc_current, N, kernel, 0, 1, dim)
        self.body = nn.Sequential()

        for i in range(opt.num_layer - 2):
            block = ConvBlock(N, N, kernel, 0, 1, dim)
            self.body.add_module("block%d" % (i + 1), block)

        block = ConvBlock(N, N, kernel, 0, 1, dim)
        self.body.add_module("block%d" % (opt.num_layer - 2), block)

        # Real/Fake output (standard Wasserstein)
        if dim == 2:
            self.tail = nn.Conv2d(N, 1, kernel_size=kernel, stride=1, padding=0)
        elif dim == 3:
            self.tail = nn.Conv3d(N, 1, kernel_size=kernel, stride=1, padding=0)
        else:
            raise NotImplementedError("Can only make 2D or 3D Conv Layers.")
        
        # Auxiliary: Biome classifier head
        # Takes features before tail and predicts biome class
        self.biome_classifier = self._build_biome_classifier(N, num_biomes, dim)

    def _build_biome_classifier(self, feature_channels, num_biomes, dim):
        """Build auxiliary biome classification head."""
        if dim == 2:
            return nn.Sequential(
                nn.Conv2d(feature_channels, feature_channels // 2, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(feature_channels // 2, num_biomes)
            )
        elif dim == 3:
            return nn.Sequential(
                nn.Conv3d(feature_channels, feature_channels // 2, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool3d(1),
                nn.Flatten(),
                nn.Linear(feature_channels // 2, num_biomes)
            )
        else:
            raise NotImplementedError("Can only make 2D or 3D Conv Layers.")

    def forward(self, x, return_biome_logits=False):
        """
        Forward pass of discriminator.
        
        Args:
            x: Input sample
            return_biome_logits: If True, also return biome class logits
            
        Returns:
            If return_biome_logits=False:
                - real_fake_score: Wasserstein discriminator score
            If return_biome_logits=True:
                - (real_fake_score, biome_logits): Tuple of both outputs
        """
        # Main path
        x = self.head(x)
        x = self.body(x)
        
        # Real/Fake score
        real_fake_score = self.tail(x)
        
        if return_biome_logits:
            # Biome classification (from features before tail)
            biome_logits = self.biome_classifier(x)
            return real_fake_score, biome_logits
        else:
            return real_fake_score
