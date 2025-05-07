import OpenGL.GL as GL
from material.material import Material

class LightMaterial(Material):
    def __init__(self, property_dict={}):
        vertex_shader_code = """
        uniform mat4 projectionMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 modelMatrix;
        in vec3 vertexPosition;
        out vec3 vPosition;
        
        void main()
        {
            vec4 worldPosition = modelMatrix * vec4(vertexPosition, 1.0);
            vPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * viewMatrix * worldPosition;
        }
        """

        fragment_shader_code = """
        uniform vec3 lightColor;
        uniform float intensity;
        in vec3 vPosition;
        out vec4 fragColor;

        void main()
        {
            // Opacidade decresce quanto mais longe do centro
            float distanceFromCenter = length(vPosition.xy);
            float alpha = 1.0 - distanceFromCenter; 
            alpha = clamp(alpha, 0.0, 1.0);
            alpha = pow(alpha, 3.0); // Torna mais concentrado no meio
            
            fragColor = vec4(lightColor, alpha * intensity);
            if (fragColor.a < 0.01)
                discard;
        }
        """

        super().__init__(vertex_shader_code, fragment_shader_code)
        self.add_uniform("vec3", "lightColor", [1.0, 1.0, 1.0])  # Luz branca por defeito
        self.add_uniform("float", "intensity", 0.5)  # Meio transparente
        self.locate_uniforms()

        self.setting_dict["doubleSide"] = True
        self.setting_dict["wireframe"] = False
        self.setting_dict["lineWidth"] = 1
        self.setting_dict["transparent"] = True  # <- importante para blend
        self.set_properties(property_dict)

    def update_render_settings(self):
        if self.setting_dict.get("transparent", False):
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        else:
            GL.glDisable(GL.GL_BLEND)

        if self.setting_dict["doubleSide"]:
            GL.glDisable(GL.GL_CULL_FACE)
        else:
            GL.glEnable(GL.GL_CULL_FACE)

        if self.setting_dict["wireframe"]:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

        GL.glLineWidth(self.setting_dict["lineWidth"])