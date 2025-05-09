from typing import List, Tuple
from core_ext.object3d import Object3D
from core_ext.mesh import Mesh
from core_ext.texture import Texture
from geometry.geometry import Geometry
from material.lambert import LambertMaterial
from material.surface import SurfaceMaterial  # fallback magenta
from material.phong import PhongMaterial

def BarGeometry(sx, sy, sz, obj_groups: List[Tuple[str, List, List, List]]):
    wall_geometry = None
    floor_geometry = None
    roof_geometry = None
    door_geometry = None

    # Color textures
    texture_map = {
        "Wall": Texture("images/brick.jpg"),
        "Floor": Texture("images/rubber_tiles.jpg"),
        "Roof": Texture("images/tiles.jpg"),
        "Door": Texture("images/door_texture.jpg")
    }

    # Bump textures (optional, can be same or different)
    bump_map = {
        "Wall": Texture("images/brick-normal-map.png"),
        "Floor": Texture("images/rubber_tiles_bump.png"),
        "Roof": Texture("images/tiles_bump.png"),
        "Door": Texture("images/door_bump.png")
    }

    tiling_map = {
        "Wall": 16.0,
        "Floor": 16.0,
        "Roof": 16.0,
    }

    for material_name, group_vertices, group_uvs, group_normals in obj_groups:
        geometry = Geometry()
        geometry.add_attribute("vec3", "vertexPosition", group_vertices)

        if not group_uvs or len(group_uvs) != len(group_vertices):
            print(f" UVs ausentes ou inválidas em {material_name}, aplicando fallback.")
            group_uvs = [[0.0, 0.0] for _ in group_vertices]

        if material_name == "Wall":
            group_uvs = [[uv[1], 1.0 - uv[0]] for uv in group_uvs]
            # Apply tiling for walls
            group_uvs = [[uv[0] * 16.0, uv[1] * 16.0] for uv in group_uvs]
        elif material_name == "Door":
            u_coords = [uv[0] for uv in group_uvs]
            v_coords = [uv[1] for uv in group_uvs]
            min_u, max_u = min(u_coords), max(u_coords)
            min_v, max_v = min(v_coords), max(v_coords)

            group_uvs = [[
                (uv[0] - min_u) / (max_u - min_u) if (max_u - min_u) != 0 else 0.0,
                1.0 - (uv[1] - min_v) / (max_v - min_v) if (max_v - min_v) != 0 else 0.0
            ] for uv in group_uvs]
        elif material_name in ["Floor", "Roof"]:
            # Apply tiling for floor and roof
            group_uvs = [[uv[0] * 16.0, uv[1] * 16.0] for uv in group_uvs]

        geometry.add_attribute("vec2", "vertexUV", group_uvs)
        geometry.add_attribute("vec3", "vertexNormal", group_normals)
        geometry.add_attribute("vec3", "faceNormal", group_normals)
        geometry.count_vertices()

        if material_name == "Wall":
            wall_geometry = geometry
        elif material_name == "Floor":
            floor_geometry = geometry
        elif material_name == "Roof":
            roof_geometry = geometry
        elif material_name == "Door":
            door_geometry = geometry

    return wall_geometry, floor_geometry, roof_geometry, door_geometry