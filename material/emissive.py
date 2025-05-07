import OpenGL.GL as GL

from material.lighted import LightedMaterial


class EmissiveMaterial(LightedMaterial):
    """
    Material that emits light but is not affected by lighting calculations.
    Useful for glowing objects or UI overlays in 3D scenes.
    """
    def __init__(self, color=(1.0, 1.0, 1.0), texture=None, property_dict=None):
        super().__init__(number_of_light_sources=0)
        self.add_uniform("vec3", "emissiveColor", list(color))

        if texture is None:
            self.add_uniform("bool", "useTexture", False)
        else:
            self.add_uniform("bool", "useTexture", True)
            self.add_uniform("sampler2D", "textureSampler", texture)  # ✅ just pass the texture object

        self.locate_uniforms()

        self.setting_dict["doubleSide"] = True
        self.setting_dict["wireframe"] = False
        self.setting_dict["lineWidth"] = 1
        self.set_properties(property_dict or {}) 

    @property
    def vertex_shader_code(self):
        return """
            uniform mat4 projectionMatrix;
            uniform mat4 viewMatrix;
            uniform mat4 modelMatrix;

            in vec3 vertexPosition;
            in vec2 vertexUV;

            out vec2 UV;

            void main()
            {
                gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
                UV = vertexUV;
            }
        """

    @property
    def fragment_shader_code(self):
        return """
            uniform vec3 emissiveColor;
            uniform bool useTexture;
            uniform sampler2D textureSampler;

            in vec2 UV;
            out vec4 fragColor;

            void main()
            {
                vec4 base = vec4(emissiveColor, 1.0);
                if (useTexture) {
                    base *= texture(textureSampler, UV);
                }
                fragColor = base;
            }
        """

    def update_render_settings(self):
        if self.setting_dict["doubleSide"]:
            GL.glDisable(GL.GL_CULL_FACE)
        else:
            GL.glEnable(GL.GL_CULL_FACE)

        if self.setting_dict["wireframe"]:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

        GL.glLineWidth(self.setting_dict["lineWidth"])