from typing import List, Tuple
from geometry.geometry import Geometry

def JukeboxGeometry(sx, sy, sz, obj_groups: List[Tuple[str, List, List, List]]):
    wood_geometry = None
    neon_geometry = None
    metal_geometry = None
    red_geometry = None
    metalmesh_geometry = None
    selectcoin_geometry = None
    selectsong_geometry = None
    vinyl_geometry = None
    songs1_geometry = None
    songs2_geometry = None
    glass_geometry = None

    for material_name, group_vertices, group_uvs, group_normals in obj_groups:
        geometry = Geometry()
        geometry.add_attribute("vec3", "vertexPosition", group_vertices)

        if not group_uvs or len(group_uvs) != len(group_vertices):
            group_uvs = [[0.0, 0.0] for _ in group_vertices]

        # Handle UV mapping for selectsong and songlist geometries
        if material_name in ["selectsong", "songlist1", "songlist2"]:
            # Get the bounds of the UV coordinates
            u_coords = [uv[0] for uv in group_uvs]
            v_coords = [uv[1] for uv in group_uvs]
            min_u, max_u = min(u_coords), max(u_coords)
            min_v, max_v = min(v_coords), max(v_coords)

            # Normalize UV coordinates to fit within [0,1] range
            group_uvs = [[
                (uv[0] - min_u) / (max_u - min_u) if (max_u - min_u) != 0 else 0.0,
                1.0 - (uv[1] - min_v) / (max_v - min_v) if (max_v - min_v) != 0 else 0.0
            ] for uv in group_uvs]

        geometry.add_attribute("vec2", "vertexUV", group_uvs)

        if not group_normals or len(group_normals) != len(group_vertices):
            normal = [0.0, 0.0, 1.0]
            group_normals = [normal] * len(group_vertices)
        geometry.add_attribute("vec3", "vertexNormal", group_normals)
        geometry.add_attribute("vec3", "faceNormal", group_normals)

        geometry.count_vertices()

        if material_name == "wood":
            wood_geometry = geometry
        elif material_name == "neon":
            neon_geometry = geometry
        elif material_name == "metal":
            metal_geometry = geometry
        elif material_name == "red":
            red_geometry = geometry
        elif material_name == "metalmesh":
            metalmesh_geometry = geometry
        elif material_name == "selectcoin":
            selectcoin_geometry = geometry
        elif material_name == "selectsong":
            selectsong_geometry = geometry
        elif material_name == "vinyl":
            vinyl_geometry = geometry
        elif material_name == "songlist1":
            songs1_geometry = geometry
        elif material_name == "songlist2":
            songs2_geometry = geometry
        elif material_name == "glass":
            glass_geometry = geometry

    return wood_geometry, neon_geometry, metal_geometry, red_geometry, metalmesh_geometry, selectcoin_geometry, selectsong_geometry, vinyl_geometry, songs1_geometry, songs2_geometry, glass_geometry 
