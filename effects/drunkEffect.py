from material.material import Material
import math


class drunkEffect(Material):

    def __init__(self, drunk_level=0.5, time=0.0):
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
        uniform float drunkLevel;
        uniform float time;
        out vec4 fragColor;

        void main()
        {
            vec2 uv = UV;

            // Simple swaying distortion
            float sway = sin(time * 1.5 + uv.y * 8.0) * drunkLevel * 0.01;
            uv.x += sway;

            // Simple blur by sampling nearby pixels
            vec4 color = vec4(0.0);
            float blur = drunkLevel * 0.002;

            // Simple 5-sample blur
            color += texture(textureSampler, uv) * 0.4;
            color += texture(textureSampler, uv + vec2(blur, 0.0)) * 0.15;
            color += texture(textureSampler, uv - vec2(blur, 0.0)) * 0.15;
            color += texture(textureSampler, uv + vec2(0.0, blur)) * 0.15;
            color += texture(textureSampler, uv - vec2(0.0, blur)) * 0.15;

            // Slight chromatic aberration
            if(drunkLevel > 0.3) {
                float aberration = drunkLevel * 0.001;
                color.r = texture(textureSampler, uv + vec2(aberration, 0.0)).r;
                color.b = texture(textureSampler, uv - vec2(aberration, 0.0)).b;
            }

            // Vignette effect
            vec2 vignetteUV = UV - 0.5;
            float vignette = 1.0 - dot(vignetteUV, vignetteUV) * drunkLevel * 0.3;
            color.rgb *= max(vignette, 0.3);

            fragColor = color;
        }
        """

        super().__init__(vertexShaderCode, fragmentShaderCode)
        self.add_uniform("sampler2D", "textureSampler", [None, 1])
        self.add_uniform("float", "drunkLevel", drunk_level)
        self.add_uniform("float", "time", time)
        self.locate_uniforms()

    def update_drunk_level(self, level):
        """Update drunk level (0.0 to 1.0)"""
        self.uniform_dict["drunkLevel"].data = max(0.0, min(1.0, level))

    def update_time(self, time):
        """Update time for animated effects"""
        self.uniform_dict["time"].data = time