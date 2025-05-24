from material.material import Material
class vignetteEffect(Material):

    def __init__(self, dim_start=0.4, dim_end=1.0, dim_color=(0,0,0)):
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
        uniform sampler2D textureSampler;
        uniform float dimStart;
        uniform float dimEnd;
        uniform vec3 dimColor;
        out vec4 fragColor;

        void main()
        {   
            vec4 color = texture(textureSampler, UV);
            // calculate position in clip space from UV coordinates
            vec2 position = 2 * UV - vec2(1,1);
            // calculate distance (d) from center, which affects brightness
            float d = length(position);
            // calculate brightness (b) factor:
            // when d=dimStart, b=1; when d=dimEnd, b=0.
            float b = (d - dimEnd)/(dimStart - dimEnd);
            // prevent oversaturation
            b = clamp(b, 0, 1);
            // mix the texture color and dim color
            fragColor = vec4( b * color.rgb + (1-b) * dimColor, 1 );
        }
        """

        super().__init__(vertexShaderCode,fragmentShaderCode)
        self.add_uniform("sampler2D", "textureSampler", [None,1])
        self.add_uniform("float", "dimStart", dim_start)
        self.add_uniform("float", "dimEnd", dim_end)
        self.add_uniform("vec3", "dimColor", dim_color)
        self.locate_uniforms()