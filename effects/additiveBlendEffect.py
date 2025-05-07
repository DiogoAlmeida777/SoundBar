from material.material import Material
class additiveBlendEffect(Material):

    def __init__(self, blend_texture, original_strength=1, blend_strength=1):
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
        uniform sampler2D blendTexture;
        uniform float originalStrength;
        uniform float blendStrength;
        out vec4 fragColor;
        void main()
        {
            vec4 originalColor = texture2D(textureSampler, UV);
            vec4 blendColor = texture2D(blendTexture, UV);
            vec4 color = originalStrength * originalColor + blendStrength * blendColor;
            fragColor = color;
        }
        """

        super().__init__(vertexShaderCode,fragmentShaderCode)
        self.add_uniform("sampler2D", "textureSampler", [None,1])
        self.add_uniform("sampler2D", "blendTexture", [blend_texture.texture_ref,2])
        self.add_uniform("float", "originalStrength", original_strength)
        self.add_uniform("float", "blendStrength", blend_strength)
        self.locate_uniforms()