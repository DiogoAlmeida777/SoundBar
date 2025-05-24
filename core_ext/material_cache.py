from material.lambert import LambertMaterial
from material.phong import PhongMaterial
from material.surface import SurfaceMaterial
from material.transparent import TransparentMaterial
from material.sprite import SpriteMaterial
from core_ext.texture import Texture

class MaterialCache:
    """Helper class for caching materials and textures"""
    def __init__(self):
        self._material_cache = {}
        self._texture_cache = {}
        
    def get_material(self, material_type, **kwargs):
        """Get a cached material or create and cache a new one"""
        # Create a unique key for the material based on its type and properties
        key = f"{material_type}_{str(sorted(kwargs.items()))}"
        
        if key not in self._material_cache:
            if material_type == "LambertMaterial":
                self._material_cache[key] = LambertMaterial(**kwargs)
            elif material_type == "PhongMaterial":
                self._material_cache[key] = PhongMaterial(**kwargs)
            elif material_type == "SurfaceMaterial":
                self._material_cache[key] = SurfaceMaterial(**kwargs)
            elif material_type == "TransparentMaterial":
                self._material_cache[key] = TransparentMaterial(**kwargs)
            elif material_type == "SpriteMaterial":
                self._material_cache[key] = SpriteMaterial(**kwargs)
                
        return self._material_cache[key]
        
    def get_texture(self, texture_path):
        """Get a cached texture or create and cache a new one"""
        if texture_path not in self._texture_cache:
            self._texture_cache[texture_path] = Texture(texture_path)
        return self._texture_cache[texture_path]
        
    def clear(self):
        """Clear all cached materials and textures"""
        self._material_cache.clear()
        self._texture_cache.clear() 