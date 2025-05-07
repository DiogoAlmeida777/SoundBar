#!/usr/bin/python3
import math
import pathlib
import sys

# Get the package directory
package_dir = str(pathlib.Path(__file__).resolve().parents[2])
# Add the package directory into sys.path if necessary
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

import OpenGL.GL as GL

from core.base import Base
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.texture import Texture
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from material.phong import PhongMaterial
from material.texture import TextureMaterial
from geometry.rectangle import RectangleGeometry
from geometry.sphere import SphereGeometry
from extras.movement_rig import MovementRig
from extras.directional_light import DirectionalLightHelper
from light.spotlight import SpotLight
from geometry.stagewireframe import WireframeGeometry
from core.obj_reader import my_obj_reader
from extras.postprocessor import Postprocessor
from core_ext.render_target import RenderTarget
from material.surface import SurfaceMaterial
from effects.horizontalBlurEffect import horizontalBlurEffect
from effects.verticalBlurEffect import verticalBlurEffect
from effects.additiveBlendEffect import additiveBlendEffect
from effects.brightFilterEffect import brightFilterEffect
class Example(Base):
    """
    Render shadows using shadow pass by depth buffers for the directional light.
    """
    def initialize(self):
        self.renderer = Renderer([0, 0, 0])
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=800/600)
        self.rig = MovementRig()
        self.rig.add(self.camera)
        self.rig.set_position([0, 2, 5])

        ambient_light = AmbientLight(color=[0.2, 0.2, 0.2])
        self.scene.add(ambient_light)
        self.directional_light = DirectionalLight(color=[0.5, 0.5, 0.5], direction=[-1, -1, 0])
        # The directional light can take any position because it covers all the space.
        # The directional light helper is a child of the directional light.
        # So changing the global matrix of the parent leads to changing
        # the global matrix of its child.
        self.directional_light.set_position([2, 4, 0])
        self.scene.add(self.directional_light)
        direct_helper = DirectionalLightHelper(self.directional_light)
        self.directional_light.add(direct_helper)

        sphere_geometry = SphereGeometry()
        phong_material = PhongMaterial(
            texture=Texture("images/grid.jpg"),
            number_of_light_sources=2,
            use_shadow=True
        )

        sphere1 = Mesh(sphere_geometry, phong_material)
        sphere1.set_position([-2, 1, 0])
        self.scene.add(sphere1)

        sphere2 = Mesh(sphere_geometry, phong_material)
        sphere2.set_position([1, 2.2, -0.5])
        self.scene.add(sphere2)

        self.renderer.enable_shadows(self.directional_light)

        """
        # optional: render depth texture to mesh in scene
        depth_texture = self.renderer.shadow_object.render_target.texture
        shadow_display = Mesh(RectangleGeometry(), TextureMaterial(depth_texture))
        shadow_display.set_position([-1, 3, 0])
        self.scene.add(shadow_display)
        """
        
        floor = Mesh(RectangleGeometry(width=20, height=20), phong_material)
        floor.rotate_x(-math.pi / 2)
        self.scene.add(floor)
    
        self.glowScene = Scene()

        glowMaterial = SurfaceMaterial(property_dict={"baseColor": [1, 0, 0]})
        glowingMirrorBall = Mesh(sphere_geometry,glowMaterial)
        glowingMirrorBall.local_matrix = sphere1.local_matrix

        self.glowScene.add(glowingMirrorBall)

        glow_target = RenderTarget(resolution=[800, 600])
        self.glow_pass = Postprocessor(self.renderer, self.glowScene, self.camera, glow_target)
        self.glow_pass.add_effect(brightFilterEffect(1))
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


        


    def update(self):
        #"""
        # view dynamic shadows -- need to increase shadow camera range
        self.directional_light.rotate_y(0.01337, False)
        #"""
        self.rig.update( self.input, self.delta_time)
        
        self.renderer.render(self.scene, self.camera)
        self.glow_pass.render()
        self.combo_pass.render()
        """
        # render scene from shadow camera
        shadow_camera = self.renderer.shadow_object.camera
        self.renderer.render(self.scene, shadow_camera)
        """


# Instantiate this class and run the program
Example(screen_size=[800, 600]).run()