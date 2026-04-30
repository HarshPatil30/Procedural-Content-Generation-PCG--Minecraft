"""
Conditional Generator with Biome Conditioning

This extends the base generator to accept and incorporate biome conditioning signals.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .conv_block import ConvBlock
from .biome_embedding import BiomeEmbedding, BiomeConditioner


class Level_ConditionalGeneratorConcatSkip2CleanAdd(nn.Module):
    """
    Conditional Patch-based Generator with biome control.
    
    Takes biome embeddings and incorporates them into generation at multiple scales.
    """
    def __init__(self, opt, use_softmax=True, embedding_dim=64, conditioning_method='affine'):
        super().__init__()
        self.is_cuda = torch.cuda.is_available()
        self.use_softmax = use_softmax
        self.embedding_dim = embedding_dim
        self.conditioning_method = conditioning_method
        
        N = int(opt.nfc)
        dim = len(opt.level_shape)
        kernel = tuple(opt.ker_size for _ in range(dim))
        
        # Biome embedding module
        self.biome_embedding = BiomeEmbedding(num_biomes=11, embedding_dim=embedding_dim)
        
        # First layer (head)
        self.head = ConvBlock(opt.nc_current, N, kernel, 0, 1, dim)
        
        # Add biome conditioning after head
        self.head_conditioner = BiomeConditioner(embedding_dim, N, method=conditioning_method)
        
        # Update head output channels if using concat
        if conditioning_method == 'concat':
            head_out_channels = N + N
        else:
            head_out_channels = N
        
        # Body layers
        self.body = nn.Sequential()
        for i in range(opt.num_layer - 2):
            block = ConvBlock(head_out_channels if i == 0 else N, N, kernel, 0, 1, dim)
            self.body.add_module("block%d" % (i + 1), block)
            
            # Add biome conditioners at intermediate layers
            conditioner = BiomeConditioner(embedding_dim, N, method=conditioning_method)
            self.body.add_module("cond%d" % (i + 1), conditioner)
        
        # Final body block
        block = ConvBlock(N, N, kernel, 0, 1, dim)
        self.body.add_module("block%d" % (opt.num_layer - 2), block)
        final_conditioner = BiomeConditioner(embedding_dim, N, method=conditioning_method)
        self.body.add_module("cond%d" % (opt.num_layer - 1), final_conditioner)
        
        # Tail layer
        if dim == 2:
            if use_softmax:
                self.tail = nn.Sequential(nn.Conv2d(N, opt.nc_current, kernel_size=kernel,
                                                    stride=1, padding=0))
            else:
                self.tail = nn.Sequential(
                    nn.Conv2d(N, opt.nc_current, kernel_size=kernel, stride=1, padding=0),
                )
        elif dim == 3:
            if use_softmax:
                self.tail = nn.Sequential(nn.Conv3d(N, opt.nc_current, kernel_size=kernel,
                                                    stride=1, padding=0))
            else:
                self.tail = nn.Sequential(
                    nn.Conv3d(N, opt.nc_current, kernel_size=kernel, stride=1, padding=0),
                )
        else:
            raise NotImplementedError("Can only make 2D or 3D Conv Layers.")

    def forward(self, x, y, biome_labels=None, temperature=1):
        """
        Forward pass with optional biome conditioning.
        
        Args:
            x: Noise input
            y: Skip connection from previous scale
            biome_labels: LongTensor of biome class indices (B,). If None, no conditioning.
            temperature: Temperature for softmax
            
        Returns:
            output: Generated sample
        """
        # Get biome embeddings if labels provided
        if biome_labels is not None:
            biome_emb = self.biome_embedding(biome_labels)  # (B, embedding_dim)
        else:
            # Create default embedding (zeros) - no conditioning
            batch_size = x.shape[0]
            biome_emb = torch.zeros(batch_size, self.embedding_dim, device=x.device)
        
        # Head
        x = self.head(x)
        
        # Apply biome conditioning to head
        if biome_labels is not None:
            x = self.head_conditioner(x, biome_emb)
        
        # Body with interspersed conditioning
        for name, layer in self.body.named_children():
            if 'cond' in name and biome_labels is not None:
                # Apply biome conditioner
                x = layer(x, biome_emb)
            elif 'cond' not in name:
                # Apply normal conv block
                x = layer(x)
        
        # Tail
        x = self.tail(x)
        
        if self.use_softmax:
            x = F.softmax(x * temperature, dim=1)
        
        # Skip connection (same as original)
        ind = int((y.shape[2] - x.shape[2]) / 2)
        if len(y.shape) == 4:
            y = y[:, :, ind:(y.shape[2] - ind), ind:(y.shape[3] - ind)]
        elif len(y.shape) == 5:
            y = y[:, :, ind:(y.shape[2] - ind), ind:(y.shape[3] - ind), ind:(y.shape[4] - ind)]
        else:
            raise NotImplementedError("only supports 4D or 5D tensors")

        return x + y
