import OpenGL.GL as GL

from material.lighted import LightedMaterial


class LambertMaterial(LightedMaterial):
    """
    Lambert material with at least one light source (or more)
    """
    def __init__(self,
                 texture=None,
                 property_dict=None,
                 number_of_light_sources=1,
                 bump_texture=None,
                 use_shadow=False):
        super().__init__(number_of_light_sources)
        self.add_uniform("vec3", "baseColor", [1.0, 1.0, 1.0])

        if texture is None:
            self.add_uniform("bool", "useTexture", False)
        else:
            self.add_uniform("bool", "useTexture", True)
            self.add_uniform("sampler2D", "textureSampler", [texture.texture_ref, 1])

        if bump_texture is None:
            self.add_uniform("bool", "useBumpTexture", False)
        else:
            self.add_uniform("bool", "useBumpTexture", True)
            self.add_uniform("sampler2D", "bumpTextureSampler", [bump_texture.texture_ref, 2])
            self.add_uniform("float", "bumpStrength", 1.0)

        if not use_shadow:
            self.add_uniform("bool", "useShadow", False)
        else:
            self.add_uniform("bool", "useShadow", True)
            self.add_uniform("Shadow", "shadow0", None)

        self.locate_uniforms()

        # Render both sides?
        self.setting_dict["doubleSide"] = True
        # Render triangles as wireframe?
        self.setting_dict["wireframe"] = False
        # Set line thickness for wireframe rendering
        self.setting_dict["lineWidth"] = 1
        self.set_properties(property_dict)

    @property
    def vertex_shader_code(self):
        return """
            uniform mat4 projectionMatrix;
            uniform mat4 viewMatrix;
            uniform mat4 modelMatrix;
            in vec3 vertexPosition;
            in vec2 vertexUV;
            in vec3 vertexNormal;
            out vec3 position;
            out vec2 UV;
            out vec3 normal;
            
            struct Shadow
            {
                // direction of light that casts shadow
                vec3 lightDirection;
                // data from camera that produces depth texture
                mat4 projectionMatrix;
                mat4 viewMatrix;
                // texture that stores depth values from shadow camera
                sampler2D depthTextureSampler;
                // regions in shadow multiplied by (1-strength)
                float strength;
                // reduces unwanted visual artifacts
                float bias;
            };
            
            uniform bool useShadow;
            uniform Shadow shadow0;
            out vec3 shadowPosition0;

            void main()
            {
                gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1);
                position = vec3(modelMatrix * vec4(vertexPosition, 1));
                UV = vertexUV;
                normal = normalize(mat3(modelMatrix) * vertexNormal);
                
                if (useShadow)
                {
                    vec4 temp0 = shadow0.projectionMatrix * shadow0.viewMatrix * modelMatrix * vec4(vertexPosition, 1);
                    shadowPosition0 = vec3(temp0);
                }            
            }
        """

    @property
    def fragment_shader_code(self):
        return """        
            struct Light
            {
                int lightType;  // 1 = AMBIENT, 2 = DIRECTIONAL, 3 = POINT, 4 = SPOT
                vec3 color;  // used by all lights
                vec3 direction;  // used by directional lights
                vec3 position;  // used by point lights
                vec3 attenuation;  // used by directional lights
                float cutoff;
                float innerCutoff;
            };\n\n""" \
            + self.declaring_light_uniforms_in_shader_code + """
            vec3 calculateLight(Light light, vec3 pointPosition, vec3 pointNormal)
            {
                float ambient = 0;
                float diffuse = 0;
                float specular = 0;
                float attenuation = 1;
                vec3 lightDirection = vec3(0, 0, 0);
                float cutoff = 0.98;
                float innerCutoff = 0.98;

                
                if (light.lightType == 1)  // ambient light
                {
                    ambient = 1;
                }                
                else if (light.lightType == 2)  // directional light
                {
                    lightDirection = normalize(light.direction);
                }
                else if (light.lightType == 3)  // point light 
                {
                    lightDirection = normalize(pointPosition - light.position);
                    float distance = length(light.position - pointPosition);
                    attenuation = 1.0 / (light.attenuation[0] 
                                       + light.attenuation[1] * distance 
                                       + light.attenuation[2] * distance * distance);
                }
                else if (light.lightType == 4) // spot light
                {
                    lightDirection = normalize(pointPosition - light.position);
                    
                    float distance = length(light.position - pointPosition);
                    cutoff = light.cutoff;
                    attenuation = 1.0 / (light.attenuation[0] 
                                       + light.attenuation[1] * distance 
                                       + light.attenuation[2] * distance * distance);
                    
                    
                    float theta = dot(lightDirection,normalize(-light.direction));
                    innerCutoff = light.innerCutoff;
                    float outerCutoff = light.cutoff;
                    
                    float intensity = smoothstep(outerCutoff,innerCutoff, theta);

                    attenuation *= intensity;
                                    
                    if (theta < cutoff)
                    {
                        attenuation = 0.0; 
                    }
                }
                
                if (light.lightType > 1)  // directional or point light
                {
                    pointNormal = normalize(pointNormal);
                    diffuse = abs(dot(pointNormal, -lightDirection));
                    diffuse *= attenuation;
                }
                return light.color * (ambient + diffuse + specular);
            }
            
            uniform vec3 baseColor;
            uniform bool useTexture;
            uniform sampler2D textureSampler;
            uniform bool useBumpTexture;
            uniform sampler2D bumpTextureSampler;
            uniform float bumpStrength;
            in vec3 position;
            in vec2 UV;
            in vec3 normal;
            out vec4 fragColor;
            
            struct Shadow
            {
                // direction of light that casts shadow
                vec3 lightDirection;
                // data from camera that produces depth texture
                mat4 projectionMatrix;
                mat4 viewMatrix;
                // texture that stores depth values from shadow camera
                sampler2D depthTextureSampler;
                // regions in shadow multiplied by (1-strength)
                float strength;
                // reduces unwanted visual artifacts
                float bias;
            };
            
            uniform bool useShadow;
            uniform Shadow shadow0;
            in vec3 shadowPosition0;

            void main()
            {
                vec4 color = vec4(baseColor, 1.0);
                if (useTexture) 
                {
                    color *= texture(textureSampler, UV );
                }
                vec3 calcNormal = normal;
                if (useBumpTexture) 
                {
                    calcNormal += bumpStrength * vec3(texture(bumpTextureSampler, UV));
                }
                // Calculate total effect of lights on color
                vec3 light = vec3(0, 0, 0);""" + self.adding_lights_in_shader_code + """
                color *= vec4(light, 1);
                
                if (useShadow)
                {
                    // determine if surface is facing towards light direction
                    float cosAngle = dot(normalize(normal), -normalize(shadow0.lightDirection));
                    bool facingLight = (cosAngle > 0.01);
                    // convert range [-1, 1] to range [0, 1]
                    // for UV coordinate and depth information
                    vec3 shadowCoord = (shadowPosition0.xyz + 1.0) / 2.0;
                    float closestDistanceToLight = texture(shadow0.depthTextureSampler, shadowCoord.xy).r;
                    float fragmentDistanceToLight = clamp(shadowCoord.z, 0, 1);
                    // determine if fragment lies in shadow of another object
                    bool inShadow = (fragmentDistanceToLight > closestDistanceToLight + shadow0.bias);
                    if (facingLight && inShadow)
                    {
                        float s = 1.0 - shadow0.strength;
                        color *= vec4(s, s, s, 1);
                    }
                }               
                
                fragColor = color;
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
