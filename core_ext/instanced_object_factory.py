class InstancedObjectFactory:
    """Factory class for creating instanced meshes with shared geometry and material"""
    def __init__(self, geometry, material):
        self.geometry = geometry
        self.material = material
        self.positions = []
        self.rotations = []
        
    def add_instance(self, position, rotation=[0, 0, 0]):
        """Add a new instance with given position and rotation"""
        self.positions.append(position)
        self.rotations.append(rotation)
        
    def add_instances(self, positions, rotations=None):
        """Add multiple instances at once"""
        if rotations is None:
            rotations = [[0, 0, 0]] * len(positions)
        self.positions.extend(positions)
        self.rotations.extend(rotations)
        
    def build_mesh(self, mesh_creator):
        """Create the final instanced mesh using the provided creator function"""
        return mesh_creator(self.geometry, self.material, self.positions, self.rotations)
        
    def clear(self):
        """Clear all instances"""
        self.positions.clear()
        self.rotations.clear() 