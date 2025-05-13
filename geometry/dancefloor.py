from typing import List, Tuple
from geometry.geometry import Geometry

def DanceFloorGeometry(sx, sy, sz, obj_groups: List[Tuple[str, List, List, List]]):
    color1_geometry = None
    color2_geometry = None


    for material_name, group_vertices, group_uvs, group_normals in obj_groups:
        geometry = Geometry()
        geometry.add_attribute("vec3", "vertexPosition", group_vertices)

        if not group_uvs or len(group_uvs) != len(group_vertices):
            group_uvs = [[0.0, 0.0] for _ in group_vertices]
        geometry.add_attribute("vec2", "vertexUV", group_uvs)

        if not group_normals or len(group_normals) != len(group_vertices):
            normal = [0.0, 0.0, 1.0]
            group_normals = [normal] * len(group_vertices)
        geometry.add_attribute("vec3", "vertexNormal", group_normals)
        geometry.add_attribute("vec3", "faceNormal", group_normals)

        geometry.count_vertices()

        if material_name == "color1":
            color1_geometry = geometry
        elif material_name == "color2":
            color2_geometry = geometry


    return color1_geometry, color2_geometry