from typing import List, Tuple
from geometry.geometry import Geometry

def SnookerTableGeometry(sx, sy, sz, obj_groups: List[Tuple[str, List, List, List]]):
    baize_geometry = None
    balls_geometry = None
    cues_geometry = None
    leg_holders_geometry = None
    legs_geometry = None
    pin_geometry = None
    pot_corner_geometry = None
    pot_middle_geometry = None
    cue_box_geometry = None
    cushion_geometry = None

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

        if material_name == "Baize":
            baize_geometry = geometry
        elif material_name == "Balls":
            balls_geometry = geometry
        elif material_name == "Cues":
            cues_geometry = geometry
        elif material_name == "Leg_holders":
            leg_holders_geometry = geometry
        elif material_name == "Legs":
            legs_geometry = geometry
        elif material_name == "Pin":
            pin_geometry = geometry
        elif material_name == "Pot_corner":
            pot_corner_geometry = geometry
        elif material_name == "Pot_middle":
            pot_middle_geometry = geometry
        elif material_name == "cue_box":
            cue_box_geometry = geometry
        elif material_name == "cushion":
            cushion_geometry = geometry

    return baize_geometry, balls_geometry, cues_geometry, leg_holders_geometry, legs_geometry, pin_geometry, pot_corner_geometry, pot_middle_geometry, cue_box_geometry, cushion_geometry 