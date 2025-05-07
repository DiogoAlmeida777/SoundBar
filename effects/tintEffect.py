from material.material import Material
import OpenGL.GL as GL

class tintEffect(Material):

      def __init__(self, tint_color = (1,0,0)):
        vertexShaderCode = """
        in vec2 vertexPosition;
        in vec2 vertexUV;
        out vec2 UV;
        void main()
        {
           gl_Position = vec4(vertexPosition, 0.0, 1.0);
           UV = vertexUV;
        }
        """

        fragmentShaderCode = """
        in vec2 UV;
        uniform vec3 tintColor;
        uniform sampler2D textureSampler;
        out vec4 fragColor;
        void main()
        {

         vec4 color = texture2D(textureSampler, UV);
         float gray = (color.r + color.g + color.b) / 3.0;
         fragColor = vec4(gray * tintColor, 1.0);
        }
        """

        super().__init__(vertexShaderCode,fragmentShaderCode)
        self.add_uniform("sampler2D", "textureSampler", [None,1])
        self.add_uniform("vec3", "tintColor", tint_color)
        self.locate_uniforms()