import os

import numpy as np
import math
import pathlib
import sys
import copy

import pygame

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
        self.show_menu = True
        self.screen_size = screen_size
        self._material_cache = {}
        self._texture_cache = {}
        self._instance_data = {}
        self._active_lights = set()
        self._light_culling_distance = 20.0  # Maximum distance for light influence
        # Add these lines after other initializations
        self.beer_tilted = False  # Track if beer is currently tilting
        self.beer_can_tilt = True  # Track if beer can be tilted again
        self.tilt_towards_player = False
        self.current_angle = 0  # Track current rotation angle
        self.move_angle = 10
        self.beer_animation_progress = 0.0  # Track animation progress (0 to 1)
        self.beer_animation_speed = 3.0  # Speed of the animation
        
        self._light_culling_distance = 20.0
        self.brightness = 2

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
        
        # Camera setup
        self.camera = Camera(aspect_ratio=1920/1080)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([11.5, 1.5, 14])
        self.dynamic_scene.add(self.rig)  # Camera is dynamic
        
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
        direct_helper = DirectionalLightHelper(directional_light)
        directional_light.add(direct_helper)
        self.renderer.enable_shadows(directional_light)

        #PointLights
        # Table positions
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
        for i in range(4):
            pointlight = PointLight(color=[0.8,1,0.8],position=(table_positions[i] + np.array([0,1.45,0])))
            self.dynamic_scene.add(pointlight)
        
        #ceiling lights
        for i in range(5):
            ceilinglight = PointLight(color=[0.5,0.5,0.2],position=[-9 - i,3.5,12])
            self.dynamic_scene.add(ceilinglight)
            
        self.light_number = 12

        #BarInterior
        wall_geometry, floor_geometry, roof_geometry, door_geometry = BarGeometry(1, 1, 1, my_obj_reader('objects/interior.obj'))
        wall_material = self._get_cached_material(
            "LambertMaterial",
            texture=self._get_cached_texture("images/brick.jpg"),
            bump_texture=self._get_cached_texture("images/brick-normal-map.png"),
            property_dict={"bumpStrength": 1},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        floor_material = self._get_cached_material(
            "PhongMaterial",
            texture=self._get_cached_texture("images/rubber_tiles.jpg"),
            bump_texture=self._get_cached_texture("images/rubber_tiles_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        roof_material = LambertMaterial(
            texture=Texture("images/tiles.jpg"),
            bump_texture=Texture("images/tiles_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        door_material = LambertMaterial(
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
            property_dict={"baseColor":[1, 1, 0.7]},
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
        
        #BarStand
        barstand_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/barstand.obj')).get("barstand")
        barstand_material = PhongMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
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
        shelf_material = PhongMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        shelf = Mesh(geometry=shelf_geometry,material=shelf_material)
        shelf.rotate_y(math.radians(180))
        shelf.set_position([-11.1,0,14.3])
        self.static_scene.add(shelf)
        #bottles
        BeerGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/bottle.obj'))
        bottle_geo = BeerGeometries.get("outer")
        liquid_geo = BeerGeometries.get("inner")
        cork_geo = BeerGeometries.get("rolha")
        
        # Create bottle instances using factory
        bottle_factory = InstancedObjectFactory(
            bottle_geo,
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
                bottle_factory.add_instance([bottle_x, bottle_y, 14.5])
                bottle_x -= 0.5
            bottle_y += 0.7
            bottle_x = -9.5
            
        # Create bottle mesh
        bottle_mesh = bottle_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(bottle_mesh)
        
        # Create liquid instances
        liquid_factory = InstancedObjectFactory(
            liquid_geo,
            self._get_cached_material(
                "TransparentMaterial",
                color=[0.3,0.3,0],
                opacity=0.5
            )
        )
        liquid_factory.add_instances(bottle_factory.positions)
        liquid_mesh = liquid_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(liquid_mesh)
        
        # Create cork instances
        cork_factory = InstancedObjectFactory(
            cork_geo,
            self._get_cached_material(
                "LambertMaterial",
                property_dict={"baseColor":[0.8, 0.8, 0.0]},
                number_of_light_sources=self.light_number,
                use_shadow=True
            )
        )
        cork_factory.add_instances(bottle_factory.positions)
        cork_mesh = cork_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(cork_mesh)


        ################PLAYER BOTTLE#########################################################


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
        print(stagegeometries.keys())
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
            property_dict={"baseColor":[0.2, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        frame = Mesh(geometry=frame_geometry,material=frame_material)
        frame.local_matrix = stage.local_matrix
        self.static_scene.add(frame)
        cloth_material = PhongMaterial(
            property_dict={"baseColor":[0.5, 0, 0]},
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
            property_dict={"baseColor": [0.8,0.8,0.6]},
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
            property_dict={"baseColor":[0.2, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True,      
        )
        chairbase_material = PhongMaterial(
            property_dict={"baseColor":[0.05, 0.05, 0.05]},
            number_of_light_sources=self.light_number,
            use_shadow=True,      
        )
        # Create puff chair instances
        cushion_factory = InstancedObjectFactory(
            cushion_geo,
            cushion_material
        )
        chairbase_factory = InstancedObjectFactory(
            chairbase_geo,
            chairbase_material
        )
        
        # Add chair instances around tables
        for tx, ty, tz in table_positions:
            for i in range(4):
                angle_deg = i * 90
                angle_rad = math.radians(angle_deg)
                dx = math.sin(angle_rad) * 1.5
                dz = math.cos(angle_rad) * 1.5
                cushion_factory.add_instance(
                    [tx + dx, 0, tz + dz],
                    [0, angle_rad + math.pi, 0]
                )
                chairbase_factory.add_instance(
                    [tx + dx, 0, tz + dz],
                    [0, angle_rad + math.pi, 0]
                )
                
        # Create chair meshes
        cushion_mesh = cushion_factory.build_mesh(self._create_instanced_mesh)
        chairbase_mesh = chairbase_factory.build_mesh(self._create_instanced_mesh)
        self.static_scene.add(cushion_mesh)
        self.static_scene.add(chairbase_mesh)

        #RoundTables
        roundtable_geometry = CustomGeometry(1,1,1,my_obj_reader('objects/table.obj')).get("table")
        roundtable_material = LambertMaterial(
            property_dict={"baseColor":[0.3, 0.2, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        roundtable1 = Mesh(geometry=roundtable_geometry,material=roundtable_material)
        roundtable1.set_position(table_positions[0])
        roundtable2 = Mesh(geometry=roundtable_geometry,material=roundtable_material)
        roundtable2.set_position(table_positions[1])
        roundtable3 = Mesh(geometry=roundtable_geometry,material=roundtable_material)
        roundtable3.set_position(table_positions[2])
        roundtable4 = Mesh(geometry=roundtable_geometry,material=roundtable_material)
        roundtable4.set_position(table_positions[3])
        self.static_scene.add(roundtable1)
        self.static_scene.add(roundtable2)
        self.static_scene.add(roundtable3)
        self.static_scene.add(roundtable4)
        #lamps
        LampGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/lamp.obj'))
        base_geometry = LampGeometries.get("base")
        lamp_geometry= LampGeometries.get("lamp")
        lampshade_geometry= LampGeometries.get("lampshade")
        switch_geometry= LampGeometries.get("switch")
        base_material = PhongMaterial(
            property_dict={"baseColor":[1.0, 0.8, 0.0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        lamp_material = PhongMaterial(
            property_dict={"baseColor":[1.0, 1.0, 0.8]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        lampshade_material = PhongMaterial(
            property_dict={"baseColor":[0.3, 0.8, 0.4]},
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

        lightcone_geo = ConeGeometry(radius=0.1, height=5)
        lightcone_material = TransparentMaterial(color=[1,1,1], opacity=0.2)
        lightcone = Mesh(lightcone_geo,lightcone_material)
        lightcone.set_position([0,2,0])
        lightcone.set_direction([0,-1,1])
        self.static_scene.add(lightcone)
        #DanceFloor
        DancefloorGeometries = CustomGeometry(1,1,1,my_obj_reader('objects/dancefloor.obj'))
        color1_geo = DancefloorGeometries.get("color1")
        color2_geo = DancefloorGeometries.get("color2")
        color1_material = SurfaceMaterial(property_dict={"baseColor": [0.6,0,0.6]})
        color2_material = SurfaceMaterial(property_dict={"baseColor": [0.0, 0.6, 0.6]})
        self.dancefloor_color1 = Mesh(geometry=color1_geo,material=color1_material)
        self.dancefloor_color2 = Mesh(geometry=color2_geo,material=color2_material)
        self.dancefloor_color1.set_position([0,0.1,0])
        self.dancefloor_color2.set_position([0,0.1,0])
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


        #####glow scene#####
        
        
        #Jukebox Neon
        
        self.glow_scene.add(self.neon)
        
        #Neon Sign
        self.current_glow = self.blueSign
        self.glow_scene.add(self.current_glow)

        #exit sign
        self.glow_scene.add(exitsign)

        #spotlight
        self.glow_scene.add(self.light)

        #Globe
        glowMaterial = SurfaceMaterial(property_dict={"baseColor": [0.4, 0.4, 0.4]})
        glowingMirrorBall = Mesh(mirrorball_geometry,glowMaterial)
        glowingMirrorBall.local_matrix = self.mirrorball.local_matrix
        self.glow_scene.add(glowingMirrorBall)

        #Mesh
        sonicglow_material = SurfaceMaterial(property_dict={"baseColor": [0.2, 0.2, 0.2]})
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
        #self.combo_pass.add_effect(vignetteEffect())

        self.brightness_effect = additiveBlendEffect(
            blend_texture=glow_target.texture,
            original_strength=self.brightness,
            blend_strength=1.5
        )
        self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
        self.combo_pass.add_effect(self.brightness_effect)

        # HUD Scene
        self.show_menu = True
        self.menu_state = "main"
        pygame.mouse.set_visible(True)
        self.hudScene = Scene()
        self.hudCamera = Camera()
        #labelGeo1 = RectangleGeometry(width=600,height=80,position=[0,600],alignment=[0,1])
        #labelMat1 = TextureMaterial (Texture("images/Bar Simulator.png"))
        #label1 = Mesh(labelGeo1,labelMat1)
        #self.hudScene.add(label1)

        BEER_MATERIAL = PhongMaterial(
            property_dict={"baseColor":[0, 0.7, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True,
            opacity=0.2
        )
        self.BEER = Mesh(geometry=bottle_geo, material=BEER_MATERIAL)
        self.dynamic_scene.add(self.BEER)
        
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

        button_width = width * 0.325
        button_height = height * 0.1
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

        for label, base_name, position, action in settings_specs:
            self.create_menu_button(base_name, position, action, self.settings_buttons, add_to_scene=False)

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
        frame_folder = os.path.join(script_dir, "images", "gif_frames")
        frame_files = sorted([f for f in os.listdir(frame_folder) if f.endswith(".png")])

        for frame_file in frame_files:
            texture = Texture(os.path.join(frame_folder, frame_file))
            self.bg_textures.append(texture)

        self.num_bg_frames = len(self.bg_textures)
        self.bg_frame_rate = 8
        self.menu_bg_mesh = menu_bg_mesh

    def handle_menu_change(self, new_state, new_button_list, old_button_list):
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

            elif action == "resetsettings":
                print("Repor definições (placeholder)")
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
        # Update camera position for light culling
        camera_position = self.camera.local_position
        self._cull_lights(camera_position)
        self._update_light_uniforms()
        

        self.head.look_at(self.camera.global_position)
        self.head.rotate_y(math.radians(180))
        
        # Check for RMB click to toggle tilt
         # Tilt 90 degrees
        
        view_matrix = self.camera.view_matrix
        camera_direction = -view_matrix[2][:3]  # Get the Z axis and normalize
        camera_direction = camera_direction / np.linalg.norm(camera_direction)

        beer_offset = 0.7  # Distance in front of camera
        base_position = np.array(self.camera.global_position) + (camera_direction * beer_offset) + np.array([0,-0.7,0])
        raised_position = base_position + np.array([0, 0.4, 0])  # Raised position when tilted
        
        # Handle tilt input and animation
        if self.input.is_mouse_button_pressed(2):  # While button is held
            # Animate towards raised position
            self.beer_animation_progress = min(1.0, self.beer_animation_progress + self.beer_animation_speed * self.delta_time)
        else:  # When button is released
            # Animate back to base position
            self.beer_animation_progress = max(0.0, self.beer_animation_progress - self.beer_animation_speed * self.delta_time)
        
        # Interpolate between base and raised positions
        current_position = base_position + (raised_position - base_position) * self.beer_animation_progress
        self.BEER.set_position(current_position)
        
        # Calculate tilt direction based on camera position
        tilt_direction = np.array(self.camera.global_position) - np.array(self.BEER.global_position)
        # Add larger downward component to increase tilt, scaled by animation progress
        tilt_direction[1] -= 2.5 * self.beer_animation_progress
        tilt_direction = tilt_direction / np.linalg.norm(tilt_direction)
        self.BEER.set_direction(tilt_direction)
        self.brightness_effect.uniform_dict["originalStrength"].data = self.brightness
        camera_position = self.camera.local_position
        self._cull_lights(camera_position)
        self._update_light_uniforms()

        if self.input.is_key_down("escape"):
            if self.show_menu:
                if self.menu_state == "main":
                    self.show_menu = False
                    pygame.mouse.set_visible(False)
                elif self.menu_state == "settings":
                    self.handle_menu_change("main", self.menu_buttons, self.settings_buttons)
                elif self.menu_state == "sensitivity":
                    self.handle_menu_change("settings", self.settings_buttons, self.sensitivity_buttons)
                elif self.menu_state == "brightness":
                    self.handle_menu_change("settings", self.settings_buttons, self.brightness_buttons)
            else:
                self.show_menu = not self.show_menu
                pygame.mouse.set_visible(self.show_menu)

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
            return
        else:
            pygame.mouse.set_visible(False)

        print(self.show_menu)
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
        #self.renderer.render(self.hudScene, self.hudCamera, clear_color=False)

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



def run_example(resolution=(1920, 1080)):
    Example(screen_size=resolution).run()

if __name__ == "__main__":
    run_example()
