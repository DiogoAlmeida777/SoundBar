
from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.texture import Texture
from geometry.rectangle import RectangleGeometry
from extras.point_light import PointLightHelper
from light.ambient import AmbientLight
from light.point import PointLight
from material.lambert import LambertMaterial
import math



class Example(Base):
    """ Bump mapping: combining color textures with normal map textures """
    def initialize(self):
        print("Initializing program...")
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=800/600)
        self.camera.set_position([0, 0, 2])

        ambient_light = AmbientLight(color=[0.3, 0.3, 0.3])
        self.scene.add(ambient_light)
        self.point_light = PointLight(color=[1, 1, 1], position=[1, 0, 1])
        self.scene.add(self.point_light)
        # texture of a brick wall
        color_texture = Texture("images/brick-wall.jpg")
        # texture of normals of the brick wall
        bump_texture = Texture("images/brick-wall-normal-map.jpg")

        rectangle_geometry = RectangleGeometry(width=2, height=2)

        color_material = LambertMaterial(
            texture=color_texture,
            number_of_light_sources=2
        )

        bump_material = LambertMaterial(
            texture=color_texture,
            bump_texture=bump_texture,
            property_dict={"bumpStrength": 1},
            number_of_light_sources=2
        )
        

        # Replace color_material and bump_material
        # in Mesh to see a difference
        mesh = Mesh(rectangle_geometry, bump_material)
        self.scene.add(mesh)

        point_light_helper = PointLightHelper(self.point_light)
        self.point_light.add(point_light_helper)

    def update(self):
        self.point_light.set_position([math.cos(0.5 * self.time) / 2, math.sin(0.5 * self.time) / 2, 1])
        self.renderer.render(self.scene, self.camera)


# Instantiate this class and run the program
Example(screen_size=[800, 600]).run()