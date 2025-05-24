import numpy as np
import math
from core_ext.mesh import Mesh
from core_ext.instanced_object_factory import InstancedObjectFactory
from geometry.custom import CustomGeometry
from geometry.bar import BarGeometry
from geometry.jukebox import JukeboxGeometry
from light.ambient import AmbientLight
from light.point import PointLight
from light.directional import DirectionalLight
from light.spotlight import SpotLight
from extras.directional_light import DirectionalLightHelper

class BarSceneLoader:
    """Helper class for loading bar scene components"""
    def __init__(self, scene_builder, obj_reader):
        self.scene = scene_builder
        self.obj_reader = obj_reader
        self.light_number = 12
        
    def load_lights(self):
        """Load all lights in the scene"""
        # Ambient light
        ambient_light = AmbientLight(color=[0.1, 0.1, 0.1])
        self.scene.add_to_dynamic(ambient_light)
        
        # Flashlight
        flashlight = SpotLight(
            color=(1.0, 1.0, 1),      
            position=(0, 3.5, -11),       
            direction=(0, 0.4, 1),      
            cutoff_angle=20,       
            inner_cutoff_angle=5,
            attenuation=(1.0, 0.01, 0.001)
        )       
        self.scene.add_to_dynamic(flashlight)
        
        # Directional light
        directional_light = DirectionalLight(
            color=[0.1, 0.1, 0.1],
            direction=[0, -1, -1],
        )
        directional_light.set_position([0, 3.5, -11])
        self.scene.add_to_dynamic(directional_light)
        direct_helper = DirectionalLightHelper(directional_light)
        directional_light.add(direct_helper)
        
        # Table lights
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
        for pos in table_positions:
            pointlight = PointLight(
                color=[0.8, 1, 0.8],
                position=(pos + np.array([0, 1.45, 0]))
            )
            self.scene.add_to_dynamic(pointlight)
            
        # Ceiling lights
        for i in range(5):
            ceilinglight = PointLight(
                color=[0.5, 0.5, 0.2],
                position=[-9 - i, 3.5, 12]
            )
            self.scene.add_to_dynamic(ceilinglight)
            
        return directional_light
        
    def load_bar_structure(self):
        """Load the main bar structure (walls, floor, roof)"""
        wall_geometry, floor_geometry, roof_geometry, door_geometry = BarGeometry(
            1, 1, 1, 
            self.obj_reader('objects/interior.obj')
        )
        
        # Create materials
        wall_material = self.scene.get_cached_material(
            "LambertMaterial",
            texture=self.scene.get_cached_texture("images/brick.jpg"),
            bump_texture=self.scene.get_cached_texture("images/brick-normal-map.png"),
            property_dict={"bumpStrength": 1},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        floor_material = self.scene.get_cached_material(
            "PhongMaterial",
            texture=self.scene.get_cached_texture("images/rubber_tiles.jpg"),
            bump_texture=self.scene.get_cached_texture("images/rubber_tiles_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        roof_material = self.scene.get_cached_material(
            "LambertMaterial",
            texture=self.scene.get_cached_texture("images/tiles.jpg"),
            bump_texture=self.scene.get_cached_texture("images/tiles_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        door_material = self.scene.get_cached_material(
            "LambertMaterial",
            texture=self.scene.get_cached_texture("images/door_texture.jpg"),
            bump_texture=self.scene.get_cached_texture("images/door_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        # Create meshes
        wall_mesh = Mesh(wall_geometry, wall_material)
        floor_mesh = Mesh(floor_geometry, floor_material)
        roof_mesh = Mesh(roof_geometry, roof_material)
        door_mesh = Mesh(door_geometry, door_material)
        
        # Add to scene
        self.scene.add_to_static(wall_mesh)
        self.scene.add_to_static(floor_mesh)
        self.scene.add_to_static(roof_mesh)
        self.scene.add_to_static(door_mesh)
        
    def load_bottles(self):
        """Load bottle instances"""
        bottle_geometries = CustomGeometry(1, 1, 1, self.obj_reader('objects/bottle.obj'))
        bottle_geo = bottle_geometries.get("outer")
        liquid_geo = bottle_geometries.get("inner")
        cork_geo = bottle_geometries.get("rolha")
        
        # Create bottle instances
        bottle_factory = InstancedObjectFactory(
            bottle_geo,
            self.scene.get_cached_material(
                "PhongMaterial",
                property_dict={"baseColor": [0, 0.7, 0]},
                number_of_light_sources=self.light_number,
                use_shadow=True,
                opacity=0.2
            )
        )
        
        # Add bottle instances
        bottle_x = -9.5
        bottle_y = 1
        for i in range(4):
            for j in range(7):
                bottle_factory.add_instance([bottle_x, bottle_y, 14.5])
                bottle_x -= 0.5
            bottle_y += 0.7
            bottle_x = -9.5
            
        # Create bottle mesh
        bottle_mesh = bottle_factory.build_mesh(self.scene._create_instanced_mesh)
        self.scene.add_to_static(bottle_mesh)
        
        # Create liquid instances
        liquid_factory = InstancedObjectFactory(
            liquid_geo,
            self.scene.get_cached_material(
                "TransparentMaterial",
                color=[0.3, 0.3, 0],
                opacity=0.5
            )
        )
        liquid_factory.add_instances(bottle_factory.positions)
        liquid_mesh = liquid_factory.build_mesh(self.scene._create_instanced_mesh)
        self.scene.add_to_static(liquid_mesh)
        
        # Create cork instances
        cork_factory = InstancedObjectFactory(
            cork_geo,
            self.scene.get_cached_material(
                "LambertMaterial",
                property_dict={"baseColor": [0.8, 0.8, 0.0]},
                number_of_light_sources=self.light_number,
                use_shadow=True
            )
        )
        cork_factory.add_instances(bottle_factory.positions)
        cork_mesh = cork_factory.build_mesh(self.scene._create_instanced_mesh)
        self.scene.add_to_static(cork_mesh)
        
    def load_puff_chairs(self):
        """Load puff chair instances"""
        puff_chair_geometries = CustomGeometry(1, 1, 1, self.obj_reader('objects/puffchair.obj'))
        cushion_geo = puff_chair_geometries.get("chaircushion")
        chairbase_geo = puff_chair_geometries.get("chairbase")
        
        # Create materials
        cushion_material = self.scene.get_cached_material(
            "LambertMaterial",
            property_dict={"baseColor": [0.2, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        chairbase_material = self.scene.get_cached_material(
            "PhongMaterial",
            property_dict={"baseColor": [0.05, 0.05, 0.05]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        # Create factories
        cushion_factory = InstancedObjectFactory(cushion_geo, cushion_material)
        chairbase_factory = InstancedObjectFactory(chairbase_geo, chairbase_material)
        
        # Add chair instances around tables
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
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
                
        # Create meshes
        cushion_mesh = cushion_factory.build_mesh(self.scene._create_instanced_mesh)
        chairbase_mesh = chairbase_factory.build_mesh(self.scene._create_instanced_mesh)
        
        # Add to scene
        self.scene.add_to_static(cushion_mesh)
        self.scene.add_to_static(chairbase_mesh)
        
    def load_lamps(self):
        """Load lamp instances"""
        lamp_geometries = CustomGeometry(1, 1, 1, self.obj_reader('objects/lamp.obj'))
        base_geometry = lamp_geometries.get("base")
        lamp_geometry = lamp_geometries.get("lamp")
        lampshade_geometry = lamp_geometries.get("lampshade")
        switch_geometry = lamp_geometries.get("switch")
        
        # Create materials
        base_material = self.scene.get_cached_material(
            "PhongMaterial",
            property_dict={"baseColor": [1.0, 0.8, 0.0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        lamp_material = self.scene.get_cached_material(
            "PhongMaterial",
            property_dict={"baseColor": [1.0, 1.0, 0.8]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        lampshade_material = self.scene.get_cached_material(
            "PhongMaterial",
            property_dict={"baseColor": [0.3, 0.8, 0.4]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        switch_material = self.scene.get_cached_material(
            "PhongMaterial",
            property_dict={"baseColor": [0.1, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        
        # Create factories
        base_factory = InstancedObjectFactory(base_geometry, base_material)
        lamp_factory = InstancedObjectFactory(lamp_geometry, lamp_material)
        lampshade_factory = InstancedObjectFactory(lampshade_geometry, lampshade_material)
        switch_factory = InstancedObjectFactory(switch_geometry, switch_material)
        
        # Add lamp instances
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
        for pos in table_positions:
            lamp_pos = pos + np.array([0, 0.9, 0])
            base_factory.add_instance(lamp_pos)
            lamp_factory.add_instance(lamp_pos)
            lampshade_factory.add_instance(lamp_pos)
            switch_factory.add_instance(lamp_pos)
            
        # Create meshes
        base_mesh = base_factory.build_mesh(self.scene._create_instanced_mesh)
        lamp_mesh = lamp_factory.build_mesh(self.scene._create_instanced_mesh)
        lampshade_mesh = lampshade_factory.build_mesh(self.scene._create_instanced_mesh)
        switch_mesh = switch_factory.build_mesh(self.scene._create_instanced_mesh)
        
        # Add to scene
        self.scene.add_to_static(base_mesh)
        self.scene.add_to_static(lamp_mesh)
        self.scene.add_to_static(lampshade_mesh)
        self.scene.add_to_static(switch_mesh) 