from core_ext.scene import Scene
from core_ext.mesh import Mesh
from core_ext.camera import Camera
from core_ext.renderer import Renderer
from core_ext.render_target import RenderTarget
from extras.postprocessor import Postprocessor
from extras.movement_rig import MovementRig

class SceneBuilder:
    """Helper class for building and managing scenes"""
    def __init__(self, renderer, material_cache, texture_cache):
        self.renderer = renderer
        self.material_cache = material_cache
        self.texture_cache = texture_cache
        
        # Create main scenes
        self.static_scene = Scene()
        self.dynamic_scene = Scene()
        self.glow_scene = Scene()
        self.hud_scene = Scene()
        
        # Create main scene that contains others
        self.main_scene = Scene()
        self.main_scene.add(self.static_scene)
        self.main_scene.add(self.dynamic_scene)
        
    def setup_camera(self, aspect_ratio=1920/1080):
        """Setup camera and movement rig"""
        self.camera = Camera(aspect_ratio=aspect_ratio)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([11.5, 1.5, 14])
        self.dynamic_scene.add(self.rig)
        return self.camera, self.rig
        
    def setup_hud_camera(self):
        """Setup HUD camera with orthographic projection"""
        self.hud_camera = Camera()
        self.hud_camera.set_orthographic(0, 800, 0, 600, 1, -1)
        return self.hud_camera
        
    def setup_postprocessing(self, glow_resolution=[400, 300]):
        """Setup glow and postprocessing effects"""
        # Create glow render target
        glow_target = RenderTarget(resolution=glow_resolution)
        
        # Create glow pass
        self.glow_pass = Postprocessor(
            self.renderer, 
            self.glow_scene, 
            self.camera, 
            glow_target
        )
        
        # Create combo pass
        self.combo_pass = Postprocessor(
            self.renderer, 
            self.main_scene, 
            self.camera
        )
        
        return self.glow_pass, self.combo_pass, glow_target
        
    def add_to_static(self, mesh):
        """Add mesh to static scene"""
        self.static_scene.add(mesh)
        
    def add_to_dynamic(self, mesh):
        """Add mesh to dynamic scene"""
        self.dynamic_scene.add(mesh)
        
    def add_to_glow(self, mesh):
        """Add mesh to glow scene"""
        self.glow_scene.add(mesh)
        
    def add_to_hud(self, mesh):
        """Add mesh to HUD scene"""
        self.hud_scene.add(mesh)
        
    def get_cached_material(self, material_type, **kwargs):
        """Get a cached material or create and cache a new one"""
        return self.material_cache.get_material(material_type, **kwargs)
        
    def get_cached_texture(self, texture_path):
        """Get a cached texture or create and cache a new one"""
        return self.texture_cache.get_texture(texture_path) 