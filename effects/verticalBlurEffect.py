from material.material import Material
class verticalBlurEffect(Material):

    def __init__(self, texture_size=[512,512], blur_radius=20):
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
        uniform vec2 textureSize;
        uniform int blurRadius;
        out vec4 fragColor;
        void main()
        {
            vec2 pixelToTextureCoords = 1 / textureSize;
            vec4 averageColor = vec4(0,0,0,0);
            for (int offsetY = -blurRadius; offsetY <= blurRadius; offsetY++)
            {
                float weight = blurRadius - abs(offsetY) + 1;
                vec2 offsetUV = vec2(0, offsetY) * pixelToTextureCoords;
                averageColor += texture2D(textureSampler, UV + offsetUV) * weight;
            }
            averageColor /= averageColor.a;
            fragColor = averageColor;
        }
        """

        super().__init__(vertexShaderCode,fragmentShaderCode)
        self.add_uniform("sampler2D", "textureSampler", [None,1])
        self.add_uniform("vec2", "textureSize", texture_size)
        self.add_uniform("int", "blurRadius", blur_radius)
        self.locate_uniforms()