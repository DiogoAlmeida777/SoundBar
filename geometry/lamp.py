from typing import List, Tuple
from geometry.geometry import Geometry

def LampGeometry(sx, sy, sz, obj_groups: List[Tuple[str, List, List, List]]):
    base_geometry = None
    lamp_geometry = None
    lampshade_geometry = None
    switch_geometry = None


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

        if material_name == "base":
            base_geometry = geometry
        elif material_name == "lamp":
            lamp_geometry = geometry
        elif material_name == "lampshade":
            lampshade_geometry = geometry
        elif material_name == "switch":
            switch_geometry = geometry

    return base_geometry, lamp_geometry, lampshade_geometry, switch_geometry