import os

import numpy as np
import math
import pathlib
import sys
import copy
import random

import pygame
import pygame.mixer
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
from core_ext.object3d import Object3D
#extra imports
from extras.axes import AxesHelper
from extras.grid import GridHelper
from extras.movement_rig import MovementRig
from extras.postprocessor import Postprocessor
from extras.directional_light import DirectionalLightHelper
from extras.point_light import PointLightHelper
from extras.collision_manager import CollisionManager
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
from extras.text_texture import TextTexture
#effects imports
from effects.tintEffect import tintEffect
from effects.pixelateEffect import pixelateEffect
from effects.vignetteEffect import vignetteEffect
from effects.colorReduceEffect import colorReduceEffect
from effects.brightFilterEffect import brightFilterEffect
from effects.horizontalBlurEffect import horizontalBlurEffect
from effects.verticalBlurEffect import verticalBlurEffect
from effects.additiveBlendEffect import additiveBlendEffect
from effects.drunkEffect import drunkEffect
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
from geometry.box import BoxGeometry
from geometry.snooker_table import SnookerTableGeometry

MAX_BEER_AMOUNT_PER_BOTTLE = 20

class Example(Base):
    """
    Render the axes and the rotated xy-grid.
    Add camera movement: WASDRF(move), QE(turn), TG(look).
    """

    def __init__(self, screen_size):
        super().__init__(screen_size)
        pygame.mixer.init()
        #SONS
        self.gulp_sound = pygame.mixer.Sound("sounds/gulp.mp3")
        self.gulping_channel = pygame.mixer.Channel(1)

        self.steps_sound = pygame.mixer.Sound("sounds/step.mp3")
        self.stepping_channel = pygame.mixer.Channel(0)

        self.burp_sound = pygame.mixer.Sound("sounds/burp.mp3")
        self.burp_sound.set_volume(0.2) # Diminuir o volume do som do arroto
        self.burp_channel = pygame.mixer.Channel(3)

        self.bottle_break_sound = pygame.mixer.Sound("sounds/bottle-break.mp3")
        self.bottle_break_channel = pygame.mixer.Channel(4)

        self.DRUNKNESS = 0
        self.BEER_LEFT = MAX_BEER_AMOUNT_PER_BOTTLE
        self.hasBeer = False
        
        # Jukebox menu state
        self.jukebox_menu_active = False
        self.jukebox_buttons = []
        
        # Music and light control
        self.song_playing = False
        self.last_song_state = False
        self.song_color_timer = 0.0
        self.dynamic_lights = []  # Lista para armazenar luzes dinâmicas

        self.beer_tilted = False  # Track if beer is currently tilting
        self.beer_can_tilt = True  # Track if beer can be tilted again
        self.tilt_towards_player = False
        self.current_angle = 0  # Track current rotation angle
        self.move_angle = 10
        self.beer_animation_progress = 0.0  # Track animation progress (0 to 1)
        self.beer_animation_speed = 3.0  # Speed of the animation


        self.show_menu = True
        self.screen_size = screen_size
        self._material_cache = {}
        self._texture_cache = {}
        self._instance_data = {}
        self._active_lights = set()
        self._light_culling_distance = 20.0  # Maximum distance for light influence
        # Add these lines after other initializations
        self.brightness = 2
        # === Drunkness Effects ===
        #self.tint = tintEffect(tint_color=[2,2,2])
        self.pixelate = pixelateEffect(pixel_size=0.01)
        self.color_reduce = colorReduceEffect(levels=256)
        self.blur_h = horizontalBlurEffect(texture_size=[400, 300], blur_radius=0)
        self.blur_v = verticalBlurEffect(texture_size=[400, 300], blur_radius=0)
        self.drunk_effect = drunkEffect(drunk_level=0.0, time=0.0)

        # Add a flag to track if space was just pressed
        self.space_was_pressed = False

        # Add flags for bottle throwing
        self.bottle_thrown = False
        self.bottle_velocity = np.array([0.0, 0.0, 0.0])
        self.bottle_gravity = -9.8  # Gravity constant
        self.bottle_can_throw = False  # Flag to indicate if bottle can be thrown

        # Add sound playing flags
        self.gulping_sound_playing = False

        # Add harmonica player animation parameters
        self.harmonica_animation_speed = 0.5  # Speed of the animation cycle
        self.harmonica_tilt_angle = 15  # Increased tilt angle in degrees
        
        # Animation states (in radians)
        self.harmonica_states = {
            'normal': 0,
            'right': math.radians(self.harmonica_tilt_angle),
            'left': math.radians(-self.harmonica_tilt_angle)
        }
        
        # Animation timing
        self.harmonica_animation_time = 0
        self.harmonica_animation_duration = 2.0  # Time for one complete cycle (normal -> right -> normal -> left -> normal)

        
        # Jukebox interaction variables
        self.jukebox_position = [0, 0, 14.5]  # Posição da jukebox
        self.jukebox_interaction_distance = 3.0  # Distância de interação
        self.show_interaction_prompt = False

        self.bar_position = [-10,0,12]  # Posição da jukebox
        self.bar_interaction_distance = 3.0  # Distância de interação
        self.show_interaction_prompt2 = False
        
        # Initialize pygame font
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)  # None uses default font, 36 is size
        
        # Glass fragments system
        self.glass_fragments = []  # List to store active glass fragments
        self.fragment_lifetime = 10.0  # How long fragments stay on the ground (seconds)
        self.fragment_gravity = -9.8  # Gravity for fragments
        self.fragment_bounce_damping = 0.3  # How much velocity is lost on bounce

        # Musical notes system
        self.musical_notes = []  # List to store active musical notes
        self.note_lifetime = 2.0  # How long notes stay visible (seconds)
        self.note_rise_speed = 2.0  # How fast notes rise up
        self.note_spawn_timer = 0.0  # Timer for spawning new notes
        self.note_spawn_interval = 0.3  # Time between note spawns (increased from 0.5 to 0.8)
        self.note_pool = []  # Pool of reusable note meshes
        self.max_notes = 20  # Maximum number of notes at once
        self.note_colors = [
            [1.0, 0.0, 0.0],  # Red
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
            [1.0, 1.0, 0.0],  # Yellow
            [1.0, 0.0, 1.0],  # Magenta
            [0.0, 1.0, 1.0]   # Cyan
        ]
        # Bottle collision system will be initialized in initialize() method

        # Instrument animation parameters
        self.instrument_animation_active = False     # becomes True when music plays
        self.instrument_animation_speed = 0.3       # base speed (rad/s)
        self.instrument_float_height = 0.2          # vertical "float" (m)
        self.instrument_rotation_speed = 0.3        # smooth rotation (rad/s)
        self.instrument_path_radius = 12.0          # circular path radius (m)
        self.instrument_vertical_offset = 1.5       # average height from floor (m)
        self.instrument_acceleration_time = 20.0    # seconds until full speed
        self.instrument_animation_start_time = 0.0  # marked when music starts

        # bar boundaries - instruments never leave these "virtual walls"
        self.bar_bounds = {
            'x_min': -14.0, 'x_max': 14.0,
            'z_min': -14.0, 'z_max': 14.0,
            'y_min': 0.5, 'y_max': 3.0
        }

        # list to store each instrument and animation metadata
        self.instruments = []

        # Add chair animation parameters
        self.chair_animation_active = False
        self.chair_animation_speed = 0.2  # Slower movement
        self.chair_float_height = 1  # Reduced float height
        self.chair_rotation_speed = 0.2  # Slower rotation
        self.chair_path_radius = 4.0  # Larger radius to keep chairs apart
        self.chair_vertical_offset = 2  # Increased base height offset
        self.chair_acceleration_time = 3.0  # Slower transition
        self.chair_animation_start_time = 0
        self.flying_chairs = []  # List to store flying chair objects

    def _get_cached_texture(self, texture_path):
        """Get a cached texture or create and cache a new one"""
        if texture_path not in self._texture_cache:
            self._texture_cache[texture_path] = Texture(texture_path)
        return self._texture_cache[texture_path]
        
    def _get_cached_material(self, material_type, **kwargs):
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
        
    def _get_cached_texture(self, texture_path):
        """Get a cached texture or create and cache a new one"""
        if texture_path not in self._texture_cache:
            self._texture_cache[texture_path] = Texture(texture_path)
        return self._texture_cache[texture_path]
        
    def _get_cached_material(self, material_type, **kwargs):
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
        for material in self._material_cache.values():
            if hasattr(material, 'number_of_light_sources'):
                material.uniform_dict["numberOfLights"].data = active_light_count
                
    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer(clear_color=[0,0,0])
        
        # Create separate scenes for static and dynamic objects
        self.static_scene = Scene()
        self.dynamic_scene = Scene()
        self.glow_scene = Scene()
        
        # Add scenes to main scene
        self.scene = Scene()
        self.scene.add(self.static_scene)
        self.scene.add(self.dynamic_scene)
        
        # Setup frames
        self._setup_pictures()
        
        # Initialize bottle collision system now that static_scene exists
        self.bottle_collision_manager = CollisionManager(self.static_scene)
        self._setup_bottle_collision_objects()
        
        # Camera setup
        self.camera = Camera(aspect_ratio=1920/1080)
        self.rig = MovementRig(debug_scene=self.static_scene)  # Pass static scene for debug boxes
        self.rig.add(self.camera)
        self.rig.set_position([11.5, 1.5, 14])
        self.dynamic_scene.add(self.rig)  # Camera is dynamic
        self.isWalking = False
        self.last_camera_position = np.array(self.camera.global_position)
        self.movement_threshold = 0.01
        # Lights (dynamic since they move/change)
        ambient_light = AmbientLight(color=[0.1, 0.1, 0.1])
        self.dynamic_scene.add(ambient_light)


        
        self.flashlight = SpotLight(
            color=(1.0, 1.0, 1),      
            position=(0, 3.5, -11),       
            direction=(0, 0.4, 1),      
            cutoff_angle=20,       
            inner_cutoff_angle=5,
            attenuation=(1.0, 0.01, 0.001)
        )       
        self.dynamic_scene.add(self.flashlight)
        
        #DirectionalLight
        
        directional_light = DirectionalLight(
            color=[0.1,0.1,0.1],
            direction=[0,-1,-1],
        )
        directional_light.set_position([0,3.5,-11])
        self.dynamic_scene.add(directional_light)
        #direct_helper = DirectionalLightHelper(directional_light)
        #directional_light.add(direct_helper)
        self.renderer.enable_shadows(directional_light)

        #PointLights
        # Table positions (incluindo duas novas mesas à direita do palco, descoordenadas em Z e afastadas da parede)
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5], [11, 0, -10], [11, 0, 0]]
        for pos in table_positions:
            pointlight = PointLight(color=[0.8,1,0.8],position=(pos + np.array([0,1.45,0])))
            self.dynamic_scene.add(pointlight)
            self.dynamic_lights.append(pointlight)
        
        #ceiling lights
        for i in range(5):
            ceilinglight = PointLight(color=[0.2,0.2,0.5],position=[-9 - i,3.5,12])
            self.dynamic_scene.add(ceilinglight)
            self.dynamic_lights.append(ceilinglight)
            
        # Snooker table ceiling lights
        for i in range(3):
            snooker_ceilinglight = PointLight(color=[0.2,0.2,0.5],position=[-12,3.5,-10.8 + i])
            self.dynamic_scene.add(snooker_ceilinglight)
            self.dynamic_lights.append(snooker_ceilinglight)
            
        self.light_number = 15

        #BarInterior
        wall_geometry, floor_geometry, roof_geometry, door_geometry = BarGeometry(1, 1, 1, my_obj_reader('objects/interior.obj'))
        wall_material = self._get_cached_material(
            "PhongMaterial",
            texture=self._get_cached_texture("images/wall.png"),
            bump_texture=self._get_cached_texture("images/wall_normal.png"),
            property_dict={"bumpStrength": 1},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        floor_material = self._get_cached_material(
            "PhongMaterial",
            texture=self._get_cached_texture("images/floor.png"),
            bump_texture=self._get_cached_texture("images/floor_normal.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        roof_material = PhongMaterial(
            texture=Texture("images/roof.png"),
            bump_texture=Texture("images/roof_normal.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        door_material = PhongMaterial(
            texture=Texture("images/door_texture.jpg"),
            bump_texture=Texture("images/door_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        wall_mesh = Mesh(wall_geometry, wall_material)
        floor_mesh = Mesh(floor_geometry, floor_material)
        roof_mesh = Mesh(roof_geometry, roof_material)
        door_mesh = Mesh(door_geometry, door_material)
        self.static_scene.add(wall_mesh)
        self.static_scene.add(floor_mesh)
        self.static_scene.add(roof_mesh)
        self.static_scene.add(door_mesh)

        ####Meshes#####

        #Table
        table_geometry = CustomGeometry(1,1,1,my_obj_reader("objects/squaretable.obj")).get("table")
        table_material = LambertMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        table = Mesh(geometry=table_geometry,material=table_material)
        table.set_position([14,0,-14])
        self.static_scene.add(table)
        
        #Snooker Table
        baize_geo, balls_geo, cues_geo, leg_holders_geo, legs_geo, pin_geo, pot_corner_geo, pot_middle_geo, cue_box_geo, cushion_geo = SnookerTableGeometry(1, 1, 1, my_obj_reader("objects/snooker_table_5.obj"))
        
        # Create materials for different components
        baize_material = LambertMaterial(
            property_dict={"baseColor": [0.1, 0.6, 0.1]},  # Green felt color
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        legs_material = LambertMaterial(
            property_dict={"baseColor": [0.4, 0.2, 0.1]},  # Brown wood color
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        balls_material = PhongMaterial(
            property_dict={"baseColor": [0.8, 0.0, 0.0]},  # Red color for snooker balls
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        metal_material = PhongMaterial(
            property_dict={"baseColor": [0.3, 0.3, 0.3]},  # Metal components
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        pocket_material = LambertMaterial(
            property_dict={"baseColor": [0.1, 0.1, 0.1]},  # Black pockets
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        cue_material = LambertMaterial(
            property_dict={"baseColor": [0.6, 0.4, 0.2]},  # Wood cues
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        # Create meshes for each component that exists
        if baize_geo:
            baize_mesh = Mesh(geometry=baize_geo, material=baize_material)
            baize_mesh.set_position([-12, 0, -8])
            self.static_scene.add(baize_mesh)
            
        if legs_geo:
            legs_mesh = Mesh(geometry=legs_geo, material=legs_material)
            legs_mesh.set_position([-12, 0, -8])
            self.static_scene.add(legs_mesh)
            
        if balls_geo:
            balls_mesh = Mesh(geometry=balls_geo, material=balls_material)
            balls_mesh.set_position([-12, 0, -8])
            self.static_scene.add(balls_mesh)
            
        if cushion_geo:
            cushion_mesh = Mesh(geometry=cushion_geo, material=legs_material)
            cushion_mesh.set_position([-12, 0, -8])
            self.static_scene.add(cushion_mesh)
            
        if leg_holders_geo:
            leg_holders_mesh = Mesh(geometry=leg_holders_geo, material=metal_material)
            leg_holders_mesh.set_position([-12, 0, -8])
            self.static_scene.add(leg_holders_mesh)
            
        if pin_geo:
            pin_mesh = Mesh(geometry=pin_geo, material=metal_material)
            pin_mesh.set_position([-12, 0, -8])
            self.static_scene.add(pin_mesh)
            
        if pot_corner_geo:
            pot_corner_mesh = Mesh(geometry=pot_corner_geo, material=pocket_material)
            pot_corner_mesh.set_position([-12, 0, -8])
            self.static_scene.add(pot_corner_mesh)
            
        if pot_middle_geo:
            pot_middle_mesh = Mesh(geometry=pot_middle_geo, material=pocket_material)
            pot_middle_mesh.set_position([-12, 0, -8])
            self.static_scene.add(pot_middle_mesh)
            
        if cues_geo:
            cues_mesh = Mesh(geometry=cues_geo, material=cue_material)
            cues_mesh.set_position([-12, 0, -8])
            self.static_scene.add(cues_mesh)
            
        if cue_box_geo:
            cue_box_mesh = Mesh(geometry=cue_box_geo, material=legs_material)
            cue_box_mesh.set_position([-12, 0, -8])
            self.static_scene.add(cue_box_mesh)

        #Sonic
        tv_geometry = CustomGeometry(1,1,1,my_obj_reader("objects/television.obj")).get("tv")
        tv_material = PhongMaterial(
            texture=Texture("images/tv_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        tv = Mesh(geometry=tv_geometry,material=tv_material)
        tv.set_position([14,1.1,-14])
        self.static_scene.add(tv)
        sonic_geometry = RectangleGeometry(0.7,0.7)
        tile_set = Texture("images/sonic-spritesheet.jpg")
        sprite_material = SpriteMaterial(
            tile_set,
            {
                "billboard": False,
                "tileCount": [4, 3],
                "tileNumber": 0
            }
        )
        self.tiles_per_second = 8
        self.sprite = Mesh(sonic_geometry, sprite_material)
        self.sprite.set_position([14,1.1,-13.60])
        self.static_scene.add(self.sprite)

        #ceiling_lights
        circlelight_geo = SphereGeometry(radius=0.1)
        circlelight_material = SurfaceMaterial(
            property_dict={"baseColor":[0.7, 0.7, 1]},
        )
        lightcable_geo = CylinderGeometry(radius=0.02,height=1.4)
        lightcable_material = LambertMaterial(
            property_dict={"baseColor":[0, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        for i in range(5):
            lightcable = Mesh(geometry=lightcable_geo,material=lightcable_material)
            circlelight = Mesh(geometry=circlelight_geo, material=circlelight_material)
            circlelight.set_position([-9 - i,3.5,12])
            lightcable.set_position([-9 - i,4.3,12])
            self.static_scene.add(circlelight)
            self.static_scene.add(lightcable)
            self.glow_scene.add(circlelight)
        
        # Snooker table ceiling lights visual elements
        for i in range(3):
            snooker_lightcable = Mesh(geometry=lightcable_geo,material=lightcable_material)
            snooker_circlelight = Mesh(geometry=circlelight_geo, material=circlelight_material)
            snooker_circlelight.set_position([-12,3.5,-10.8 + i])
            snooker_lightcable.set_position([-12,4.3,-10.8 + i])
            self.static_scene.add(snooker_circlelight)
            self.static_scene.add(snooker_lightcable)
            self.glow_scene.add(snooker_circlelight)
        
        #BarStand
        barstand_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/barstand.obj')).get("barstand")
        barstand_material = LambertMaterial(
            texture=Texture("images/metal2.jpg"), # Textura de metal
            bump_texture=Texture("images/metal2_normal.png"), # Corrigido para .png
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        barstand = Mesh(geometry=barstand_geometry,material=barstand_material)
        barstand.rotate_y(math.radians(90))
        barstand.set_position([-10,0,12])
        self.static_scene.add(barstand)

        #BarMan
        barman_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/barman.obj'))
        body_geo = barman_geometry.get("Body")
        head_geo = barman_geometry.get("Head")
        body_material = LambertMaterial(
            texture=Texture("images/body_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        #body_material = TextureMaterial(Texture("images/body_texture.png"))
        head_material = LambertMaterial(
            texture=Texture("images/head_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        #head_material = TextureMaterial(Texture("images/head_texture.png"))
        self.head = Mesh(geometry=head_geo,material=head_material)
        self.body = Mesh(geometry=body_geo,material=body_material)
        self.head.set_position([-11,1.6,13])
        self.head.rotate_y(math.radians(180))
        self.body.local_matrix = self.head.local_matrix
        self.dynamic_scene.add(self.head)
        self.static_scene.add(self.body)

        #Shelf
        shelf_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/shelf.obj')).get("shelf")
        shelf_material = LambertMaterial(
            texture=Texture("images/metal2.jpg"), # Textura de metal
            bump_texture=Texture("images/metal2_normal.png"), # Corrigido para .png
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        shelf = Mesh(geometry=shelf_geometry,material=shelf_material)
        shelf.rotate_y(math.radians(180))
        shelf.set_position([-11.1,0,14.3])
        self.static_scene.add(shelf)
        #bottles
        BeerGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/bottle.obj'))
        self.bottle_geo = BeerGeometries.get("outer")  # Store bottle geometry
        self.liquid_geo = BeerGeometries.get("inner")  # Store liquid geometry
        cork_geo = BeerGeometries.get("rolha")
        
        # Store bottle factory and positions as instance variables
        self.bottle_factory = InstancedObjectFactory(
            self.bottle_geo,  # Use the instance variable
            self._get_cached_material(
                "PhongMaterial",
            property_dict={"baseColor":[0, 0.7, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True,
            opacity=0.2
        )
        )
        
        # Add bottle instances
        bottle_x = -9.5
        bottle_y = 1
        for i in range(3):
            for j in range(7):
                self.bottle_factory.add_instance([bottle_x, bottle_y, 14.5])
                bottle_x -= 0.5
            bottle_y += 0.7
            bottle_x = -9.5
            
        # Create bottle mesh
        self.bottle_mesh = self.bottle_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(self.bottle_mesh)
        
        # Store initial number of bottles
        self.remaining_bottles = len(self.bottle_factory.positions)
        
        # Create liquid instances and store as instance variable
        self.liquid_factory = InstancedObjectFactory(
            self.liquid_geo,
            self._get_cached_material(
                "TransparentMaterial",
                color=[0.3,0.3,0],
                opacity=0.5
        )
        )
        self.liquid_factory.add_instances(self.bottle_factory.positions)
        self.liquid_mesh = self.liquid_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(self.liquid_mesh)
        
        # Create cork instances and store as instance variable
        self.cork_factory = InstancedObjectFactory(
            cork_geo,
            self._get_cached_material(
                "LambertMaterial",
                property_dict={"baseColor":[0.8, 0.8, 0.0]},
                number_of_light_sources=self.light_number,
                use_shadow=True
            )
        )
        self.cork_factory.add_instances(self.bottle_factory.positions)
        self.cork_mesh = self.cork_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(self.cork_mesh)




        #BarStool 
        barstool_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/barstool.obj')).get("Material.001")
        barstool_material = PhongMaterial(
            texture=Texture("images/barstooltexture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        x_coord = 0
        for i in range(4):
            barstool = Mesh(geometry=barstool_geometry, material=barstool_material)
            barstool.set_position([-12.5 + x_coord,0,11])
            self.static_scene.add(barstool)
            x_coord += 1
        
        #StageWireframe
        wireframe_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/stage_wireframe.obj')).get("Material")
        wireframe_material = PhongMaterial(
            property_dict={"baseColor":[0.1, 0.1, 0.1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        wireframe = Mesh(geometry=wireframe_geometry,material=wireframe_material)
        wireframe.set_position([0,0,-10])
        self.static_scene.add(wireframe)

        #Spotlight
        SpotlightGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/spotlight.obj'))
        support_geo = SpotlightGeometries.get("spotlightsupport")
        spotlight_geo = SpotlightGeometries.get("spotlight")
        light_geo = SpotlightGeometries.get("light")
        spotlight_material = PhongMaterial(
            property_dict={"baseColor":[0.05, 0.05, 0.05]},
            number_of_light_sources=self.light_number,
            use_shadow=True,      
        )
        light_material = SurfaceMaterial(property_dict={"baseColor": [1.0, 1.0, 0.8]})
        support = Mesh(geometry=support_geo,material=spotlight_material)
        self.spotlight = Mesh(geometry=spotlight_geo,material=spotlight_material)
        self.light = Mesh(geometry=light_geo,material=light_material)
        support.rotate_y(math.radians(180))
        support.set_position([0,3.9,-10])
        self.spotlight.local_matrix = support.local_matrix
        self.light.local_matrix = support.local_matrix
        self.static_scene.add(support)
        self.dynamic_scene.add(self.spotlight)
        self.dynamic_scene.add(self.light)

        #Stage
        stagegeometries = CustomGeometry(1,1,1,my_obj_reader('objects/stage.obj'))
        stage_geometry = stagegeometries.get("stage")
        
        frame_geometry =  stagegeometries.get("frame")
        cloth_geometry1 = stagegeometries.get("cloth01")
        cloth_geometry2 = stagegeometries.get("cloth02")
        backstage_geometry = stagegeometries.get("backstage")
        stage_material = PhongMaterial(
            texture=Texture("images/lightwood.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        stage = Mesh(geometry=stage_geometry,material=stage_material)
        stage.set_position([0,0,-11.5])
        self.static_scene.add(stage)
        frame_material = LambertMaterial(
            property_dict={"baseColor":[0.1, 0.1, 0.2]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        frame = Mesh(geometry=frame_geometry,material=frame_material)
        frame.local_matrix = stage.local_matrix
        self.static_scene.add(frame)
        cloth_material = PhongMaterial(
            property_dict={"baseColor":[0.5, 0, 0.2]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        cloth1 = Mesh(geometry=cloth_geometry1,material=cloth_material)
        cloth1.local_matrix = stage.local_matrix
        self.static_scene.add(cloth1)
        cloth2 = Mesh(geometry=cloth_geometry2,material=cloth_material)
        cloth2.local_matrix = stage.local_matrix
        self.static_scene.add(cloth2)
        backstage_material = PhongMaterial(
            property_dict={"baseColor": [0.1,0.1,0.1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        backstage = Mesh(geometry=backstage_geometry,material=backstage_material)
        backstage.local_matrix = stage.local_matrix
        self.static_scene.add(backstage)

        #PuffChair
        PuffchairGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/puffchair.obj'))
        cushion_geo = PuffchairGeometries.get("chaircushion")
        chairbase_geo = PuffchairGeometries.get("chairbase")
        cushion_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0.2, 0.7]},
            number_of_light_sources=self.light_number,
            use_shadow=True,      
        )
        chairbase_material = PhongMaterial(
            property_dict={"baseColor":[0.05, 0.05, 0.05]},
            number_of_light_sources=self.light_number,
            use_shadow=True,      
        )
        # Create puff chair instances
        self.cushion_geo = cushion_geo  # Store as class attribute
        self.chairbase_geo = chairbase_geo  # Store as class attribute
        self.cushion_material = cushion_material  # Store as class attribute
        self.chairbase_material = chairbase_material  # Store as class attribute
        
        cushion_factory = InstancedObjectFactory(
            self.cushion_geo,
            self.cushion_material
        )
        chairbase_factory = InstancedObjectFactory(
            self.chairbase_geo,
            self.chairbase_material
        )
        
        # Store chair positions for later use
        self.chair_positions = []
        
        # Add chair instances around tables
        for tx, ty, tz in table_positions:
            for i in range(4):
                angle_deg = i * 90
                angle_rad = math.radians(angle_deg)
                dx = math.sin(angle_rad) * 1.5
                dz = math.cos(angle_rad) * 1.5
                pos = [tx + dx, 0, tz + dz]
                rot = [0, angle_rad + math.pi, 0]
                cushion_factory.add_instance(pos, rot)
                chairbase_factory.add_instance(pos, rot)
                self.chair_positions.append({'position': pos, 'rotation': rot})
                
        client_geo = CustomGeometry(1,1,1,my_obj_reader('objects/client.obj')).get("Body")
        client1_material = LambertMaterial(
            texture=Texture('images/afro_texture.png'),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        client2_material = LambertMaterial(
            texture=Texture('images/body_texture.png'),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        client = Mesh(geometry=client_geo, material=client1_material)
        client2 = Mesh(geometry=client_geo, material=client1_material)
        client.rotate_y(math.radians(-90))
        client.set_position([6.3,0.7,5])
        self.static_scene.add(client)
        client2.set_position([-5,0.7,-6.3])
        self.static_scene.add(client2)
        

        # Create chair meshes
        cushion_mesh = cushion_factory.build_mesh(self._create_instanced_mesh)
        chairbase_mesh = chairbase_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(cushion_mesh)
        self.static_scene.add(chairbase_mesh)

        #RoundTables
        roundtable_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/table.obj')).get("table")
        roundtable_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0.2, 0.2]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        # Criar uma mesa para cada posição na lista table_positions
        for pos in table_positions:
            roundtable = Mesh(geometry=roundtable_geometry,material=roundtable_material)
            roundtable.set_position(pos)
            self.static_scene.add(roundtable)

        #lamps
        LampGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/lamp.obj'))
        base_geometry = LampGeometries.get("base")
        lamp_geometry= LampGeometries.get("lamp")
        lampshade_geometry= LampGeometries.get("lampshade")
        switch_geometry= LampGeometries.get("switch")
        base_material = PhongMaterial(
            property_dict={"baseColor":[0.1, 0.1, 0.1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        lamp_material = PhongMaterial(
            property_dict={"baseColor":[0.8, 0.8, 1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        lampshade_material = PhongMaterial(
            property_dict={"baseColor":[0.3, 0.2, 1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        switch_material  = PhongMaterial(
            property_dict={"baseColor":[0.1, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        # Create lamp instances
        base_factory = InstancedObjectFactory(base_geometry, base_material)
        lamp_factory = InstancedObjectFactory(lamp_geometry, lamp_material)
        lampshade_factory = InstancedObjectFactory(lampshade_geometry, lampshade_material)
        switch_factory = InstancedObjectFactory(switch_geometry, switch_material)
        
        # Add lamp instances
        for pos in table_positions:
            lamp_pos = pos + np.array([0, 0.9, 0])
            base_factory.add_instance(lamp_pos)
            lamp_factory.add_instance(lamp_pos)
            lampshade_factory.add_instance(lamp_pos)
            switch_factory.add_instance(lamp_pos)
            
        # Create lamp meshes
        base_mesh = base_factory.build_mesh(self._create_instanced_mesh)
        lamp_mesh = lamp_factory.build_mesh(self._create_instanced_mesh)
        lampshade_mesh = lampshade_factory.build_mesh(self._create_instanced_mesh)
        switch_mesh = switch_factory.build_mesh(self._create_instanced_mesh)
        
        self.static_scene.add(base_mesh)
        self.static_scene.add(lamp_mesh)
        self.static_scene.add(lampshade_mesh)
        self.static_scene.add(switch_mesh)
        #mirrorball
        cable_geometry = CylinderGeometry(radius=0.02,height=1)
        cable_material  = PhongMaterial(
            property_dict={"baseColor": [0,0,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        cable = Mesh(cable_geometry,cable_material)
        cable.set_position([0,4.5,0])
        self.static_scene.add(cable)
        mirrorball_geometry = SphereGeometry(radius=0.5)
        mirrorball_material = PhongMaterial(
            texture=Texture("images/mirrorball.jpg"),
            bump_texture=Texture("images/mirrorball_normal.jpg"),
            property_dict={"bumpStrength": 10},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        self.mirrorball = Mesh(geometry=mirrorball_geometry, material=mirrorball_material)
        self.mirrorball.set_position([0,4,0])
        self.static_scene.add(self.mirrorball)

        # Adicionar lista de lightcones para controle
        self.lightcones = []
        
        lightcone_geo = ConeGeometry(radius=0.1, height=5)
        lightcone_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone = Mesh(lightcone_geo,lightcone_material)
        lightcone.set_position([0,2,-1.5])
        lightcone.set_direction([0,-1,1])
        self.static_scene.add(lightcone)
        self.lightcones.append(lightcone)

        lightcone1_geo = ConeGeometry(radius=0.1, height=5)
        lightcone1_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone1 = Mesh(lightcone1_geo,lightcone1_material)
        lightcone1.set_position([-1.5,2,0])
        lightcone1.set_direction([1,-1,0])
        self.static_scene.add(lightcone1)
        self.lightcones.append(lightcone1)

        lightcone2_geo = ConeGeometry(radius=0.1, height=5)
        lightcone2_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone2 = Mesh(lightcone1_geo,lightcone1_material)
        lightcone2.set_position([1.5,2,0])
        lightcone2.set_direction([-1,-1,0])
        self.static_scene.add(lightcone2)
        self.lightcones.append(lightcone2)

        lightcone3_geo = ConeGeometry(radius=0.1, height=5)
        lightcone3_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone3 = Mesh(lightcone_geo,lightcone_material)
        lightcone3.set_position([0,2,1.5])
        lightcone3.set_direction([0,-1,-1])
        self.static_scene.add(lightcone3)
        self.lightcones.append(lightcone3)
        
        # Adicionar mais 4 lightcones para as diagonais
        lightcone4_geo = ConeGeometry(radius=0.1, height=5)
        lightcone4_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone4 = Mesh(lightcone4_geo,lightcone4_material)
        lightcone4.set_position([-1.0,2,-1.0])
        lightcone4.set_direction([1,-1,1])
        self.static_scene.add(lightcone4)
        self.lightcones.append(lightcone4)

        lightcone5_geo = ConeGeometry(radius=0.1, height=5)
        lightcone5_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone5 = Mesh(lightcone5_geo,lightcone5_material)
        lightcone5.set_position([1.0,2,-1.0])
        lightcone5.set_direction([-1,-1,1])
        self.static_scene.add(lightcone5)
        self.lightcones.append(lightcone5)

        lightcone6_geo = ConeGeometry(radius=0.1, height=5)
        lightcone6_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone6 = Mesh(lightcone6_geo,lightcone6_material)
        lightcone6.set_position([-1.0,2,1.0])
        lightcone6.set_direction([1,-1,-1])
        self.static_scene.add(lightcone6)
        self.lightcones.append(lightcone6)

        lightcone7_geo = ConeGeometry(radius=0.1, height=5)
        lightcone7_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone7 = Mesh(lightcone7_geo,lightcone7_material)
        lightcone7.set_position([1.0,2,1.0])
        lightcone7.set_direction([-1,-1,-1])
        self.static_scene.add(lightcone7)
        self.lightcones.append(lightcone7)

        #DanceFloor
        DancefloorGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/dancefloor.obj'))
        color1_geo = DancefloorGeometries.get("color1")
        color2_geo = DancefloorGeometries.get("color2")
        color1_material = SurfaceMaterial(property_dict={"baseColor": [0.6,0,0.6]})
        color2_material = SurfaceMaterial(property_dict={"baseColor": [0.0, 0.6, 0.6]})
        self.dancefloor_color1 = Mesh(geometry=color1_geo,material=color1_material)
        self.dancefloor_color2 = Mesh(geometry=color2_geo,material=color2_material)
        self.dancefloor_color1.set_position([0,0.02,0])
        self.dancefloor_color2.set_position([0,0.02,0])
        self.static_scene.add(self.dancefloor_color1)
        self.static_scene.add(self.dancefloor_color2)

        #NeonSign
        NeonsignGeometries = CustomGeometry(1, 1, 1, my_obj_reader('objects/neonsign.obj'))
        blue_geo = NeonsignGeometries.get("BlueText")
        yellow_geo = NeonsignGeometries.get("YellowText")
        black_geo = NeonsignGeometries.get("BlackText")
        self.bluesign_material = SurfaceMaterial(property_dict={"baseColor": [0.0, 1.0, 1.0]})
        self.yellowsign_material = SurfaceMaterial(property_dict={"baseColor": [1.0, 1.0, 0.0]})
        blacksign_material = SurfaceMaterial(property_dict={"baseColor": [0., 0, 0]})
        self.blueSign = Mesh(blue_geo,self.bluesign_material)
        self.yellowSign = Mesh(yellow_geo,self.yellowsign_material)
        blackSign = Mesh(black_geo,blacksign_material)

        self.blueSign.rotate_y(math.radians(90))
        self.blueSign.set_position([-14.9, 2, 5])
        self.yellowSign.local_matrix = self.blueSign.local_matrix
        blackSign.local_matrix = self.blueSign.local_matrix
        self.static_scene.add(self.blueSign)
        self.static_scene.add(self.yellowSign)
        self.static_scene.add(blackSign)

        #ExitSign
        exit_geo = CustomGeometry(1,1,1,my_obj_reader('objects/exitsign.obj')).get("text")
        exit_material = SurfaceMaterial(property_dict={"baseColor": [0.0, 1.0, 0]})
        exitsign = Mesh(geometry=exit_geo,material=exit_material)
        exitsign.rotate_y(math.radians(180))
        exitsign.set_position([12.1,2.5,15])
        self.static_scene.add(exitsign)

        #JUkeboxSign
        jukeboxsign_geo = CustomGeometry(1,1,1,my_obj_reader('objects/jukeboxneonsign.obj')).get("neon")
        jukeboxsign_material = SurfaceMaterial(property_dict={"baseColor": [0.8, 0.2, 0.2]}) # Cor alterada para rosa escuro
        self.jukeboxsign = Mesh(geometry=jukeboxsign_geo,material=jukeboxsign_material)


        # Escalar o neon pela metade manipulando a local_matrix
        scale_factor = 0.5
        scale_matrix = np.array([
            [scale_factor, 0.0, 0.0, 0.0],
            [0.0, scale_factor, 0.0, 0.0],
            [0.0, 0.0, scale_factor, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        self.jukeboxsign.local_matrix = self.jukeboxsign.local_matrix @ scale_matrix

        self.jukeboxsign.rotate_y(math.radians(180))
        self.jukeboxsign.set_position([1.95, 1.5, 15]) # Aumentei a coordenada Y para subir o neon
        self.static_scene.add(self.jukeboxsign)

        #sign
        sign_geo = CustomGeometry(1,1,1,my_obj_reader('objects/sign.obj')).get("girl")
        sign_material = SurfaceMaterial(property_dict={"baseColor":[0.2,0,0.8]},)
        self.sign=Mesh(geometry=sign_geo,material=sign_material)
        self.sign2=Mesh(geometry=sign_geo,material=sign_material)
        self.sign.set_position([-10,0,-15])
        self.sign2.rotate_y(math.radians(180))
        self.sign2.set_position([9,0,-15])
        self.static_scene.add(self.sign)
        self.static_scene.add(self.sign2)


    
        #Jukebox
        wood_geo, neon_geo, metal_geo, red_geo, metalmesh_geo, selectcoin_geo, selectsong_geo, vinyl_geo, songs1_geo, songs2_geo, glass_geo = JukeboxGeometry(1,1,1,my_obj_reader('objects/jukebox.obj'))
        wood_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        neon_material = SurfaceMaterial(
            property_dict={"baseColor": [0.0, 1.0, 1.0]},
        )
        metal_material = PhongMaterial(
            property_dict={"baseColor":[0.4, 0.4, 0.4]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        red_material = PhongMaterial(
            property_dict={"baseColor":[0.8, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        metalmesh_material = PhongMaterial(
            texture=Texture("images/metalmesh.jpg"),
            bump_texture=Texture("images/metalmesh_normal.jpg"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        selectcoin_material = PhongMaterial(
            texture=Texture("images/selectcoin.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        selectsong_material = PhongMaterial(
            texture=Texture("images/selectsong.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        vinyl_material = PhongMaterial(
            texture=Texture("images/vinyltexture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        songlist_material = LambertMaterial(
            texture=Texture("images/jukebox_label.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        glass_material = TransparentMaterial(color=[0.9,0.9,0.1],opacity=0.1)
        wood = Mesh(geometry=wood_geo,material=wood_material)
        self.neon = Mesh(geometry=neon_geo,material=neon_material)
        metal = Mesh(geometry=metal_geo,material=metal_material)
        red = Mesh(geometry=red_geo,material=red_material)
        metalmesh = Mesh(geometry=metalmesh_geo,material=metalmesh_material)
        selectcoin = Mesh(geometry=selectcoin_geo,material=selectcoin_material)
        selectsong = Mesh(geometry=selectsong_geo,material=selectsong_material)
        self.vinyl = Mesh(geometry=vinyl_geo,material=vinyl_material)
        songlist1 = Mesh(geometry=songs1_geo,material=songlist_material)
        songlist2 = Mesh(geometry=songs2_geo,material=songlist_material)
        glass = Mesh(geometry=glass_geo,material=glass_material)
        wood.rotate_y(math.radians(180))
        wood.set_position([0,0,14.5])
        self.neon.local_matrix = wood.local_matrix
        metal.local_matrix = wood.local_matrix
        red.local_matrix = wood.local_matrix
        metalmesh.local_matrix = wood.local_matrix
        selectcoin.local_matrix = wood.local_matrix
        selectsong.local_matrix = wood.local_matrix
        self.vinyl.local_matrix = wood.local_matrix
        songlist1.local_matrix = wood.local_matrix
        songlist2.local_matrix = wood.local_matrix
        glass.local_matrix = wood.local_matrix
        self.static_scene.add(wood)
        self.static_scene.add(self.neon)
        self.static_scene.add(metal)
        self.static_scene.add(red)
        self.static_scene.add(metalmesh)
        self.static_scene.add(selectcoin)
        self.static_scene.add(selectsong)
        self.static_scene.add(self.vinyl)
        self.static_scene.add(songlist1)
        self.static_scene.add(songlist2)
        self.static_scene.add(glass)

        ################INSTRUMENTS###########################

        mandolin_geo = CustomGeometry(1,1,1,my_obj_reader('objects/mandolin.obj'))
        red_mandolin_geo = mandolin_geo.get("Red")
        black_mandolin_geo = mandolin_geo.get("Black")
        brown_mandolin_geo = mandolin_geo.get("Brown")
        strings_geo = mandolin_geo.get("strings")
        red_mandolin_material = PhongMaterial(
            property_dict={"baseColor": [0.4,0,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        black_mandolin_material = PhongMaterial(
            property_dict={"baseColor": [0,0,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        brown_mandolin_material = PhongMaterial(
            property_dict={"baseColor": [0.2,0.1,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        strings_mandolin_material = PhongMaterial(
            property_dict={"baseColor": [0.8,0.8,0.8]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        red_part = Mesh(geometry=red_mandolin_geo,material=red_mandolin_material)
        black_part = Mesh(geometry=black_mandolin_geo,material=black_mandolin_material)
        brown_part = Mesh(geometry=brown_mandolin_geo,material=brown_mandolin_material)
        mandolin_strings = Mesh(geometry=strings_geo,material=strings_mandolin_material)
        self.mandolin = Object3D()
        self.mandolin.add(red_part)
        self.mandolin.add(black_part)
        self.mandolin.add(brown_part)
        self.mandolin.add(mandolin_strings)
        self.mandolin.set_position([-2,0.5,-12])
        self.dynamic_scene.add(self.mandolin)
        self.instruments.append({
            'object': self.mandolin,
            'base_position': [-2, self.instrument_vertical_offset, -12],
            'phase_offset': 0.0
        })

        fiddle_geo = CustomGeometry(1,1,1,my_obj_reader('objects/fiddle.obj'))
        wood_fiddle_geo = fiddle_geo.get("fiddle")
        black_fiddle_geo = fiddle_geo.get("black")
        fiddle_strings_geo = fiddle_geo.get("strings")
        fiddle_material = PhongMaterial(
            texture=Texture("images/fiddle_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        wood_part = Mesh(geometry=wood_fiddle_geo,material=fiddle_material)
        fiddle_black_part = Mesh(geometry=black_fiddle_geo, material=black_mandolin_material)
        fiddle_strings = Mesh(geometry=fiddle_strings_geo,material=strings_mandolin_material)
        self.fiddle = Object3D()
        self.fiddle.add(wood_part)
        self.fiddle.add(fiddle_black_part)
        self.fiddle.add(fiddle_strings)
        self.fiddle.set_position([2,0.5,-12])
        self.dynamic_scene.add(self.fiddle)
        self.instruments.append({
            'object': self.fiddle,
            'base_position': [2, self.instrument_vertical_offset, -12],
            'phase_offset': math.pi/2  # offset to vary movement
        })

        harmonica_player_geo = CustomGeometry(1,1,1,my_obj_reader('objects/harmonicaplayer.obj'))
        harmonica_wood_geo = harmonica_player_geo.get("Madeira")
        harmonica_metal_geo = harmonica_player_geo.get("Metal")
        harmonica_wood_material = PhongMaterial(
            texture=Texture('images/wood.jpg'),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        harmonica_metal_material = PhongMaterial(
            texture=Texture('images/metal.jpg'),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        harmonica_metal = Mesh(geometry=harmonica_wood_geo,material=harmonica_wood_material)
        harmonica_wood = Mesh(geometry=harmonica_metal_geo,material=harmonica_metal_material)
        self.harmonica = Object3D()
        self.harmonica.add(harmonica_metal)
        self.harmonica.add(harmonica_wood)
        self.harmonica.set_position([0, 1.5, -10])
        self.dynamic_scene.add(self.harmonica)
        # Removed harmonica from instruments list since it should stay in place

        # Banjo
        banjo_geo = CustomGeometry(1.5,1.5,1.5,my_obj_reader('objects/banjo.obj'))  # Increased size by 1.5x
        wood_banjo_geo = banjo_geo.get("madeira")
        metal_banjo_geo = banjo_geo.get("branco")
        strings_banjo_geo = banjo_geo.get("cordas")
        preto_banjo_geo = banjo_geo.get("preto")
        wood_banjo_material = PhongMaterial(
            property_dict={"baseColor": [0.2,0.1,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        metal_banjo_material = PhongMaterial(
            property_dict={"baseColor": [0.8,0.8,0.8]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        strings_banjo_material = PhongMaterial(
            property_dict={"baseColor": [0.5,0.5,0.5]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        wood_part = Mesh(geometry=wood_banjo_geo,material=wood_banjo_material)
        metal_part = Mesh(geometry=metal_banjo_geo,material=metal_banjo_material)
        banjo_strings = Mesh(geometry=strings_banjo_geo,material=strings_banjo_material)
        banjo_preto = Mesh(geometry=preto_banjo_geo,material=black_mandolin_material)
        self.banjo = Object3D()
        self.banjo.add(wood_part)
        self.banjo.add(metal_part)
        self.banjo.add(banjo_strings)
        self.banjo.add(banjo_preto)
        self.banjo.set_position([0,0.5,-13])  # Positioned between mandolin (-2) and fiddle (2)
        self.dynamic_scene.add(self.banjo)
        self.instruments.append({
            'object': self.banjo,
            'base_position': [0, self.instrument_vertical_offset, -12],  # Updated base position
            'phase_offset': math.pi/4  # different offset for varied movement
        })

        harmonicaplayer_head_geo = harmonica_player_geo.get("Head")
        harmonicaplayer_body_geo = harmonica_player_geo.get("Body")
        harmonicaplayer_legs_geo = harmonica_player_geo.get("legs")

        harmonicaplayer_head_material = PhongMaterial(
            texture=Texture("images/head_harmonicaplayer_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        harmonicaplayer_body_material = PhongMaterial(
            texture=Texture("images/body_harmonicaplayer_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        self.HarmonicaPlayerHead = Mesh(geometry=harmonicaplayer_head_geo,material=harmonicaplayer_head_material)
        self.HarmonicaPlayerBody = Mesh(geometry=harmonicaplayer_body_geo,material=harmonicaplayer_body_material)
        self.HarmonicaPlayerLegs = Mesh(geometry=harmonicaplayer_legs_geo,material=black_mandolin_material)
        self.HarmonicaPlayer = Object3D()
        self.HarmonicaPlayer.add(self.HarmonicaPlayerHead)
        self.HarmonicaPlayer.add(self.HarmonicaPlayerBody)
        self.HarmonicaPlayer.add(self.HarmonicaPlayerLegs)
        self.HarmonicaPlayer.set_position([0,1.5,-10])
        self.dynamic_scene.add(self.HarmonicaPlayer)

        #Sonic Update
        tile_number = math.floor(self.time * self.tiles_per_second)
        self.sprite.material.uniform_dict["tileNumber"].data = tile_number

        #####glow scene#####
        
        
        #Jukebox Neon
        
        self.glow_scene.add(self.neon)
        
        #Neon Sign
        self.current_glow = self.blueSign
        self.glow_scene.add(self.current_glow)

        #exit sign
        self.glow_scene.add(exitsign)

        #jukebox sign
        self.glow_scene.add(self.jukeboxsign)

        #sign
        self.glow_scene.add(self.sign)
        self.glow_scene.add(self.sign2)

        #spotlight
        self.glow_scene.add(self.light)

        #Globe
        glowMaterial = SurfaceMaterial(property_dict={"baseColor": [0.4, 0.4, 0.4]})
        glowingMirrorBall = Mesh(mirrorball_geometry,glowMaterial)
        glowingMirrorBall.local_matrix = self.mirrorball.local_matrix
        self.glow_scene.add(glowingMirrorBall)

        #Mesh
        sonicglow_material = SurfaceMaterial(property_dict={"baseColor": [0.1, 0.1, 0.1]})
        sonic_glow = Mesh(sonic_geometry,sonicglow_material)
        sonic_glow.local_matrix = self.sprite.local_matrix
        self.glow_scene.add(sonic_glow)

        #DanceFloor
        self.current_color = self.dancefloor_color1
        self.glow_scene.add(self.current_color)

        #ceilinglights
        self.glow_scene.add(circlelight)


        #glow postprocessing
        glow_target = RenderTarget(resolution=[400, 300])  # Reduced resolution for better performance
        self.glow_pass = Postprocessor(self.renderer, self.glow_scene, self.camera, glow_target)
        # Reduced blur radius for better performance
        self.glow_pass.add_effect(horizontalBlurEffect(texture_size=[400,300], blur_radius=25))
        self.glow_pass.add_effect(verticalBlurEffect(texture_size=[400,300], blur_radius=25))
        


        # combining results of glow effect with main scene
        self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
        self.combo_pass.add_effect(
            additiveBlendEffect(
                blend_texture=glow_target.texture,
                original_strength=self.brightness,
                blend_strength=1.5
            )
        )
        self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
        #self.combo_pass.add_effect(self.tint)
        self.combo_pass.add_effect(self.pixelate)
        #self.combo_pass.add_effect(self.color_reduce)
        self.combo_pass.add_effect(self.blur_h)
        self.combo_pass.add_effect(self.blur_v)
        self.combo_pass.add_effect(self.drunk_effect)


        self.brightness_effect = additiveBlendEffect(
            blend_texture=glow_target.texture,
            original_strength=self.brightness,
            blend_strength=1.5
        )
        self.combo_pass.add_effect(self.brightness_effect)
        self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
        # self.combo_pass.add_effect(self.tint)
        self.combo_pass.add_effect(self.pixelate)
        # self.combo_pass.add_effect(self.color_reduce)
        self.combo_pass.add_effect(self.blur_h)
        self.combo_pass.add_effect(self.blur_v)
        self.combo_pass.add_effect(self.drunk_effect)
        self.combo_pass.add_effect(self.brightness_effect)

        # HUD Scene
        self.show_menu = True
        self.menu_state = "main"
        pygame.mouse.set_visible(True)
        self.hudScene = Scene()
        self.hudCamera = Camera()
        width, height = self.screen_size
        self.hudCamera.set_orthographic(0, width, 0, height, 1, -1)

        # Background (GIF frame)
        menu_bg = RectangleGeometry(width=width, height=height, position=[width / 2, height / 2], alignment=[0.5, 0.5])
        bg_texture = Texture("images/bar-background-menu.gif")
        menu_bg_mesh = Mesh(menu_bg, TextureMaterial(bg_texture))
        menu_bg_mesh.set_position([0, 0, 0.1])
        self.hudScene.add(menu_bg_mesh)

        # Title
        title_geo = RectangleGeometry(
            width=width * 0.6,
            height=height * 0.15,
            position=[width / 2, height - 80],
            alignment=[0.5, 1]
        )
        title_mat = TextureMaterial(Texture("images/title.png"))
        title_mesh = Mesh(title_geo, title_mat)
        self.hudScene.add(title_mesh)

        # Buttons
        self.menu_buttons = []

        center_x = width / 2
        button_specs = [
            ("Start Game", "start", [center_x, height * 0.6], "start_game"),
            ("Settings", "settings", [center_x, height * 0.45], "open_settings"),
            ("Exit", "exit", [center_x, height * 0.3], "exit_game"),
        ]

        self.settings_buttons = []

        settings_specs = [
            ("camerasensitivity", "camerasensitivity", [center_x, height * 0.6], "camerasensitivity"),
            ("Brightness", "Brightness", [center_x, height * 0.45], "Brightness"),
            ("resetsettings", "resetsettings", [center_x, height * 0.3], "resetsettings"),
            ("back", "back", [center_x, height * 0.15], "back"),
        ]

        self.sensitivity_buttons = []

        sensitivity_specs = [
            ("slow", "slow", [center_x, height * 0.6], "slow"),
            ("normal", "normal", [center_x, height * 0.45], "normal"),
            ("fast", "fast", [center_x, height * 0.3], "fast"),
            ("back", "back", [center_x, height * 0.15], "back2"),
        ]



        self.brightness_buttons = []

        brightness_specs = [
            ("Dark", "Dark", [center_x, height * 0.6], "Dark"),
            ("Normal", "Normal", [center_x, height * 0.45], "Normal"),
            ("Bright", "Bright", [center_x, height * 0.3], "Bright"),
            ("back", "back", [center_x, height * 0.15], "back3"),
        ]

        self.jukebox_buttons = []

        jukebox_specs = [
            ("Play Song 1", "res_Banjo", [center_x, height * 0.75], "play_song1"),
            ("Play Song 2", "res_Violino", [center_x, height * 0.6], "play_song2"),
            ("Play Song 3", "res_Mandolin", [center_x, height * 0.45], "play_song3"),
            ("Play Song 4", "res_Bateria", [center_x, height * 0.3], "play_song4"),
            ("Close", "back", [center_x, height * 0.15], "close_jukebox")
        ]

        for label, base_name, position, action in settings_specs:
            self.create_menu_button(base_name, position, action, self.settings_buttons, add_to_scene=False)

        for label, base_name, position, action in jukebox_specs:
            self.create_menu_button(base_name, position, action, self.jukebox_buttons, add_to_scene=False)

        for label, base_name, position, action in sensitivity_specs:
            self.create_menu_button(base_name, position, action, self.sensitivity_buttons, add_to_scene=False)

        for label, base_name, position, action in brightness_specs:
            self.create_menu_button(base_name, position, action, self.brightness_buttons, add_to_scene=False)

        for label, base_name, position, action in button_specs:
            self.create_menu_button(base_name, position, action, self.menu_buttons, add_to_scene=True)

        import os

        # === Load GIF background frames ===
        self.bg_textures = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frame_folder = os.path.join(script_dir, "images", "gif_frames/background")
        frame_files = sorted([f for f in os.listdir(frame_folder) if f.endswith(".png")])

        for frame_file in frame_files:
            texture = Texture(os.path.join(frame_folder, frame_file))
            self.bg_textures.append(texture)

        self.num_bg_frames = len(self.bg_textures)
        self.bg_frame_rate = 8
        self.menu_bg_mesh = menu_bg_mesh

        # Nova cena HUD para mensagens contextuais
        self.context_hud = Scene()
        self.context_camera = Camera()
        self.context_camera.set_orthographic(0, width, 0, height, 1, -1)
        self.context_label = None

        # === HUD da cerveja no jogo ===
        self.beer_hud_scene = Scene()
        self.beer_hud_camera = Camera()
        self.beer_hud_camera.set_orthographic(0, self.screen_size[0], 0, self.screen_size[1], 1, -1)

        self.beer_icon_textures = []
        self.total_beer_frames = 12  # ou o número que tiveres
        self.beers_drank = 0

        for i in range(self.total_beer_frames):
            texture = Texture(f"images/gif_frames/beer/frame_{i + 1:03d}.png")
            self.beer_icon_textures.append(texture)

        beer_icon_geo = RectangleGeometry(width=300, height=300, position=[60, self.screen_size[1] - 60],
                                          alignment=[0.5, 0.5])
        beer_icon_mat = TextureMaterial(self.beer_icon_textures[0])
        self.beer_icon_mesh = Mesh(beer_icon_geo, beer_icon_mat)
        self.beer_hud_scene.add(self.beer_icon_mesh)

        # Texto de interação com a jukebox
        jukebox_label_geo = RectangleGeometry(
            width=400, height=60,
            position=[400, 100], alignment=[0.5, 0]
        )
        text_texture = TextTexture(
            text="Pressiona E para interagir com a jukebox",
            system_font_name="Arial",
            font_size=32,
            font_color=(255, 255, 255),
            background_color=(0, 0, 0, 128),
            transparent=True
        )
        text_material = TextureMaterial(text_texture)

        bar_label_geo = RectangleGeometry(
            width=650, height=80,
            position=[750, 400], alignment=[0.5, 0]
        )
        text_texture2 = TextTexture(
            text="Pressiona ESPAÇO para pedir uma cerveja",
            system_font_name="Arial",
            font_size=32,
            font_color=(255, 255, 255),
            background_color=(0, 0, 0, 128),
            transparent=True
        )
        text_material2 = TextureMaterial(text_texture2)
        self.jukebox_prompt = Mesh(jukebox_label_geo, text_material)
        self.bar_prompt = Mesh(bar_label_geo, text_material2)


        # Create player's BEER components but don't add to scene yet
        BEER_MATERIAL = PhongMaterial(
            property_dict={"baseColor":[0, 0.7, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True,
            opacity=0.2
        )
        LIQUID_MATERIAL = self._get_cached_material(
            "TransparentMaterial",
            color=[0.3,0.3,0],
            opacity=0.5
        )
        
        # Create both bottle and liquid meshes for player's BEER
        self.BEER = Mesh(geometry=self.bottle_geo, material=BEER_MATERIAL)
        self.BEER_LIQUID = Mesh(geometry=self.liquid_geo, material=LIQUID_MATERIAL)  # Use the same liquid geometry as the shelf bottles
        # Don't add to scene yet since player starts without beer


        # Add a list to store spawned beers
        self.spawned_beers = []
        
        # Add a flag to track if we're currently animating a beer
        self.animating_beer = False
        self.beer_animation_time = 0
        self.beer_animation_duration = 1.0  # seconds

    def handle_menu_change(self, new_state, new_button_list, old_button_list):
        if self.menu_state == "settings" and new_state == "jukebox":
            old_button_list = self.settings_buttons
        elif self.menu_state == "sensitivity" and new_state == "jukebox":
            old_button_list = self.sensitivity_buttons
        elif self.menu_state == "brightness" and new_state == "jukebox":
            old_button_list = self.brightness_buttons
        self.menu_state = new_state
        for mesh, *_ in old_button_list:
            self.hudScene.remove(mesh)
        for mesh, tex_normal, tex_hover, action, position, width, height in new_button_list:
            self.hudScene.add(mesh)

    def handle_button_action(self, action):
        try:
            pygame.time.delay(100) # Para evitar double clicks
            if action == "start_game":
                self.show_menu = False
                pygame.mouse.set_visible(False)
            elif action == "open_settings":
                self.handle_menu_change("settings", self.settings_buttons, self.menu_buttons)
            elif action == "exit_game":
                pygame.quit()
                exit(0)
            elif action == "back":
                self.handle_menu_change("main", self.menu_buttons, self.settings_buttons)
            elif action == "back2":
                self.handle_menu_change("settings", self.settings_buttons, self.sensitivity_buttons)
            elif action == "camerasensitivity":
                self.handle_menu_change("sensitivity", self.sensitivity_buttons, self.settings_buttons)
            elif action == "slow":
                self.input.set_mouse_sensitivity(0.1)
                self.show_menu = False
            elif action == "normal":
                self.input.set_mouse_sensitivity(0.5)
                self.show_menu = False
            elif action == "fast":
                self.input.set_mouse_sensitivity(1.0)
                self.show_menu = False
            elif action == "Brightness":
                self.handle_menu_change("brightness", self.brightness_buttons, self.settings_buttons)
            elif action == "Dark":
                self.brightness = 1
                self.show_menu = False
            elif action == "Normal":
                self.brightness = 2
                self.show_menu = False
            elif action == "Bright":
                self.brightness = 3
                self.show_menu = False
            elif action == "back3":
                self.handle_menu_change("settings", self.settings_buttons, self.brightness_buttons)
            elif action == "resetsettings":
                self.input.set_mouse_sensitivity(0.5)
                self.brightness = 2
                self.show_menu = False
            elif action == "play_song1":
                pygame.mixer.music.load("sounds/banjo.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                self.song_playing = True
                self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                self.show_menu = False
            elif action == "play_song2":
                pygame.mixer.music.load("sounds/fiddle.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                self.song_playing = True
                self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                self.show_menu = False
            elif action == "play_song3":
                pygame.mixer.music.load("sounds/mandolin.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                self.song_playing = True
                self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                self.show_menu = False
            elif action == "play_song4":
                pygame.mixer.music.load("sounds/bateria.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                self.song_playing = True
                self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                self.show_menu = False
            elif action == "close_jukebox":
                self.jukebox_menu_active = False
                pygame.mixer.music.stop()
                self.song_playing = False
                self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                self.show_menu = False
        except Exception as e:
            print(f"Error handling button action '{action}': {e}")
            return

    def create_menu_button(self, base_name, position, action, button_list, add_to_scene=True, folder="images/buttons"):
        width = self.screen_size[0] * 0.325
        height = self.screen_size[1] * 0.1

        geo = RectangleGeometry(width=width, height=height, position=position, alignment=[0.5, 0.5])
        tex_normal = Texture(f"{folder}/{base_name}.png")
        tex_hover = Texture(f"{folder}/{base_name}_hover.png")
        mat = TextureMaterial(tex_normal)
        mesh = Mesh(geo, mat)

        if add_to_scene:
            self.hudScene.add(mesh)

        button_list.append((mesh, tex_normal, tex_hover, action, position, width, height))





    def update(self):
        
        
        # Check for P key press to play Song 1
        keys = pygame.key.get_pressed()
        if keys[pygame.K_p] and not self.song_playing:
            pygame.mixer.music.load("sounds/song1.mp3")
            pygame.mixer.music.play()
            self.song_playing = True

        # Update HarmonicaPlayer animation
        # Update animation time
        self.harmonica_animation_time = (self.time * self.harmonica_animation_speed) % self.harmonica_animation_duration
        
        # Calculate which phase of the animation we're in (0 to 1)
        phase = self.harmonica_animation_time / self.harmonica_animation_duration
        
        # Determine current state based on phase
        if phase < 0.25:  # Normal to Right
            t = phase / 0.25  # Normalize to 0-1
            current_angle = self.lerp(self.harmonica_states['normal'], self.harmonica_states['right'], t)
        elif phase < 0.5:  # Right to Normal
            t = (phase - 0.25) / 0.25
            current_angle = self.lerp(self.harmonica_states['right'], self.harmonica_states['normal'], t)
        elif phase < 0.75:  # Normal to Left
            t = (phase - 0.5) / 0.25
            current_angle = self.lerp(self.harmonica_states['normal'], self.harmonica_states['left'], t)
        else:  # Left to Normal
            t = (phase - 0.75) / 0.25
            current_angle = self.lerp(self.harmonica_states['left'], self.harmonica_states['normal'], t)
        
        # Reset rotations first
        self.HarmonicaPlayerHead.local_matrix = self.HarmonicaPlayerLegs.local_matrix
        self.HarmonicaPlayerBody.local_matrix = self.HarmonicaPlayerLegs.local_matrix
        self.harmonica.local_matrix = self.HarmonicaPlayer.local_matrix
        
        # Apply the interpolated angle
        self.HarmonicaPlayerHead.rotate_z(current_angle)
        self.HarmonicaPlayerBody.rotate_z(current_angle)
        self.harmonica.rotate_z(current_angle)

        # Update musical notes
        # Update existing notes
        for note in self.musical_notes:
            note['lifetime'] += self.delta_time
            
            # Reset note when it expires
            if note['lifetime'] > self.note_lifetime:
                # Choose a random instrument to reset to
                instruments = [
                    self.harmonica,
                    self.mandolin,
                    self.fiddle,
                    self.banjo
                ]
                reset_instrument = random.choice(instruments)
                instrument_pos = reset_instrument.global_position
                
                # Reset position to chosen instrument
                note['mesh'].set_position([instrument_pos[0], instrument_pos[1] + 0.5, instrument_pos[2]])
                
                # New random color
                color = random.choice(self.note_colors)
                note['mesh'].material.set_properties(property_dict={"baseColor": color})
                
                # New random velocity
                note['velocity'] = [random.uniform(-0.5, 0.5), self.note_rise_speed, random.uniform(-0.5, 0.5)]
                
                # Reset lifetime
                note['lifetime'] = 0.0
                continue
            
            # Update position
            current_pos = np.array(note['mesh'].global_position)
            new_pos = current_pos + np.array(note['velocity']) * self.delta_time
            note['mesh'].set_position(new_pos)
            
            # Add some rotation for visual effect
            note['mesh'].rotate_y(self.delta_time * 2)

        # Play harmonica as background music when no other music is playing
        if not pygame.mixer.music.get_busy() and not self.song_playing:
            pygame.mixer.music.load("sounds/harmonica.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely

        # Spawn new notes if we haven't reached max_notes
        self.note_spawn_timer += self.delta_time
        if self.note_spawn_timer >= self.note_spawn_interval and len(self.musical_notes) < self.max_notes:
            # Choose a random instrument to spawn from
            instruments = [
                self.harmonica,
                self.mandolin,
                self.fiddle,
                self.banjo
            ]
            spawn_instrument = random.choice(instruments)
            
            # Create new note
            musical_geo = RectangleGeometry(0.1, 0.1)
            musical_sprite = Texture("images/musical.png")
            musical_material = SpriteMaterial(
                musical_sprite,
                {
                    "billboard": True,
                    "tileCount": [1, 1],
                    "tileNumber": 0
                }
            )
            note_mesh = Mesh(musical_geo, musical_material)
            self.dynamic_scene.add(note_mesh)

            # Set initial position at the chosen instrument
            instrument_pos = spawn_instrument.global_position
            note_mesh.set_position([instrument_pos[0], instrument_pos[1] + 0.5, instrument_pos[2]+0.3])
            
            # Randomize color
            color = random.choice(self.note_colors)
            note_mesh.material.set_properties(property_dict={"baseColor": color})
            
            # Add to active notes
            self.musical_notes.append({
                'mesh': note_mesh,
                'lifetime': 0.0,
                'velocity': [random.uniform(-0.5, 0.5), self.note_rise_speed, random.uniform(-0.5, 0.5)]
            })
            
            self.note_spawn_timer = 0.0

        # Spawn drunkness-based notes
        if self.DRUNKNESS > 0:
            # Scale spawn rate with drunkness (0-1 range)
            drunk_spawn_chance = self.DRUNKNESS * self.delta_time * 2.0  # 2.0 is the base spawn rate multiplier
            
            if random.random() < drunk_spawn_chance and len(self.musical_notes) < self.max_notes:
                # Create new note
                musical_geo = RectangleGeometry(0.1, 0.1)
                musical_sprite = Texture("images/musical.png")
                musical_material = SpriteMaterial(
                    musical_sprite,
                    {
                        "billboard": True,
                        "tileCount": [1, 1],
                        "tileNumber": 0
                    }
                )
                note_mesh = Mesh(musical_geo, musical_material)
                self.dynamic_scene.add(note_mesh)

                # Random position within bar bounds
                x = random.uniform(self.bar_bounds['x_min'], self.bar_bounds['x_max'])
                z = random.uniform(self.bar_bounds['z_min'], self.bar_bounds['z_max'])
                y = self.bar_bounds['y_min']  # Start from floor level
                
                note_mesh.set_position([x, y, z])
                
                # Randomize color
                color = random.choice(self.note_colors)
                note_mesh.material.set_properties(property_dict={"baseColor": color})
                
                # Add to active notes with upward velocity
                self.musical_notes.append({
                    'mesh': note_mesh,
                    'lifetime': 0.0,
                    'velocity': [random.uniform(-0.3, 0.3), self.note_rise_speed * 0.8, random.uniform(-0.3, 0.3)]
                })

        # Remove expired notes
        notes_to_remove = []
        for note in self.musical_notes:
            note['lifetime'] += self.delta_time
            
            # Remove notes that have expired
            if note['lifetime'] > self.note_lifetime:
                if note['mesh'] in self.dynamic_scene._children_list:
                    self.dynamic_scene.remove(note['mesh'])
                self.note_pool.append(note['mesh'])  # Return to pool
                notes_to_remove.append(note)
                continue
            
            # Update position
            current_pos = np.array(note['mesh'].global_position)
            new_pos = current_pos + np.array(note['velocity']) * self.delta_time
            note['mesh'].set_position(new_pos)
            
            # Add some rotation for visual effect
            note['mesh'].rotate_y(self.delta_time * 2)

        # Remove expired notes
        for note in notes_to_remove:
            self.musical_notes.remove(note)

        # ---------------------- INSTRUMENT ANIMATION -------------------
        # Start when music is playing and it's a jukebox song
        if pygame.mixer.music.get_busy() and self.song_playing:
            if not self.instrument_animation_active:
                self.instrument_animation_active = True
                self.instrument_animation_start_time = self.time

            # acceleration progress (0→1) over self.instrument_acceleration_time
            accel_progress = min(
                1.0,
                (self.time - self.instrument_animation_start_time) / self.instrument_acceleration_time
            )

            for inst in self.instruments:
                # mix two angles for a more "organic" path
                ang1 = self.time * self.instrument_animation_speed + inst['phase_offset']
                ang2 = self.time * self.instrument_animation_speed * 0.5 + inst['phase_offset']*2

                # combined circular in X/Z
                x = (math.cos(ang1) + math.sin(ang2)) * self.instrument_path_radius * 0.5
                z = (math.sin(ang1) + math.cos(ang2)) * self.instrument_path_radius * 0.5

                # vertical "float"
                y = self.instrument_float_height * math.sin(self.time*2 + inst['phase_offset'])

                # apply bar boundaries
                x = max(self.bar_bounds['x_min'], min(self.bar_bounds['x_max'], x))
                z = max(self.bar_bounds['z_min'], min(self.bar_bounds['z_max'], z))
                y = max(self.bar_bounds['y_min'], min(self.bar_bounds['y_max'],
                                                     y + self.instrument_vertical_offset))

                # interpolation for smooth acceleration
                base = np.array(inst['base_position'])
                target = np.array([x, y, z])
                pos = base + (target - base)*accel_progress
                inst['object'].set_position(pos)

                # smooth rotations
                rot_speed = self.instrument_rotation_speed * accel_progress
                inst['object'].rotate_y(rot_speed * self.delta_time)
                inst['object'].rotate_x(math.sin(self.time + inst['phase_offset'])
                                      * 0.1 * accel_progress)

        else:
            # Music stopped → return instruments to base pose
            if self.instrument_animation_active:
                self.instrument_animation_active = False
                for inst in self.instruments:
                    inst['object'].set_position(inst['base_position'])
                    inst['object'].rotate_x(0)
                    inst['object'].rotate_y(0)
                    inst['object'].rotate_z(0)
        # --------------------------------------------------------------------

        camera_position = self.camera.local_position
        self._cull_lights(camera_position)
        self._update_light_uniforms()
        
        # Get the actual player position from the rig
        player_position = self.rig.local_position
        
        # Check distance to jukebox using player position
        distance_to_jukebox = np.linalg.norm(np.array(player_position) - np.array(self.jukebox_position))
        distance_to_bar = np.linalg.norm(np.array(player_position) - np.array(self.bar_position))
        
        # Handle jukebox interaction
        self.show_interaction_prompt = distance_to_jukebox < self.jukebox_interaction_distance
        self.show_interaction_prompt2 = distance_to_bar < self.bar_interaction_distance
        
        # Mostrar ou esconder a mensagem de interação dinamicamente
        if self.show_interaction_prompt:
            if self.jukebox_prompt not in self.context_hud._children_list:
                self.context_hud.add(self.jukebox_prompt)
                
            # Handle jukebox menu activation
            if self.input.is_key_pressed("e") and not self.jukebox_menu_active and not self.show_menu:
                pygame.mouse.set_visible(True)
                self.show_menu = True
                if self.menu_state != "jukebox":
                    self.handle_menu_change("jukebox", self.jukebox_buttons, self.menu_buttons)

        else:
            if self.jukebox_prompt in self.context_hud._children_list:
                self.context_hud.remove(self.jukebox_prompt)
            self.show_interaction_prompt = False

        if self.show_interaction_prompt2:
            if self.bar_prompt not in self.context_hud._children_list:
                self.context_hud.add(self.bar_prompt)
        else:
            if self.bar_prompt in self.context_hud._children_list:
                self.context_hud.remove(self.bar_prompt)
            self.show_interaction_prompt2 = False
        # Só atualiza a câmera se nenhum menu estiver aberto
        if not self.jukebox_menu_active and not self.show_menu:
            self.rig.update(self.input, self.delta_time)

        self.head.look_at(self.camera.global_position)
        self.head.rotate_y(math.radians(180))


        # Update dynamic objects
        speed = 0.5
        x = math.cos(self.time * speed)/2
        y = math.sin(self.time * speed)/2
        dir = [x, y, 1] 
        
        current_camera_position = np.array(self.camera.global_position)
        movement = np.linalg.norm(current_camera_position - self.last_camera_position)
        if movement > self.movement_threshold:
            if not self.isWalking:
                self.stepping_channel.play(Sound=self.steps_sound, loops=-1)
                self.isWalking = True
        else:
            if self.isWalking:
                if self.stepping_channel:
                    self.stepping_channel.stop()
                self.isWalking = False
        self.last_camera_position = current_camera_position

        # Check for space key press to remove bottle
        if self.input.is_key_pressed("space"):
            if not self.space_was_pressed and not self.hasBeer and not self.bottle_thrown:
                self.remove_bottle()
                self.space_was_pressed = True
        else:
            self.space_was_pressed = False

        # Get camera direction for both beer holding and throwing
        view_matrix = self.camera.view_matrix
        camera_direction = -view_matrix[2][:3]
        camera_direction = camera_direction / np.linalg.norm(camera_direction)
        beer_offset = 0.7
        base_position = np.array(self.camera.global_position) + (camera_direction * beer_offset) + np.array([0,-0.7,0])
        raised_position = base_position + np.array([0, 0.4, 0])

        # Handle beer drinking and holding
        if self.hasBeer:
            # Handle tilt input and animation
            if self.input.is_mouse_button_pressed(2) and self.BEER_LEFT > 0:
                self.beer_animation_progress = min(1.0, self.beer_animation_progress + self.beer_animation_speed * self.delta_time)
                if not self.gulping_sound_playing and self.beer_animation_progress > 0.2:
                    self.gulping_channel.play(Sound=self.gulp_sound, loops=-1)
                    self.gulping_sound_playing = True
            else:
                self.beer_animation_progress = max(0.0, self.beer_animation_progress - self.beer_animation_speed * self.delta_time)
                if self.gulping_channel is not None:
                    self.gulping_channel.stop()
                    self.gulping_sound_playing = False

            # Update beer amount and drunkenness
            if self.input.is_mouse_button_pressed(2) and self.BEER_LEFT > 0:
                self.BEER_LEFT = max(0, self.BEER_LEFT - self.delta_time * 10)
            elif self.BEER_LEFT <= 0:
                if self.gulping_channel is not None:
                    self.gulping_channel.stop()
                    self.gulping_sound_playing = False

                if self.BEER_LIQUID in self.dynamic_scene._children_list:
                    self.dynamic_scene.remove(self.BEER_LIQUID)
                    self.burp_channel.play(self.burp_sound)
                    self.beers_drank += 1
                self.bottle_can_throw = True
                if self.beers_drank < 12:
                    self.DRUNKNESS = self.beers_drank
                    self.beer_icon_mesh.material = TextureMaterial(self.beer_icon_textures[self.beers_drank])
                

            # Handle bottle throwing when empty
            if self.bottle_can_throw and self.input.is_mouse_button_pressed(0):
                throw_strength = 15.0
                self.bottle_velocity = camera_direction * throw_strength
                self.bottle_thrown = True
                self.bottle_can_throw = False
                self.hasBeer = False
                

            # Normal beer holding behavior
            if not self.bottle_thrown:
                current_position = base_position + (raised_position - base_position) * self.beer_animation_progress
                self.BEER.set_position(current_position)
                self.BEER_LIQUID.set_position(current_position)  # Update liquid position
                
                tilt_direction = np.array(self.camera.global_position) - np.array(self.BEER.global_position)
                tilt_direction[1] -= 2.5 * self.beer_animation_progress
                tilt_direction = tilt_direction / np.linalg.norm(tilt_direction)
                self.BEER.set_direction(tilt_direction)
                self.BEER_LIQUID.set_direction(tilt_direction)  # Update liquid direction

        # Handle bottle throwing first (independent of hasBeer)
        if self.bottle_thrown:
            # Update bottle position based on physics
            current_pos = np.array(self.BEER.global_position)
            self.bottle_velocity[1] += self.bottle_gravity * self.delta_time
            new_pos = current_pos + self.bottle_velocity * self.delta_time
            
            # Check for collision with objects using CollisionManager
            bottle_radius = 0.1  # Small radius for bottle collision
            collision_detected = self.bottle_collision_manager.check_collision(new_pos, bottle_radius)
            
            # Check for collision with floor (y = 0) OR with objects
            if new_pos[1] <= 0 or collision_detected:
                # Play bottle break sound when it hits something
                self.bottle_break_channel.play(self.bottle_break_sound)
                
                # Create glass fragments at impact position
                impact_position = [new_pos[0], max(0, new_pos[1]), new_pos[2]]  # Ensure Y is not negative
                self.create_glass_fragments(impact_position, self.bottle_velocity)
                
                self.dynamic_scene.remove(self.BEER)
                if self.BEER_LIQUID in self.dynamic_scene._children_list:  # Also remove liquid if it exists
                    self.dynamic_scene.remove(self.BEER_LIQUID)
                self.bottle_thrown = False
                self.bottle_velocity = np.array([0.0, 0.0, 0.0])
            else:
                self.BEER.set_position(new_pos)
                if self.BEER_LIQUID in self.dynamic_scene._children_list:  # Update liquid position if it exists
                    self.BEER_LIQUID.set_position(new_pos)
                self.BEER.rotate_x(self.delta_time * 5)
                self.BEER.rotate_z(self.delta_time * 3)
                if self.BEER_LIQUID in self.dynamic_scene._children_list:  # Update liquid rotation if it exists
                    self.BEER_LIQUID.rotate_x(self.delta_time * 5)
                    self.BEER_LIQUID.rotate_z(self.delta_time * 3)

        self.brightness_effect.uniform_dict["originalStrength"].data = self.brightness
        camera_position = self.camera.local_position
        self._cull_lights(camera_position)
        self._update_light_uniforms()

        if self.input.is_key_down("escape"):
            if self.show_menu:
                if self.menu_state == "main":
                    self.show_menu = not self.show_menu
                    pygame.mouse.set_visible(False)
                elif self.menu_state == "settings":
                    self.handle_menu_change("main", self.menu_buttons, self.settings_buttons)
                elif self.menu_state == "sensitivity":
                    self.handle_menu_change("settings", self.settings_buttons, self.sensitivity_buttons)
                elif self.menu_state == "brightness":
                    self.handle_menu_change("settings", self.settings_buttons, self.brightness_buttons)
                elif self.menu_state == "jukebox":
                    self.handle_menu_change("main", self.menu_buttons, self.jukebox_buttons)
                    self.show_menu = not self.show_menu
                    pygame.mouse.set_visible(False)
            if not self.show_menu:
                self.show_menu = True
                pygame.mouse.set_visible(True)


        #Menu
        if self.show_menu:
            mx, my = pygame.mouse.get_pos()
            my = self.screen_size[1] - my

            if self.menu_state == "main":
                button_list = self.menu_buttons
            elif self.menu_state == "settings":
                button_list = self.settings_buttons
            elif self.menu_state == "sensitivity":
                button_list = self.sensitivity_buttons
            elif self.menu_state == "brightness":
                button_list = self.brightness_buttons
            elif self.menu_state == "jukebox":
                button_list = self.jukebox_buttons
            else:
                button_list = []

            for mesh, tex_normal, tex_hover, action, position, width, height in button_list:
                center_x, center_y = position

                left = center_x - width // 2
                right = center_x + width // 2
                top = center_y - height // 2
                bottom = center_y + height // 2

                hovered = left <= mx <= right and top <= my <= bottom

                if hovered:
                    mesh.material = TextureMaterial(tex_hover)
                    if self.input.is_mouse_button_pressed(0):
                        self.handle_button_action(action)
                else:
                    mesh.material = TextureMaterial(tex_normal)

            frame_index = int(self.time * self.bg_frame_rate) % self.num_bg_frames
            self.menu_bg_mesh.material = TextureMaterial(self.bg_textures[frame_index])
            self.renderer.render(self.hudScene, self.hudCamera, clear_color=False)
        else:
            pygame.mouse.set_visible(False)
        


        # Update dynamic objects
        speed = 0.5
        x = math.cos(self.time * speed)/2
        y = math.sin(self.time * speed)/2
        dir = [x, y, 1] 
        
        # Only update active lights
        for light in self._active_lights:
            if isinstance(light, SpotLight):
                light.direction = dir
                self.spotlight.set_direction(dir)
                self.light.local_matrix = self.spotlight.local_matrix
                
        self.vinyl.rotate_y(0.01337)
        self.mirrorball.rotate_y(0.02)

        # === Luzes reactivas à música ===
        if pygame.mixer.music.get_busy() and self.song_playing:  # Only react to jukebox songs
            self.song_color_timer += self.delta_time * 2.0  # controla a velocidade da troca
            color = self.get_rainbow_color(self.song_color_timer)
            
            # Atualiza os lightcones com efeito de apagar/acender
            for i, lightcone in enumerate(self.lightcones):
                # Usa o tempo e o índice do lightcone para criar um padrão de apagar/acender
                should_light = (math.sin(self.time * 2 + i * math.pi/4) + 1) / 2 > 0.5
                if should_light:
                    # Quando aceso, usa uma cor do arco-íris com offset baseado no índice
                    lightcone_color = self.get_rainbow_color(self.song_color_timer + i * 0.5)
                    lightcone.material.set_properties(property_dict={"baseColor": lightcone_color, "opacity": 0.2})
                else:
                    # Quando apagado, fica transparente
                    lightcone.material.set_properties(property_dict={"baseColor": [1,1,1], "opacity": 0.0})
            
            # Aplica a cor às outras luzes (neon, dancefloor, etc.)
            self.neon.material.set_properties(property_dict={"baseColor": color})
            self.dancefloor_color1.material.set_properties(property_dict={"baseColor": color})
            self.dancefloor_color2.material.set_properties(property_dict={"baseColor": [color[2], color[0], color[1]]})
            
            # Atualiza as luzes dinâmicas
            dynamic_color = self.get_rainbow_color(self.song_color_timer + 1.0)
            for light in self.dynamic_lights:
                light._color = dynamic_color
        else:
            self.song_color_timer = 0.0
            # Mantém os lightcones piscando em branco quando não há música
            for i, lightcone in enumerate(self.lightcones):
                should_light = (math.sin(self.time * 2 + i * math.pi/4) + 1) / 2 > 0.5
                if should_light:
                    lightcone.material.set_properties(property_dict={"baseColor": [1,1,1], "opacity": 0.2})
                else:
                    lightcone.material.set_properties(property_dict={"baseColor": [1,1,1], "opacity": 0.0})

        # Update neon color using set_properties instead of creating new material
        rainbow_color = self.get_rainbow_color(self.time)
        self.neon.material.set_properties(property_dict={"baseColor": rainbow_color})
        self.sign.material.set_properties(property_dict={"baseColor": rainbow_color})
        self.sign2.material.set_properties(property_dict={"baseColor": rainbow_color})
        
        #NeonSign Update
        blink_interval = 1.0  # seconds
        blinking = int(self.time // blink_interval) % 2 == 0
        if blinking:
            # Blue ON, Yellow OFF
            next_glow = self.blueSign
            next_color = self.dancefloor_color1
            self.dancefloor_color1.material.set_properties(property_dict={"baseColor": [0.2,0.2,1]})
            self.dancefloor_color2.material.set_properties(property_dict={"baseColor": [0.1,0.1,0.1]})
            self.blueSign.material.set_properties(property_dict={"baseColor": [0.2,0.2,1]})
            self.yellowSign.material.set_properties(property_dict={"baseColor": [0,0,0]})
            self.jukeboxsign.material.set_properties(property_dict={"baseColor": [1,0.1,0.1]})
        else:
            # Yellow ON, Blue OFF
            next_glow = self.yellowSign
            next_color = self.dancefloor_color2
            self.blueSign.material.set_properties(property_dict={"baseColor": [0,0,0]})
            self.yellowSign.material.set_properties(property_dict={"baseColor": [0.8,0.8,1]})
            self.dancefloor_color1.material.set_properties(property_dict={"baseColor": [0.1,0.1,0.2]})
            self.dancefloor_color2.material.set_properties(property_dict={"baseColor": [0.8,0.8,0.8]})
            self.jukeboxsign.material.set_properties(property_dict={"baseColor": [0.1,0,0]})

        # Reset glow scene and add the correct glowing mesh
        self.glow_scene.remove(self.current_glow)
        self.glow_scene.remove(self.current_color)
        self.glow_scene.add(next_glow)
        self.glow_scene.add(next_color)
        self.current_glow = next_glow
        self.current_color = next_color

        #Sonic Update
        tile_number = math.floor(self.time * self.tiles_per_second)
        self.sprite.material.uniform_dict["tileNumber"].data = tile_number

        self.rig.update(self.input, self.delta_time)

        self.glow_pass.render()
        self.combo_pass.render()
        d = self.DRUNKNESS

        if d > 0:

            self.pixelate.uniform_dict["pixelSize"].data = 0.01 + int(d / 10)
            self.pixelate.uniform_dict["resolution"].data = [self.screen_size[0], self.screen_size[1]]

            self.color_reduce.uniform_dict["levels"].data = 256 if d < 10 else 64


            blur_amount = 0 if d < 11 else 5 + (d - 11) * 2
            self.blur_h.uniform_dict["blurRadius"].data = blur_amount
            self.blur_v.uniform_dict["blurRadius"].data = blur_amount
            self.drunk_effect.update_drunk_level(min(self.DRUNKNESS / 12.0, 1.0))
            self.drunk_effect.update_time(self.time)

        self.renderer.render(self.beer_hud_scene, self.beer_hud_camera, clear_color=False)

        # Update beer animations
        if self.animating_beer and self.spawned_beers:
            # Get the current position for the player's BEER
            view_matrix = self.camera.view_matrix
            camera_direction = -view_matrix[2][:3]
            camera_direction = camera_direction / np.linalg.norm(camera_direction)
            beer_offset = 0.7
            target_position = np.array(self.camera.global_position) + (camera_direction * beer_offset) + np.array([0,-0.7,0])
            
            # Update each spawned beer
            beers_to_remove = []
            for beer_data in self.spawned_beers:
                beer_data['animation_time'] += self.delta_time
                progress = min(1.0, beer_data['animation_time'] / self.beer_animation_duration)
                
                # Use smooth easing function
                eased_progress = progress * (2 - progress)  # Quadratic ease-out
                
                # Interpolate position
                current_position = beer_data['start_position'] + (target_position - beer_data['start_position']) * eased_progress
                beer_data['bottle'].set_position(current_position)
                beer_data['liquid'].set_position(current_position)  # Animate liquid position
                
                # If animation is complete
                if progress >= 1.0:
                    if beer_data.get('is_player_beer', False):
                        # This is the player's beer, make it the active BEER
                        self.BEER = beer_data['bottle']  # Use the animated bottle
                        self.BEER_LIQUID = beer_data['liquid']  # Use the animated liquid
                        self.hasBeer = True
                        self.BEER_LEFT = MAX_BEER_AMOUNT_PER_BOTTLE
                    else:
                        # Just remove other beers
                        self.dynamic_scene.remove(beer_data['bottle'])
                        self.dynamic_scene.remove(beer_data['liquid'])
                    beers_to_remove.append(beer_data)
            
            # Remove completed animations
            for beer_data in beers_to_remove:
                self.spawned_beers.remove(beer_data)
            
            # Update animation state
            self.animating_beer = len(self.spawned_beers) > 0

        # Update glass fragments physics
        self.update_glass_fragments()

        self.glow_pass.render()
        
        self.renderer.render(self.context_hud, self.context_camera, clear_color=False)

        # Renderiza HUD do menu principal ou jukebox consoante o estado
        if self.show_menu:
            self.renderer.render(self.hudScene, self.hudCamera, clear_color=False)

        # Update flying chairs when drunkness is high
        if self.DRUNKNESS > 6:
            if not self.chair_animation_active:
                self.chair_animation_active = True
                self.chair_animation_start_time = self.time
                
                # Create flying chairs if they don't exist
                if not self.flying_chairs:
                    # Choose 2 random chairs to fly
                    flying_positions = random.sample(self.chair_positions, 2)
                    for chair_data in flying_positions:
                        # Create cushion
                        cushion = Mesh(
                            geometry=self.cushion_geo,
                            material=self.cushion_material
                        )
                        # Create base
                        base = Mesh(
                            geometry=self.chairbase_geo,
                            material=self.chairbase_material
                        )
                        # Set initial positions
                        cushion.set_position(chair_data['position'])
                        base.set_position(chair_data['position'])
                        # Store original position for smooth transition
                        self.flying_chairs.append({
                            'cushion': cushion,
                            'base': base,
                            'original_position': chair_data['position'],
                            'target_position': chair_data['position'],
                            'angle': 0,
                            'vertical_offset': 0,
                            'transition_progress': 0  # Add transition progress
                        })
                        self.scene.add(cushion)
                        self.scene.add(base)
            
            # Update flying chairs animation
            for i, chair in enumerate(self.flying_chairs):
                # Calculate time since animation started
                elapsed_time = self.time - self.chair_animation_start_time
                
                # Add phase offset based on chair index to keep them apart
                phase_offset = i * math.pi  # 180 degrees offset between chairs
                
                # Smooth transition from original position to flying animation
                if chair['transition_progress'] < 1:
                    chair['transition_progress'] = min(1, elapsed_time / self.chair_acceleration_time)
                    # Calculate target position with minimum height
                    target_x = math.cos(chair['angle'] + phase_offset) * self.chair_path_radius
                    target_z = math.sin(chair['angle'] + phase_offset) * self.chair_path_radius
                    # Use absolute value of sin to ensure positive height variation
                    target_y = self.chair_vertical_offset + (abs(math.sin(elapsed_time * self.chair_animation_speed + phase_offset)) * self.chair_float_height)
                    
                    # Interpolate position, but ensure minimum height during transition
                    current_pos = self.lerp(
                        chair['original_position'],
                        [target_x, target_y, target_z],
                        chair['transition_progress']
                    )
                    # Ensure minimum height during transition
                    current_pos[1] = max(current_pos[1], self.chair_vertical_offset * chair['transition_progress'])
                    
                    chair['cushion'].set_position(current_pos)
                    chair['base'].set_position(current_pos)
                
                # Update angle and vertical offset with more variation
                chair['angle'] += self.chair_rotation_speed * self.delta_time
                # Add more variation to vertical movement, but keep it positive
                vertical_variation = abs(math.sin(elapsed_time * self.chair_animation_speed * 0.5)) * 0.5
                chair['vertical_offset'] = (
                    abs(math.sin(elapsed_time * self.chair_animation_speed + phase_offset)) * self.chair_float_height +
                    vertical_variation
                )
                
                # Calculate new position with phase offset
                x = math.cos(chair['angle'] + phase_offset) * self.chair_path_radius
                z = math.sin(chair['angle'] + phase_offset) * self.chair_path_radius
                y = chair['vertical_offset'] + self.chair_vertical_offset
                
                # Update target position
                chair['target_position'] = [x, y, z]
                
                # Only update position if transition is complete
                if chair['transition_progress'] >= 1:
                    chair['cushion'].set_position(chair['target_position'])
                    chair['base'].set_position(chair['target_position'])
                
                # Apply rotation with slight tilt
                chair['cushion'].rotate_y(self.chair_rotation_speed * self.delta_time)
                chair['base'].rotate_y(self.chair_rotation_speed * self.delta_time)
                # Add slight tilt based on movement
                tilt = math.sin(elapsed_time * self.chair_animation_speed + phase_offset) * 0.1
                chair['cushion'].rotate_x(tilt)
                chair['base'].rotate_x(tilt)
        else:
            # Reset chairs when drunkness drops
            if self.chair_animation_active:
                self.chair_animation_active = False
                # Remove flying chairs from scene
                for chair in self.flying_chairs:
                    if chair['cushion'] in self.dynamic_scene._children_list:
                        self.dynamic_scene.remove(chair['cushion'])
                    if chair['base'] in self.dynamic_scene._children_list:
                        self.dynamic_scene.remove(chair['base'])
                self.flying_chairs.clear()

    def close_all_menus(self):
        self.show_menu = False
        self.jukebox_menu_active = False

        for button_list in [
            self.menu_buttons,
            self.settings_buttons,
            self.sensitivity_buttons,
            self.brightness_buttons,
            self.jukebox_buttons,
        ]:
            for mesh, *_ in button_list:
                if mesh in self.hudScene._children_list:
                    self.hudScene.remove(mesh)
        self.jukebox_buttons.clear()

        # Remove o fundo do menu se estiver presente
        if self.menu_bg_mesh in self.hudScene._children_list:
            self.hudScene.remove(self.menu_bg_mesh)
        if hasattr(self, 'jukebox_bg_mesh') and self.jukebox_bg_mesh in self.hudScene._children_list:
            self.hudScene.remove(self.jukebox_bg_mesh)


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

    def remove_bottle(self):
        """Remove one bottle instance if there are bottles remaining and player is near barman/shelf"""
        # Get player position and direction
        player_position = np.array(self.camera.global_position)
        view_matrix = self.camera.view_matrix
        player_direction = -view_matrix[2][:3]
        player_direction = player_direction / np.linalg.norm(player_direction)

        # Define positions for barman and shelf
        barman_position = np.array([-11, 1.6, 13])  # Position of barman's head
        shelf_position = np.array([-11.1, 0, 14.3])  # Position of shelf

        # Calculate distances
        distance_to_barman = np.linalg.norm(player_position - barman_position)
        distance_to_shelf = np.linalg.norm(player_position - shelf_position)

        # Calculate directions to barman and shelf
        direction_to_barman = barman_position - player_position
        direction_to_barman = direction_to_barman / np.linalg.norm(direction_to_barman)
        direction_to_shelf = shelf_position - player_position
        direction_to_shelf = direction_to_shelf / np.linalg.norm(direction_to_shelf)

        # Calculate dot products to check if player is looking towards barman or shelf
        dot_barman = np.dot(player_direction, direction_to_barman)
        dot_shelf = np.dot(player_direction, direction_to_shelf)

        # Maximum distance to interact (3 units)
        MAX_INTERACTION_DISTANCE = 3.0
        # Minimum dot product to consider "looking at" (cosine of 45 degrees)
        MIN_LOOK_DOT = 0.7071  # cos(45 degrees)

        # Check if player is close enough and looking in the right direction
        is_near_barman = distance_to_barman < MAX_INTERACTION_DISTANCE and dot_barman > MIN_LOOK_DOT
        is_near_shelf = distance_to_shelf < MAX_INTERACTION_DISTANCE and dot_shelf > MIN_LOOK_DOT

        if not (is_near_barman or is_near_shelf):
            return  # Exit if player is not in position to take beer

        if self.remaining_bottles > 0 and not self.hasBeer:
            # Store the position of the bottle we're about to remove
            removed_position = self.bottle_factory.positions[-1]
            
            # Remove the last position from all factories
            self.bottle_factory.positions.pop()
            self.liquid_factory.positions.pop()
            self.cork_factory.positions.pop()
            
            # Remove the old meshes from the scene
            self.static_scene.remove(self.bottle_mesh)
            self.static_scene.remove(self.liquid_mesh)
            self.static_scene.remove(self.cork_mesh)
            
            # Create new meshes with the updated positions
            self.bottle_mesh = self.bottle_factory.build_mesh(self._create_instanced_mesh)
            self.liquid_mesh = self.liquid_factory.build_mesh(self._create_instanced_mesh)
            self.cork_mesh = self.cork_factory.build_mesh(self._create_instanced_mesh)
            
            # Add the new meshes to the scene
            self.static_scene.add(self.bottle_mesh)
            self.static_scene.add(self.liquid_mesh)
            self.static_scene.add(self.cork_mesh)
            
            # Update remaining bottles count
            self.remaining_bottles -= 1
            
            # Create both bottle and liquid meshes for animation
            new_beer = Mesh(
                geometry=self.bottle_geo,
                material=self._get_cached_material(
                    "PhongMaterial",
                    property_dict={"baseColor":[0, 0.7, 0]},
                    number_of_light_sources=self.light_number,
                    use_shadow=True,
                    opacity=0.2
                )
            )
            new_liquid = Mesh(
                geometry=self.liquid_geo,
                material=self._get_cached_material(
                    "TransparentMaterial",
                    color=[0.3,0.3,0],
                    opacity=0.5
                )
            )
            
            # Set initial positions
            new_beer.set_position(removed_position)
            new_liquid.set_position(removed_position)
            
            # Add both to scene
            self.dynamic_scene.add(new_beer)
            self.dynamic_scene.add(new_liquid)
            
            # Add both to spawned beers list
            self.spawned_beers.append({
                'bottle': new_beer,
                'liquid': new_liquid,
                'start_position': np.array(removed_position),
                'animation_time': 0,
                'is_player_beer': True
            })

            self.animating_beer = True

    def lerp(self, start, end, t):
        # Handle position lists (x,y,z coordinates)
        if isinstance(start, list) and isinstance(end, list):
            return [
                start[0] + (end[0] - start[0]) * t,
                start[1] + (end[1] - start[1]) * t,
                start[2] + (end[2] - start[2]) * t
            ]
        # Handle single values
        return start + (end - start) * t

    def create_glass_fragments(self, impact_position, impact_velocity):
        """Create glass fragments when bottle breaks"""
        import random
        
        # Number of fragments to create
        num_fragments = random.randint(8, 15)
        
        for i in range(num_fragments):
            # Create small box geometry for fragment
            fragment_size = random.uniform(0.02, 0.08)  # Random size between 0.02 and 0.08
            fragment_geo = BoxGeometry(
                width=fragment_size,
                height=fragment_size,
                depth=fragment_size
            )
            
            # Create glass material with transparency
            fragment_material = self._get_cached_material(
                "TransparentMaterial",
                color=[0.2, 0.8, 0.3],  # Green glass color to match beer bottles
                opacity=0.7
            )
            
            # Create mesh
            fragment_mesh = Mesh(fragment_geo, fragment_material)
            
            # Set initial position near impact point with some randomness
            offset_x = random.uniform(-0.3, 0.3)
            offset_z = random.uniform(-0.3, 0.3)
            offset_y = random.uniform(0.0, 0.2)
            
            fragment_position = np.array(impact_position) + np.array([offset_x, offset_y, offset_z])
            fragment_mesh.set_position(fragment_position)
            
            # Calculate initial velocity based on impact velocity and random spread
            spread_factor = 3.0
            velocity_x = impact_velocity[0] * random.uniform(0.2, 0.8) + random.uniform(-spread_factor, spread_factor)
            velocity_y = abs(impact_velocity[1]) * random.uniform(0.3, 1.0) + random.uniform(1.0, 3.0)  # Upward bounce
            velocity_z = impact_velocity[2] * random.uniform(0.2, 0.8) + random.uniform(-spread_factor, spread_factor)
            
            fragment_velocity = np.array([velocity_x, velocity_y, velocity_z])
            
            # Add random rotation velocity
            rotation_velocity = np.array([
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(-10, 10)
            ])
            
            # Store fragment data
            fragment_data = {
                'mesh': fragment_mesh,
                'velocity': fragment_velocity,
                'rotation_velocity': rotation_velocity,
                'lifetime': 0.0,
                'on_ground': False
            }
            
            # Add to scene and fragments list
            self.dynamic_scene.add(fragment_mesh)
            self.glass_fragments.append(fragment_data)

    def update_glass_fragments(self):
        """Update physics and lifetime of glass fragments"""
        fragments_to_remove = []
        
        for fragment in self.glass_fragments:
            fragment['lifetime'] += self.delta_time
            
            # Remove fragments after lifetime expires
            if fragment['lifetime'] > self.fragment_lifetime:
                self.dynamic_scene.remove(fragment['mesh'])
                fragments_to_remove.append(fragment)
                continue
            
            # Update physics if not settled on ground
            if not fragment['on_ground']:
                current_pos = np.array(fragment['mesh'].global_position)
                
                # Apply gravity
                fragment['velocity'][1] += self.fragment_gravity * self.delta_time
                
                # Update position
                new_pos = current_pos + fragment['velocity'] * self.delta_time
                
                # Check for ground collision
                if new_pos[1] <= 0.01:  # Small threshold above ground
                    new_pos[1] = 0.01
                    
                    # Bounce with damping
                    if fragment['velocity'][1] < -0.5:  # Only bounce if moving fast enough
                        fragment['velocity'][1] = -fragment['velocity'][1] * self.fragment_bounce_damping
                        fragment['velocity'][0] *= 0.8  # Reduce horizontal velocity
                        fragment['velocity'][2] *= 0.8
                    else:
                        # Stop bouncing and settle on ground
                        fragment['velocity'] = np.array([0, 0, 0])
                        fragment['rotation_velocity'] *= 0.1  # Slow down rotation
                        fragment['on_ground'] = True
                
                fragment['mesh'].set_position(new_pos)
                
                # Apply rotation
                fragment['mesh'].rotate_x(fragment['rotation_velocity'][0] * self.delta_time)
                fragment['mesh'].rotate_y(fragment['rotation_velocity'][1] * self.delta_time)
                fragment['mesh'].rotate_z(fragment['rotation_velocity'][2] * self.delta_time)
                
                # Damping for rotation when in air
                fragment['rotation_velocity'] *= 0.98
        
        # Remove expired fragments
        for fragment in fragments_to_remove:
            self.glass_fragments.remove(fragment)

    def _setup_bottle_collision_objects(self):
        """Setup collision objects for bottle physics"""
        # Add tables with appropriate height
        # Table positions (incluindo as novas mesas, descoordenadas em Z e afastadas da parede)
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5], [11, 0, -10], [11, 0, 0]]
        for i, pos in enumerate(table_positions):
            self.bottle_collision_manager.add_collision_object(pos, [2, 0, 2], height=1.5, name=f"Bottle_Table_{i+1}")
            
        # Add bar stand components
        self.bottle_collision_manager.add_collision_object([-8.7, 0, 12], [1, 0, 1], height=1, name="Bottle_Bar_Front")
        self.bottle_collision_manager.add_collision_object([-10.9, 0, 12], [4.4, 0, 1.5], height=1, name="Bottle_Bar_Back")  # Increased width and depth to cover full bar
        self.bottle_collision_manager.add_collision_object([-8.7, 0, 13.3], [1, 0, 1.8], height=1, name="Bottle_Bar_Side")
        
        # Add stage
        self.bottle_collision_manager.add_collision_object([0, 0, -13.5], [6, 0, 6], height=0.5, name="Bottle_Stage")
        
        # Add circular stage area where musicians are (round part) - more precise
        self.bottle_collision_manager.add_collision_object([0, 0, -10.5], [4.5, 0, 4.5], height=0.5, name="Bottle_Stage_Round")
        
        # Add stage wireframe structure (metal framework)
        # Left vertical support
        self.bottle_collision_manager.add_collision_object([-4, 0, -10], [0.75, 0, 0.75], height=6.0, name="Bottle_Stage_Support_Left")
        # Right vertical support  
        self.bottle_collision_manager.add_collision_object([4, 0, -10], [0.75, 0, 0.75], height=6.0, name="Bottle_Stage_Support_Right")

        # Add musician on stage collision (same size as barman)
        self.bottle_collision_manager.add_collision_object([0, 0, -10], [0.65, 0, 0.65], height=2.3, name="Bottle_Musician")
        
        # Add jukebox
        self.bottle_collision_manager.add_collision_object([0, 0, 14.5], [1.5, 0, 1.4], height=1.7, name="Bottle_Jukebox")
        
        # Add shelf
        self.bottle_collision_manager.add_collision_object([-11.1, 0, 14.8], [4, 0, 0.9], height=3.2, name="Bottle_Shelf")
        
        # Add barman collision
        self.bottle_collision_manager.add_collision_object([-11, 0, 13], [0.65, 0, 0.65], height=2.0, name="Bottle_Barman")
        
        # Add barstools
        for i in range(4):
            self.bottle_collision_manager.add_collision_object([-12.5 + i, 0, 11], [0.3, 0, 0.3], height=1.0, name=f"Bottle_Barstool_{i+1}")
            
        # Add TV table
        self.bottle_collision_manager.add_collision_object([14, 0, -14], [2, 0, 1.5], height=1.5, name="Bottle_TV_Table")
        
        # Add snooker table
        self.bottle_collision_manager.add_collision_object([-12, 0, -10], [2.5, 0, 3.8], height=0.9, name="Bottle_Snooker_Table")
        
        # Add seated clients collision
        self.bottle_collision_manager.add_collision_object([6.3, 0, 5], [0.6, 0, 0.6], height=1.74, name="Bottle_Client_1")
        self.bottle_collision_manager.add_collision_object([-5, 0, -6.3], [0.6, 0, 0.6], height=1.74, name="Bottle_Client_2")
        
    def _setup_pictures(self):
        """Coloca um quadro de cada imagem na parede lateral, alinhados, centralizados e com tamanho ajustado"""
        import numpy as np
        width = 2.5   # Tamanho da largura (ligeiramente diminuído)
        height = width * 1.5 # Altura calculada para proporção 2:3
        x = 14.9      # Parede lateral direita
        y = 2.5       # Altura de alinhamento na parede

        picture_files = [
            "images/quadro1.jpg",
            "images/quadro2.jpg",
            "images/quadro3.jpg",
            "images/quadro4.jpg",
            "images/quadro5.jpg",
            "images/quadro6.jpg",
            "images/quadro7.jpg",
        ]

        # Calcular a posição inicial para centralizar o bloco de quadros na parede lateral em Z
        total_width = len(picture_files) * width  # Largura total ocupada pelos quadros
        spacing = 0.3 # Espaço entre os quadros
        total_occupied_z = total_width + (len(picture_files) - 1) * spacing
        z_start = -total_occupied_z / 2.0 # Ponto de início para centralizar o bloco

        current_z = z_start

        # Criar e posicionar cada quadro individualmente
        for img in picture_files:
            geo = RectangleGeometry(width, height)
            tex = Texture(img)
            mat = TextureMaterial(tex)
            mesh = Mesh(geo, mat)
            mesh.set_position([x, y, current_z])
            mesh.rotate_y(math.radians(-90))
            self.static_scene.add(mesh)
            current_z += width + spacing # Atualizar a posição para o próximo quadro

def run_example(resolution=(1920, 1080)):
    Example(screen_size=resolution).run()

if __name__ == "__main__":
    run_example()
