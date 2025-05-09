import numpy as np
import math
import pathlib
import sys

#core imports
from core.base import Base
from core.obj_reader import my_obj_reader
#core_ext imports
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.render_target import RenderTarget
from core_ext.texture import Texture
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
from geometry.box import BoxGeometry  
from geometry.cylinder import CylinderGeometry
from geometry.cone import ConeGeometry
from geometry.bar import BarGeometry
from geometry.neonsign import NeonSignGeometry
from geometry.stagewireframe import WireframeGeometry
from geometry.sphere import SphereGeometry
from geometry.stage import StageGeometry
from geometry.lamp import LampGeometry
from geometry.jukebox import JukeboxGeometry

class Example(Base):
    """
    Render the axes and the rotated xy-grid.
    Add camera movement: WASDRF(move), QE(turn), TG(look).
    """

    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer( clear_color=[0,0,0])
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=1920/1080)


        #Lights
        #AmbientLight
        ambient_light = AmbientLight(color=[0.2, 0.2, 0.2])
        self.scene.add(ambient_light)
        #self.point_light = PointLight(color=[1, 1, 1], position=[10, 3, 1])
        #self.scene.add(self.point_light)
        
        #SpotLights
        
        flashlight = SpotLight(
            color=(1.0, 1.0, 1),      
            position=(0, 2, 5),       
            direction=(0, 0, 1),      
            cutoff_angle=1,       
            inner_cutoff_angle=1,
            attenuation=(1.0, 0.01, 0.001)
        )       
        self.scene.add(flashlight)
        
        #DirectionalLight
        """
        directional_light = DirectionalLight(
            color=[0.1,0.1,0.1],
            direction=[0,0,-2],
        )
        directional_light.set_position([0,2,5])
        self.scene.add(directional_light)
        direct_helper = DirectionalLightHelper(directional_light)
        directional_light.add(direct_helper)"""
        self.renderer.enable_shadows(flashlight,resolution=(1024,1024))

        #PointLights
        # Table positions
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
        for i in range(4):
            pointlight = PointLight(color=[0.8,1,0.8],position=(table_positions[i] + np.array([0,1.45,0])))
            self.scene.add(pointlight)
            
        self.light_number = 2 + 4
        #self.scene.add(light_cone)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([0.5, 1.3, 1])
        self.scene.add(self.rig)
        
        #BarInterior
        wall_geometry, floor_geometry, roof_geometry, door_geometry = BarGeometry(1, 1, 1, my_obj_reader('objects/interior.obj'))
        wall_material = PhongMaterial(
            texture=Texture("images/brick.jpg"),
            bump_texture=Texture("images/brick-normal-map.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        floor_material = PhongMaterial(
            texture=Texture("images/rubber_tiles.jpg"),
            bump_texture=Texture("images/rubber_tiles_bump.png"),
            property_dict={"bumpStrength": 3},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        roof_material = PhongMaterial(
            texture=Texture("images/tiles.jpg"),
            bump_texture=Texture("images/tiles_bump.png"),
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
        self.scene.add(wall_mesh)
        self.scene.add(floor_mesh)
        self.scene.add(roof_mesh)
        self.scene.add(door_mesh)

        ####Meshes#####

        #Box
        #box_geometry = BoxGeometry(width=1, height=1, depth=1)
        #box_material = BasicMaterial()
        #self.box = Mesh(geometry=box_geometry,material=box_material)
        #self.box.translate(0, 1.5, 0) 
        #self.scene.add(self.box)

        #Table
        table_geometry = WireframeGeometry(1,1,1,my_obj_reader("objects/squaretable.obj"))
        table_material = PhongMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        table = Mesh(geometry=table_geometry,material=table_material)
        table.set_position([14,0,-14])
        self.scene.add(table)
        #Sonic
        tv_geometry = WireframeGeometry(1,1,1,my_obj_reader("objects/television.obj"))
        tv_material = PhongMaterial(
            texture=Texture("images/tv_texture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        tv = Mesh(geometry=tv_geometry,material=tv_material)
        tv.set_position([14,1.1,-14])
        self.scene.add(tv)
        geometry = RectangleGeometry(0.7,0.7)
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
        self.sprite = Mesh(geometry, sprite_material)
        self.sprite.set_position([14,1.1,-13.60])
        self.scene.add(self.sprite)

        #BarStand
        barstand_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/barstand.obj'))
        barstand_material = PhongMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        barstand = Mesh(geometry=barstand_geometry,material=barstand_material)
        barstand.rotate_y(math.radians(90))
        barstand.set_position([-10,0,12])
        self.scene.add(barstand)
        #Shelf
        shelf_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/shelf.obj'))
        shelf_material = PhongMaterial(
            texture=Texture("images/darkwood.jpg"),
            bump_texture=Texture("images/TableWood_Normal.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        shelf = Mesh(geometry=shelf_geometry,material=shelf_material)
        shelf.rotate_y(math.radians(180))
        shelf.set_position([-11.1,0,14.3])
        self.scene.add(shelf)
        #BarStool 
        barstool_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/barstool.obj'))
        barstool_material = PhongMaterial(
            texture=Texture("images/barstooltexture.png"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        x_coord = 0
        for i in range(4):
            barstool = Mesh(geometry=barstool_geometry, material=barstool_material)
            barstool.set_position([-12.5 + x_coord,0,11])
            self.scene.add(barstool)
            x_coord += 1
        
        #StageWireframe
        wireframe_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/stage_wireframe.obj'))
        wireframe_material = PhongMaterial(
            property_dict={"baseColor":[0.1, 0.1, 0.1]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        wireframe = Mesh(geometry=wireframe_geometry,material=wireframe_material)
        wireframe.set_position([0,0,-10])
        self.scene.add(wireframe)

        #Stage
        stage_geometry, frame_geometry, cloth_geometry1, cloth_geometry2, backstage_geometry = StageGeometry(1,1,1,my_obj_reader('objects/stage.obj'))
        stage_material = PhongMaterial(
            texture=Texture("images/lightwood.jpg"),
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        stage = Mesh(geometry=stage_geometry,material=stage_material)
        stage.set_position([0,0,-11.5])
        self.scene.add(stage)
        frame_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        frame = Mesh(geometry=frame_geometry,material=frame_material)
        frame.local_matrix = stage.local_matrix
        self.scene.add(frame)
        cloth_material = PhongMaterial(
            property_dict={"baseColor":[0.5, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        cloth1 = Mesh(geometry=cloth_geometry1,material=cloth_material)
        cloth1.local_matrix = stage.local_matrix
        self.scene.add(cloth1)
        cloth2 = Mesh(geometry=cloth_geometry2,material=cloth_material)
        cloth2.local_matrix = stage.local_matrix
        self.scene.add(cloth2)
        backstage_material = PhongMaterial(
            property_dict={"baseColor": [0.8,0.8,0.6]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        backstage = Mesh(geometry=backstage_geometry,material=backstage_material)
        backstage.local_matrix = stage.local_matrix
        self.scene.add(backstage)

        #PuffChair
        chair_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/puffchair.obj'))
        chair_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        # Place 4 chairs around each table
        for tx, ty, tz in table_positions:
            for i in range(4):
                angle_deg = i * 90
                angle_rad = math.radians(angle_deg)
                dx = math.sin(angle_rad) * 1.5
                dz = math.cos(angle_rad) * 1.5
                chair = Mesh(geometry=chair_geometry, material=chair_material)
                chair.set_position([tx + dx, 0, tz + dz])
                chair.rotate_y(angle_rad + math.pi)
                self.scene.add(chair)
        #RoundTables
        roundtable_geometry = WireframeGeometry(1,1,1,my_obj_reader('objects/table.obj'))
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
        self.scene.add(roundtable1)
        self.scene.add(roundtable2)
        self.scene.add(roundtable3)
        self.scene.add(roundtable4)
        #lamps
        base_geometry, lamp_geometry, lampshade_geometry, switch_geometry = LampGeometry(1,1,1,my_obj_reader('objects/lamp.obj'))
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
        for i in range(4):
            base = Mesh(geometry=base_geometry,material=base_material)
            lamp = Mesh(geometry=lamp_geometry,material=lamp_material)
            lampshade = Mesh(geometry=lampshade_geometry,material=lampshade_material)
            switch = Mesh(geometry=switch_geometry,material=switch_material)
            pos = table_positions[i] + np.array([0,0.9,0])
            base.set_position(pos)
            lamp.local_matrix = base.local_matrix
            lampshade.local_matrix = base.local_matrix
            switch.local_matrix = base.local_matrix
            self.scene.add(base)
            self.scene.add(lamp)
            self.scene.add(lampshade)
            self.scene.add(switch)
        #mirrorball
        cable_geometry = CylinderGeometry(radius=0.02,height=1)
        cable_material  = PhongMaterial(
            property_dict={"baseColor": [0,0,0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        cable = Mesh(cable_geometry,cable_material)
        cable.set_position([0,4.5,0])
        self.scene.add(cable)
        mirrorball_geometry = SphereGeometry(radius=0.5)
        mirrorball_material = PhongMaterial(
            texture=Texture("images/mirrorball.jpg"),
            bump_texture=Texture("images/mirrorball_normal.jpg"),
            property_dict={"bumpStrength": 10},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        globe = Mesh(geometry=mirrorball_geometry, material=mirrorball_material)
        globe.set_position([0,4,0])
        self.scene.add(globe)

        #NeonSign
        blue_geo, yellow_geo, black_geo = NeonSignGeometry(1, 1, 1, my_obj_reader('objects/neonsign.obj'))
        self.bluesign_material = SurfaceMaterial(property_dict={"baseColor": [0.0, 1.0, 1.0]})
        self.yellowsign_material = SurfaceMaterial(property_dict={"baseColor": [1.0, 1.0, 0.0]})
        blacksign_material = SurfaceMaterial(property_dict={"baseColor": [0., 0, 0]})
        self.blueSign = Mesh(blue_geo,self.bluesign_material)
        self.yellowSign = Mesh(yellow_geo,self.yellowsign_material)
        blackSign = Mesh(black_geo,blacksign_material)

        self.blueSign.rotate_y(math.radians(90))
        self.blueSign.set_position([-14.9, 2, 10])
        self.yellowSign.local_matrix = self.blueSign.local_matrix
        blackSign.local_matrix = self.blueSign.local_matrix
        self.scene.add(self.blueSign)
        self.scene.add(self.yellowSign)
        self.scene.add(blackSign)

        #Jukebox
        wood_geo, neon_geo, metal_geo, red_geo, metalmesh_geo, selectcoin_geo, selectsong_geo, vinyl_geo, songs1_geo, songs2_geo, glass_geo = JukeboxGeometry(1,1,1,my_obj_reader('objects/jukebox.obj'))
        wood_material = LambertMaterial(
            property_dict={"baseColor":[0.2, 0.1, 0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        neon_material = PhongMaterial(
            property_dict={"baseColor": [0.0, 1.0, 1.0]},
            number_of_light_sources=self.light_number,
            use_shadow=True
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
        self.scene.add(wood)
        self.scene.add(self.neon)
        self.scene.add(metal)
        self.scene.add(red)
        self.scene.add(metalmesh)
        self.scene.add(selectcoin)
        self.scene.add(selectsong)
        self.scene.add(self.vinyl)
        self.scene.add(songlist1)
        self.scene.add(songlist2)
        self.scene.add(glass)

        #self.postprocessor = Postprocessor(self.renderer,self.scene, self.camera)

        #####glow scene#####
        self.glowScene = Scene()
        #Box
        #cyanMaterial = SurfaceMaterial(property_dict={"baseColor": [0,1,1]})
        #glow_box = Mesh(box_geometry,cyanMaterial)
        #glow_box.local_matrix = self.box.local_matrix
        #self.glowScene.add(glow_box)
        
        #Jukebox Neon
        self.neonJukeboxMaterial = SurfaceMaterial(property_dict={"baseColor": [0.0, 0.6, 0.6]})
        self.neonJukebox = Mesh(neon_geo,self.neonJukeboxMaterial)
        self.neonJukebox.local_matrix = self.neon.local_matrix
        self.glowScene.add(self.neonJukebox)
        
        #Neon Sign
        self.neonBlueSign = Mesh(blue_geo,self.bluesign_material)
        self.neonYellowSign = Mesh(yellow_geo,self.yellowsign_material)
        self.neonBlueSign.local_matrix = self.blueSign.local_matrix
        self.neonYellowSign.local_matrix = self.yellowSign.local_matrix
        self.current_glow = self.neonBlueSign
        self.glowScene.add(self.current_glow)

        #Globe
        glowMaterial = SurfaceMaterial(property_dict={"baseColor": [0.3, 0.3, 0.3]})
        glowingMirrorBall = Mesh(mirrorball_geometry,glowMaterial)
        glowingMirrorBall.local_matrix = globe.local_matrix

        self.glowScene.add(glowingMirrorBall)

        #glow postprocessing
        glow_target = RenderTarget(resolution=[800, 600])
        self.glow_pass = Postprocessor(self.renderer, self.glowScene, self.camera, glow_target)
        #self.postprocessor.add_effect(brightFilterEffect(2))
        self.glow_pass.add_effect( horizontalBlurEffect(texture_size=[800,600], blur_radius=50) )
        self.glow_pass.add_effect( verticalBlurEffect(texture_size=[800,600], blur_radius=50) )


        # combining results of glow effect with main scene
        self.combo_pass = Postprocessor(self.renderer, self.scene, self.camera)
        self.combo_pass.add_effect(
            additiveBlendEffect(
                blend_texture=glow_target.texture,
                original_strength=1,
                blend_strength=3
            )
        )



        #mainScene = self.postprocessor.render_target_list[0].texture
        #self.postprocessor.add_effect( additiveBlendEffect( blend_texture=mainScene, original_strength=2, blend_strength=1) )


        
        ######HUD scene#######
        self.hudScene = Scene()
        self.hudCamera = Camera()
        self.hudCamera.set_orthographic(0,800,0,600,1,-1)
        labelGeo1 = RectangleGeometry(width=600,height=80,position=[0,600],alignment=[0,1])
        labelMat1 = TextureMaterial (Texture("images/Bar Simulator.png"))
        label1 = Mesh(labelGeo1,labelMat1)
        self.hudScene.add(label1)
        



    def update(self):
        # Check for quit event
        #glow_strength = (math.sin(self.time * 2.0) + 1.0) / 2.0  # oscillates between 0 and 1
        #animated_color = [glow_strength * 1.0, glow_strength * 0.5, 0.1]
        #self.glow_material.uniform_dict["emissiveColor"].data = animated_color
        self.vinyl.rotate_y(0.01337)

        rainbow_color = self.get_rainbow_color(self.time)
        neon_material = PhongMaterial(
            property_dict={"baseColor": rainbow_color},
            number_of_light_sources=self.light_number,
            use_shadow=True
        )
        self.neon.material = neon_material
        
        # Update glow scene neon color
        self.neonJukeboxMaterial = SurfaceMaterial(property_dict={"baseColor": rainbow_color})
        self.neonJukebox.material = self.neonJukeboxMaterial
        #NeonSign Update
        blink_interval = 1.0  # seconds
        blinking = int(self.time // blink_interval) % 2 == 0
        if blinking:
            # Blue ON, Yellow OFF
            next_glow = self.neonBlueSign
            self.bluesign_material = SurfaceMaterial(property_dict={"baseColor": [0,1,1]})
            self.yellowsign_material = SurfaceMaterial(property_dict={"baseColor": [0,0,0]})
            self.blueSign.material = self.bluesign_material
            self.yellowSign.material = self.yellowsign_material
        else:
            # Yellow ON, Blue OFF
            next_glow = self.neonYellowSign
            self.bluesign_material = SurfaceMaterial(property_dict={"baseColor": [0,0,0]})
            self.yellowsign_material = SurfaceMaterial(property_dict={"baseColor": [1,1,0]})
            self.blueSign.material = self.bluesign_material
            self.yellowSign.material = self.yellowsign_material

        # Reset glow scene and add the correct glowing mesh
        self.glowScene.remove(self.current_glow)
        self.glowScene.add(next_glow)
        self.current_glow = next_glow

        #Sonic Update
        tile_number = math.floor(self.time * self.tiles_per_second)
        self.sprite.material.uniform_dict["tileNumber"].data = tile_number

        #self.point_light.set_position([math.cos(0.5 * self.time) / 2, math.sin(0.5 * self.time) / 2, 1])

        self.rig.update(self.input, self.delta_time)
        self.glow_pass.render()
        self.combo_pass.render()
        self.renderer.render( self.hudScene, self.hudCamera,clear_color=False)
    

    def get_rainbow_color(self, time):
        # Convert time to a value between 0 and 1
        t = (time % 6) / 6.0  # Complete cycle every 6 seconds
        
        # Define rainbow colors in RGB
        colors = [
            [1.0, 0.0, 0.0],  # Red
            [1.0, 0.5, 0.0],  # Orange
            [1.0, 1.0, 0.0],  # Yellow
            [0.0, 1.0, 0.0],  # Green
            [0.0, 0.0, 1.0],  # Blue
            [0.5, 0.0, 1.0]   # Purple
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
Example(screen_size=[1920, 1080]).run()
