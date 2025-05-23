import OpenGL.GL as GL

from core_ext.object3d import Object3D


class Mesh(Object3D):
    """
    Contains geometric data that specifies vertex-related properties and material data
    that specifies the general appearance of the object
    """
    def __init__(self, geometry, material):
        super().__init__()
        self._geometry = geometry
        self._material = material
        # Should this object be rendered?
        self._visible = True
        # Set up associations between attributes stored in geometry
        # and shader program stored in material
        self._vao_ref = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self._vao_ref)
        for variable_name, attribute_object in geometry.attribute_dict.items():
            attribute_object.associate_variable(material.program_ref, variable_name)
        # Unbind this vertex array object
        GL.glBindVertexArray(0)

    @property
    def geometry(self):
        return self._geometry

    @property
    def material(self):
        return self._material
    
    
    @material.setter
    def material(self, new_material):
        self._material = new_material
        # If necessary, update any associations between geometry and the new material
        GL.glBindVertexArray(self._vao_ref)
        for variable_name, attribute_object in self._geometry.attribute_dict.items():
            attribute_object.associate_variable(new_material.program_ref, variable_name)
        GL.glBindVertexArray(0)

    @property
    def vao_ref(self):
        return self._vao_ref

    @property
    def visible(self):
        return self._visible
