def my_obj_reader(filename):
    vertices = []
    uvs = []
    normals = []
    materials = {}
    current_material = None

    with open(filename, 'r') as in_file:
        for line in in_file:
            tokens = line.strip().split()
            if not tokens:
                continue

            if tokens[0] == 'v':
                vertices.append([float(v) for v in tokens[1:]])
            elif tokens[0] == 'vt':
                uvs.append([float(v) for v in tokens[1:]])
            elif tokens[0] == 'vn':
                normals.append([float(v) for v in tokens[1:]])
            elif tokens[0] == 'usemtl':
                current_material = tokens[1]
                if current_material not in materials:
                    materials[current_material] = {"positions": [], "uvs": [], "normals": []}
            elif tokens[0] == 'f':
                face = [value.split('/') for value in tokens[1:]]
                for vertex_info in face:
                    v_idx = int(vertex_info[0]) - 1
                    t_idx = int(vertex_info[1]) - 1 if len(vertex_info) > 1 and vertex_info[1] else None
                    n_idx = int(vertex_info[2]) - 1 if len(vertex_info) > 2 and vertex_info[2] else None

                    materials[current_material]["positions"].append(vertices[v_idx])
                    if t_idx is not None and t_idx < len(uvs):
                        materials[current_material]["uvs"].append(uvs[t_idx])
                    else:
                        materials[current_material]["uvs"].append([0.0, 0.0])
                    if n_idx is not None and n_idx < len(normals):
                        materials[current_material]["normals"].append(normals[n_idx])
                    else:
                        materials[current_material]["normals"].append([0.0, 0.0, 1.0])  # fallback

    # Return (material_name, positions, uvs, normals)
    return [
        (mat_name, mat_data["positions"], mat_data["uvs"], mat_data["normals"])
        for mat_name, mat_data in materials.items()
    ]