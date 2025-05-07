from geometry.geometry import Geometry

class WireframeGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, obj_data=()):
        super().__init__()

        all_vertices = []
        all_uvs = []
        all_normals = []

        for material_name, positions, uvs, normals in obj_data:
            all_vertices.extend(positions)
            all_uvs.extend(uvs)
            all_normals.extend(normals)

        # Single uniform color (e.g., yellow)
        color = [1.0, 1.0, 0.0]
        color_data = [color] * len(all_vertices)

        self.add_attribute("vec3", "vertexPosition", all_vertices)
        self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", all_uvs)
        self.add_attribute("vec3", "vertexNormal", all_normals)
        self.add_attribute("vec3", "faceNormal", all_normals)
        self.count_vertices()