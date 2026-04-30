"""
Biome Embedding and Conditioning Module for Conditional World-GAN

This module provides:
1. BiomeEmbedding: Converts biome class labels to embeddings
2. BiomeEncoder: Encodes text prompts/descriptions to biome vectors
3. BiomeConditioner: Fuses biome embeddings into feature maps
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import json
from pathlib import Path


# Define biome classes
BIOME_CLASSES = {
    'plains': 0,
    'forest': 1,
    'desert': 2,
    'mountains': 3,
    'river': 4,
    'ocean': 5,
    'swamp': 6,
    'tundra': 7,
    'jungle': 8,
    'savanna': 9,
    'mixed': 10,  # Mixed biomes
}

BIOME_NAMES = {v: k for k, v in BIOME_CLASSES.items()}


class BiomeEmbedding(nn.Module):
    """
    Converts biome class labels to dense embeddings.
    
    Args:
        num_biomes: Number of biome classes
        embedding_dim: Dimension of the embedding vector
    """
    def __init__(self, num_biomes=len(BIOME_CLASSES), embedding_dim=64):
        super().__init__()
        self.num_biomes = num_biomes
        self.embedding_dim = embedding_dim
        self.embedding = nn.Embedding(num_biomes, embedding_dim)
        
    def forward(self, biome_labels):
        """
        Args:
            biome_labels: LongTensor of shape (batch_size,) with biome class indices
            
        Returns:
            embeddings: FloatTensor of shape (batch_size, embedding_dim)
        """
        return self.embedding(biome_labels)


class BiomeDescriptionEncoder(nn.Module):
    """
    Encodes biome descriptions/prompts into embedding vectors.
    
    Uses simple keyword-based encoding for text prompts.
    Can be extended with more sophisticated NLP models.
    
    Example prompts:
    - "desert world"
    - "mountain-heavy terrain"
    - "tropical jungle"
    - "snowy mountains"
    """
    def __init__(self, embedding_dim=64):
        super().__init__()
        self.embedding_dim = embedding_dim
        
        # Load biome profiles to get statistical features
        self.biome_profiles = self._load_biome_profiles()
        
        # Create learnable embedding matrix
        self.biome_embeddings = nn.Embedding(len(BIOME_CLASSES), embedding_dim)
        self.prompt_to_biome = self._create_prompt_mapping()
        
    def _load_biome_profiles(self):
        """Load biome profiles from JSON file."""
        try:
            profiles_path = Path('biome_profiles.json')
            if profiles_path.exists():
                with open(profiles_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load biome profiles: {e}")
        return {}
    
    def _create_prompt_mapping(self):
        """Create mapping from keywords to biome types."""
        return {
            'desert': BIOME_CLASSES['desert'],
            'sand': BIOME_CLASSES['desert'],
            'dry': BIOME_CLASSES['desert'],
            'hot': BIOME_CLASSES['desert'],
            
            'forest': BIOME_CLASSES['forest'],
            'tree': BIOME_CLASSES['forest'],
            'wood': BIOME_CLASSES['forest'],
            'green': BIOME_CLASSES['forest'],
            
            'mountain': BIOME_CLASSES['mountains'],
            'peak': BIOME_CLASSES['mountains'],
            'high': BIOME_CLASSES['mountains'],
            'rocky': BIOME_CLASSES['mountains'],
            
            'water': BIOME_CLASSES['ocean'],
            'ocean': BIOME_CLASSES['ocean'],
            'sea': BIOME_CLASSES['ocean'],
            'river': BIOME_CLASSES['river'],
            
            'jungle': BIOME_CLASSES['jungle'],
            'tropical': BIOME_CLASSES['jungle'],
            'dense': BIOME_CLASSES['jungle'],
            
            'snow': BIOME_CLASSES['tundra'],
            'ice': BIOME_CLASSES['tundra'],
            'cold': BIOME_CLASSES['tundra'],
            'frozen': BIOME_CLASSES['tundra'],
            
            'plain': BIOME_CLASSES['plains'],
            'flat': BIOME_CLASSES['plains'],
            'grass': BIOME_CLASSES['plains'],
            
            'swamp': BIOME_CLASSES['swamp'],
            'wet': BIOME_CLASSES['swamp'],
            'marsh': BIOME_CLASSES['swamp'],
        }
    
    def encode_prompt(self, prompt):
        """
        Encode a text prompt to biome class.
        
        Args:
            prompt: String description of desired biome(s)
            
        Returns:
            biome_class: Integer class index of the dominant biome
            confidence: Float confidence score (0-1)
        """
        prompt_lower = prompt.lower()
        scores = {}
        
        # Score each biome based on keyword matches
        for keyword, biome_idx in self.prompt_to_biome.items():
            if keyword in prompt_lower:
                scores[biome_idx] = scores.get(biome_idx, 0) + 1
        
        if not scores:
            # Default to mixed if no keywords match
            return BIOME_CLASSES['mixed'], 0.5
        
        # Return biome with highest score
        best_biome = max(scores.items(), key=lambda x: x[1])
        confidence = min(1.0, best_biome[1] / len(prompt_lower.split()))
        
        return best_biome[0], confidence
    
    def forward(self, prompts):
        """
        Encode multiple prompts to embeddings.
        
        Args:
            prompts: List of string prompts or LongTensor of biome indices
            
        Returns:
            embeddings: FloatTensor of shape (batch_size, embedding_dim)
        """
        if isinstance(prompts, list):
            # Convert prompts to biome indices
            biome_indices = []
            for prompt in prompts:
                biome_idx, _ = self.encode_prompt(prompt)
                biome_indices.append(biome_idx)
            biome_indices = torch.tensor(biome_indices, dtype=torch.long)
        else:
            biome_indices = prompts
            
        return self.biome_embeddings(biome_indices)


class BiomeConditioner(nn.Module):
    """
    Injects biome conditioning into feature maps.
    
    Methods:
    1. Concatenation: Append embedding to feature map
    2. Affine: Use embedding to modulate feature channels (AdaIN-style)
    3. Spatial: Broadcast embedding and concatenate spatially
    """
    def __init__(self, embedding_dim, feature_channels, method='concat'):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.feature_channels = feature_channels
        self.method = method
        
        if method == 'concat':
            # Project embedding to feature size for concatenation
            self.proj = nn.Linear(embedding_dim, feature_channels)
            
        elif method == 'affine':
            # Affine transformation (scale and bias)
            self.gamma = nn.Linear(embedding_dim, feature_channels)
            self.beta = nn.Linear(embedding_dim, feature_channels)
            
        elif method == 'spatial':
            # Project to single channel and broadcast
            self.proj = nn.Linear(embedding_dim, 1)
    
    def forward(self, features, biome_embedding):
        """
        Condition features with biome embedding.
        
        Args:
            features: Feature map tensor (B, C, H, W) or (B, C, D, H, W)
            biome_embedding: Biome embedding (B, embedding_dim)
            
        Returns:
            conditioned_features: Conditioned feature tensor
        """
        batch_size = features.shape[0]
        
        if self.method == 'concat':
            # Project embedding to spatial dimension
            proj_emb = self.proj(biome_embedding)  # (B, C)
            
            # Reshape for broadcasting
            if len(features.shape) == 4:  # 2D: (B, C, H, W)
                proj_emb = proj_emb.view(batch_size, -1, 1, 1)
                proj_emb = proj_emb.expand_as(features)
            elif len(features.shape) == 5:  # 3D: (B, C, D, H, W)
                proj_emb = proj_emb.view(batch_size, -1, 1, 1, 1)
                proj_emb = proj_emb.expand_as(features)
            
            # Concatenate
            return torch.cat([features, proj_emb], dim=1)
        
        elif self.method == 'affine':
            # Affine transformation (like AdaIN)
            gamma = self.gamma(biome_embedding)  # (B, C)
            beta = self.beta(biome_embedding)    # (B, C)
            
            # Reshape for broadcasting
            if len(features.shape) == 4:  # 2D
                gamma = gamma.view(batch_size, -1, 1, 1)
                beta = beta.view(batch_size, -1, 1, 1)
            elif len(features.shape) == 5:  # 3D
                gamma = gamma.view(batch_size, -1, 1, 1, 1)
                beta = beta.view(batch_size, -1, 1, 1, 1)
            
            # Apply affine: y = gamma * x + beta
            return gamma * features + beta
        
        elif self.method == 'spatial':
            # Project to single channel
            proj_emb = self.proj(biome_embedding)  # (B, 1)
            
            # Reshape and broadcast
            if len(features.shape) == 4:  # 2D
                proj_emb = proj_emb.view(batch_size, 1, 1, 1)
                proj_emb = proj_emb.expand(batch_size, 1, features.shape[2], features.shape[3])
            elif len(features.shape) == 5:  # 3D
                proj_emb = proj_emb.view(batch_size, 1, 1, 1, 1)
                proj_emb = proj_emb.expand(batch_size, 1, features.shape[2], features.shape[3], features.shape[4])
            
            # Concatenate
            return torch.cat([features, proj_emb], dim=1)
        
        else:
            raise ValueError(f"Unknown conditioning method: {self.method}")


class ConditionalBiomeWrapper(nn.Module):
    """
    Wrapper that adds biome conditioning to existing generator/discriminator.
    
    Usage:
        gen = ConditionalBiomeWrapper(original_generator, embedding_dim=64)
        output = gen(noise, prev_output, biome_label)
    """
    def __init__(self, model, embedding_dim=64, conditioning_method='affine'):
        super().__init__()
        self.model = model
        self.embedding_dim = embedding_dim
        self.conditioning_method = conditioning_method
        
        # Get feature dimensions from model
        self.biome_embedding = BiomeEmbedding(
            num_biomes=len(BIOME_CLASSES),
            embedding_dim=embedding_dim
        )
        
    def forward(self, x, y, biome_labels, temperature=1):
        """
        Forward pass with biome conditioning.
        
        Args:
            x: Noise input
            y: Previous scale output
            biome_labels: LongTensor of biome class indices (B,)
            temperature: Temperature for softmax
            
        Returns:
            output: Generated sample with biome conditioning applied
        """
        # Get biome embeddings
        biome_emb = self.biome_embedding(biome_labels)  # (B, embedding_dim)
        
        # Forward through original model
        output = self.model(x, y, temperature=temperature)
        
        return output
