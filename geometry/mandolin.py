from geometry.geometry import Geometry


class MandolinGeometry(Geometry):
    def __init__(self, width=1, height=1, depth=1, obj_data=()):
        super().__init__()

        verticesHarmonica, uv_coords = obj_data  # Unpack vertex positions and UVs

        # Define four distinct colors
        colors = [
            [1, 1, 0],
            [0.5, 1, 0],
            [1, 0.5, 0],
            [0.5, 0.5, 0],
        ]

        # Assign colors based on vertex groups
        num_vertices = len(verticesHarmonica)
        color_data = [colors[i % 4] for i in range(num_vertices)]

        # Store attributes in the mesh
        self.add_attribute("vec3", "vertexPosition", verticesHarmonica)
        self.add_attribute("vec3", "vertexColor", color_data)
        self.add_attribute("vec2", "vertexUV", uv_coords)
        self.count_vertices()