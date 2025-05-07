import OpenGL.GL as GL

from core_ext.camera import Camera
from core_ext.render_target import RenderTarget
from material.depth import DepthMaterial


class Shadow:
    def __init__(self,
                 light_source,
                 strength=0.5,
                 resolution=(512, 512),
                 camera_bounds=(-5, 5, -5, 5, 0, 20),
                 bias=0.01,
                 spotlight=False,  # Adicionando parâmetro para verificar se é spotlight
                 spotlight_fov=45,  # FOV para spotlight
                 spotlight_cone_angle=30):  # Ângulo do cone

        self._light_source = light_source
        self._spotlight = spotlight
        self._spotlight_fov = spotlight_fov
        self._spotlight_cone_angle = spotlight_cone_angle
        self._camera = Camera()
        
        if self._spotlight:
            # Para spotlight, configurar uma projeção perspectiva
            self._camera.set_perspective(self._spotlight_fov, 1.0, 0.1, 100)
        else:
            # Para luz direcional, configurar uma projeção ortográfica
            # Usa camera_bounds da luz se disponível, senão usa o padrão
            if hasattr(light_source, 'camera_bounds'):
                camera_bounds = light_source.camera_bounds
            left, right, bottom, top, near, far = camera_bounds
            self._camera.set_orthographic(left, right, bottom, top, near, far)
        
        self._light_source.add(self._camera)
        self._render_target = RenderTarget(
            resolution,
            property_dict={"wrap": GL.GL_CLAMP_TO_BORDER}
        )
        self._material = DepthMaterial()
        self._strength = strength
        self._bias = bias

    @property
    def bias(self):
        return self._bias

    @property
    def camera(self):
        return self._camera

    @property
    def material(self):
        return self._material

    @property
    def light_source(self):
        return self._light_source

    @property
    def render_target(self):
        return self._render_target

    @property
    def strength(self):
        return self._strength

    def update_internal(self):
        self._camera.update_view_matrix()
        self._material.uniform_dict["viewMatrix"].data = self._camera.view_matrix
        self._material.uniform_dict["projectionMatrix"].data = self._camera.projection_matrix
