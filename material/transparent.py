import OpenGL.GL as GL
from material.material import Material

class TransparentMaterial(Material):
    def __init__(self, color=[1.0, 1.0, 1.0], opacity=0.1):
        vertex_shader_code = """
        uniform mat4 projectionMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 modelMatrix;
        in vec3 vertexPosition;
        void main()
        {
            gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
        }
        """

        fragment_shader_code = """
        uniform vec3 baseColor;
        uniform float opacity;
        out vec4 fragColor;
        void main()
        {
            fragColor = vec4(baseColor, opacity);
        }
        """
        super().__init__(vertex_shader_code, fragment_shader_code)
        self.add_uniform("vec3", "baseColor", color)
        self.add_uniform("float", "opacity", opacity)
        self.locate_uniforms()
        self.setting_dict["doubleSide"] = True  # Renderizar frente e verso
        self.setting_dict["wireframe"] = False
        self.setting_dict["lineWidth"] = 1

    def update_render_settings(self):
        if self.setting_dict["doubleSide"]:
            GL.glDisable(GL.GL_CULL_FACE)
        else:
            GL.glEnable(GL.GL_CULL_FACE)
        if self.setting_dict["wireframe"]:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)