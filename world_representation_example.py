import numpy as np
import math
import pathlib
import sys
import copy


#core imports
from core.base import Base
from core.obj_reader import my_obj_reader
from core.matrix import Matrix
#core_ext imports
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.render_target import RenderTarget
from core_ext.texture import Texture
from core_ext.instanced_object_factory import InstancedObjectFactory
from core_ext.scene_builder import SceneBuilder
from core_ext.material_cache import MaterialCache
from core_ext.bar_scene_loader import BarSceneLoader
#extra imports
from extras.axes import AxesHelper
from extras.grid import GridHelper
from extras.movement_rig import MovementRig
from extras.postprocessor import Postprocessor
from extras.directional_light import DirectionalLightHelper
from extras.point_light import PointLightHelper
#material imports
from material.surface import SurfaceMaterial
from material.texture import TextureMaterial
from material.lambert import LambertMaterial
from material.phong import PhongMaterial
from material.basic import BasicMaterial
from material.emissive import EmissiveMaterial
from material.transparent import TransparentMaterial
from material.sprite import SpriteMaterial
from material.line import LineMaterial
#effects imports
from effects.tintEffect import tintEffect
from effects.pixelateEffect import pixelateEffect
from effects.vignetteEffect import vignetteEffect
from effects.colorReduceEffect import colorReduceEffect
from effects.brightFilterEffect import brightFilterEffect
from effects.horizontalBlurEffect import horizontalBlurEffect
from effects.verticalBlurEffect import verticalBlurEffect
from effects.additiveBlendEffect import additiveBlendEffect
#light imports
from light.ambient import AmbientLight
from light.point import PointLight
from light.directional import DirectionalLight
from light.spotlight import SpotLight
from light.directional_spotlight import DirectionalSpotLight
#geometry imports
from geometry.rectangle import RectangleGeometry
from geometry.cylinder import CylinderGeometry
from geometry.cone import ConeGeometry
from geometry.bar import BarGeometry
from geometry.sphere import SphereGeometry
from geometry.custom import CustomGeometry
from geometry.jukebox import JukeboxGeometry
from geometry.geometry import Geometry

class Example(Base):
    """
    Render the axes and the rotated xy-grid.
    Add camera movement: WASDRF(move), QE(turn), TG(look).
    """

    def __init__(self, screen_size):
        super().__init__(screen_size)
        # Initialize material and texture caches
        self._material_cache = MaterialCache()
        # Initialize instance data storage
        self._instance_data = {}
        # Initialize light culling
        self._active_lights = set()
        self._light_culling_distance = 20.0  # Maximum distance for light influence
        
    def _create_instanced_mesh(self, geometry, material, positions, rotations=None):
        """Create a mesh with instanced geometry for multiple positions"""
        if rotations is None:
            rotations = [[0, 0, 0]] * len(positions)
            
        # Create a new geometry for the instanced mesh
        instanced_geometry = Geometry()
        
        # Get the original vertex data
        original_positions = geometry.attribute_dict["vertexPosition"].data
        original_normals = geometry.attribute_dict["vertexNormal"].data
        original_uvs = geometry.attribute_dict["vertexUV"].data
        
        # Create new vertex data for all instances
        new_positions = []
        new_normals = []
        new_uvs = []
        
        # For each instance, transform the vertices
        for pos, rot in zip(positions, rotations):
            # Create rotation matrix
            rot_x = rot[0]
            rot_y = rot[1]
            rot_z = rot[2]
            rot_matrix = Matrix.make_rotation_x(rot_x) @ Matrix.make_rotation_y(rot_y) @ Matrix.make_rotation_z(rot_z)
            
            # Transform each vertex
            for vertex_pos, vertex_normal, vertex_uv in zip(original_positions, original_normals, original_uvs):
                # Transform position
                transformed_pos = list(rot_matrix @ np.array(vertex_pos + [1]))[:3]
                transformed_pos = [p + offset for p, offset in zip(transformed_pos, pos)]
                new_positions.append(transformed_pos)
                
                # Transform normal
                transformed_normal = list(rot_matrix @ np.array(vertex_normal + [0]))[:3]
                new_normals.append(transformed_normal)
                
                # UV coordinates remain unchanged
                new_uvs.append(vertex_uv)
        
        # Add attributes to the new geometry
        instanced_geometry.add_attribute("vec3", "vertexPosition", new_positions)
        instanced_geometry.add_attribute("vec3", "vertexNormal", new_normals)
        instanced_geometry.add_attribute("vec2", "vertexUV", new_uvs)
        instanced_geometry.add_attribute("vec3", "faceNormal", new_normals)
        
        # Create and return the mesh
        mesh = Mesh(instanced_geometry, material)
        return mesh
        
    def _cull_lights(self, camera_position):
        """Update active lights based on camera position"""
        self._active_lights.clear()
        for light in self.dynamic_scene._children_list:
            if isinstance(light, (PointLight, SpotLight, DirectionalLight)):
                # For point and spot lights, check distance
                if isinstance(light, (PointLight, SpotLight)):
                    distance = np.linalg.norm(np.array(light.local_position) - np.array(camera_position))
                    if distance <= self._light_culling_distance:
                        self._active_lights.add(light)
                # Directional lights are always active
                elif isinstance(light, DirectionalLight):
                    self._active_lights.add(light)
                    
    def _update_light_uniforms(self):
        """Update material uniforms with only active lights"""
        active_light_count = len(self._active_lights)
        for material in self._material_cache._material_cache.values():
            if hasattr(material, 'number_of_light_sources'):
                material.uniform_dict["numberOfLights"].data = active_light_count
                
    def _setup_postprocessing(self):
        """Setup postprocessing effects"""
        # Create glow render target
        glow_target = RenderTarget(resolution=[400, 300])
        
        # Create glow pass
        self.glow_pass = Postprocessor(
            self.renderer, 
            self.scene_builder.glow_scene, 
            self.camera, 
            glow_target
        )
        
        # Add blur effects
        self.glow_pass.add_effect(horizontalBlurEffect(texture_size=[400,300], blur_radius=25))
        self.glow_pass.add_effect(verticalBlurEffect(texture_size=[400,300], blur_radius=25))
        
        # Create combo pass
        self.combo_pass = Postprocessor(
            self.renderer, 
            self.scene_builder.main_scene, 
            self.camera
        )
        
        # Add blend effect
        self.combo_pass.add_effect(
            additiveBlendEffect(
                blend_texture=glow_target.texture,
                original_strength=1,
                blend_strength=1.5
            )
        )

    def _setup_hud(self):
        """Setup HUD elements"""
        label_geo = RectangleGeometry(width=600, height=80, position=[0,600], alignment=[0,1])
        label_mat = TextureMaterial(Texture("images/Bar Simulator.png"))
        label = Mesh(label_geo, label_mat)
        self.scene_builder.add_to_hud(label)

    def initialize(self):
        print("Initializing program...")
        
        # Create renderer
        self.renderer = Renderer(clear_color=[0,0,0])
        
        # Create scene builder
        self.scene_builder = SceneBuilder(self.renderer, self._material_cache, self._material_cache)
        
        # Setup camera
        self.camera, self.rig = self.scene_builder.setup_camera()
        
        # Create bar scene loader
        bar_loader = BarSceneLoader(self.scene_builder, my_obj_reader)
        
        # Load scene components
        directional_light = bar_loader.load_lights()
        bar_loader.load_bar_structure()
        bar_loader.load_bottles()
        bar_loader.load_puff_chairs()
        bar_loader.load_lamps()
        
        # Setup postprocessing
        self._setup_postprocessing()
        
        # Setup HUD
        self._setup_hud()
        
        # Enable shadows
        self.renderer.enable_shadows(directional_light)

    def update(self):
        # Update camera position for light culling
        camera_position = self.camera.local_position
        self._cull_lights(camera_position)
        self._update_light_uniforms()
        
        # Update dynamic objects
        speed = 0.5
        x = math.cos(self.time * speed)/2
        y = math.sin(self.time * speed)/2
        dir = [x, y, 1] 
        
        # Only update active lights
        for light in self._active_lights:
            if isinstance(light, SpotLight):
                light.direction = dir
                
        self.vinyl.rotate_y(0.01337)
        self.mirrorball.rotate_y(0.02)

        # Update neon color using set_properties instead of creating new material
        rainbow_color = self.get_rainbow_color(self.time)
        self.neon.material.set_properties(property_dict={"baseColor": rainbow_color})
        
        #NeonSign Update
        blink_interval = 1.0  # seconds
        blinking = int(self.time // blink_interval) % 2 == 0
        if blinking:
            # Blue ON, Yellow OFF
            next_glow = self.blueSign
            next_color = self.dancefloor_color1
            self.dancefloor_color1.material.set_properties(property_dict={"baseColor": [0.6,0.3,0.6]})
            self.dancefloor_color2.material.set_properties(property_dict={"baseColor": [0.2,0.5,0.5]})
            self.blueSign.material.set_properties(property_dict={"baseColor": [0,1,1]})
            self.yellowSign.material.set_properties(property_dict={"baseColor": [0,0,0]})
        else:
            # Yellow ON, Blue OFF
            next_glow = self.yellowSign
            next_color = self.dancefloor_color2
            self.blueSign.material.set_properties(property_dict={"baseColor": [0,0,0]})
            self.yellowSign.material.set_properties(property_dict={"baseColor": [1,1,0]})
            self.dancefloor_color1.material.set_properties(property_dict={"baseColor": [0.5,0.2,0.5]})
            self.dancefloor_color2.material.set_properties(property_dict={"baseColor": [0.3,0.6,0.6]})

        # Reset glow scene and add the correct glowing mesh
        self.scene_builder.glow_scene.remove(self.current_glow)
        self.scene_builder.glow_scene.remove(self.current_color)
        self.scene_builder.glow_scene.add(next_glow)
        self.scene_builder.glow_scene.add(next_color)
        self.current_glow = next_glow
        self.current_color = next_color

        #Sonic Update
        tile_number = math.floor(self.time * self.tiles_per_second)
        self.sprite.material.uniform_dict["tileNumber"].data = tile_number

        self.rig.update(self.input, self.delta_time)

        self.glow_pass.render()
        self.combo_pass.render()
    

    def get_rainbow_color(self, time):
        # Convert time to a value between 0 and 1
        t = (time % 6) / 6.0  # Complete cycle every 6 seconds
        
        # Define rainbow colors in RGB
        colors = [
            [0.5, 0.0, 0.0],  # Red 
            [0.5, 0.25, 0.0], # Orange 
            [0.5, 0.5, 0.0],  # Yellow 
            [0.0, 0.5, 0.0],  # Green 
            [0.0, 0.0, 0.5],  # Blue 
            [0.25, 0.0, 0.5]  # Purple 
        ]
        
        # Calculate which colors to interpolate between
        color_index = int(t * len(colors))
        next_color_index = (color_index + 1) % len(colors)
        
        # Calculate interpolation factor
        factor = (t * len(colors)) - color_index
        
        # Interpolate between colors
        color1 = colors[color_index]
        color2 = colors[next_color_index]
        
        return [
            color1[0] + (color2[0] - color1[0]) * factor,
            color1[1] + (color2[1] - color1[1]) * factor,
            color1[2] + (color2[2] - color1[2]) * factor
        ]

# Instantiate this class and run the program
Example(screen_size=[1500, 800]).run()
