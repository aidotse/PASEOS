import trimesh


def create_body_mesh(vertices=None, faces=None, scale=1):
    """Creates the mesh of the satellite. If no vertices input is given, it defaults to a cuboid scaled by the
    scale value. The default without scale values is a cube with 1m sides. This uses the python module Trimesh.
    Args:
        vertices (list): List of all vertices of the mesh in terms of distance (in m) from origin of body frame.
            Coordinates of the corners of the object. If not selected, it will default to a cube that can be scaled
            by the scale. Uses Trimesh to create the mesh from this and the list of faces.
        faces (list): List of the indexes of the vertices of a face. This builds the faces of the satellite by
            defining the three vertices to form a triangular face. For a cuboid each face is split into two
            triangles. Uses Trimesh to create the mesh from this and the list of vertices.
        scale (float): Parameter to scale the cuboid by, defaults to 1.

    Returns:
        mesh: Trimesh mesh of the satellite
    """
    if vertices is None:
        # Defines the corners of the mesh, values are in meters, from the origin of the body frame.
        vertices = [
            [-0.5, -0.5, -0.5],
            [-0.5, -0.5, 0.5],
            [-0.5, 0.5, -0.5],
            [-0.5, 0.5, 0.5],
            [0.5, -0.5, -0.5],
            [0.5, -0.5, 0.5],
            [0.5, 0.5, -0.5],
            [0.5, 0.5, 0.5],
        ]
        # List of three vertices to form a triangular face of the satellite.
        # Two triangular faces are used per side of the cuboid.
        faces = [
            [0, 1, 3],
            [0, 3, 2],
            [0, 2, 6],
            [0, 6, 4],
            [1, 5, 3],
            [3, 5, 7],
            [2, 3, 7],
            [2, 7, 6],
            [4, 6, 7],
            [4, 7, 5],
            [0, 4, 1],
            [1, 4, 5],
        ]

    # Set mesh
    mesh = trimesh.Trimesh(vertices, faces).apply_scale(scale)

    return mesh
