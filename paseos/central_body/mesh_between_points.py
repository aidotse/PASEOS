import numpy as np
from loguru import logger


def mesh_between_points(
    point_1: np.array, point_2: np.array, mesh_vertices: np.array, mesh_triangles: np.array
) -> bool:
    """Checks whether the mesh is between the two points using ray-triangle
    intersection with Möller-Trumbore algorithm.

    Args:
        point_1 (np.array): First point
        point_2 (np.array): Second point
        mesh_vertices (np.array): Vertices of the mesh
        mesh_triangles (np.array): Triangles of the mesh

    Returns:
        bool: True if the mesh is between the two points
    """
    logger.trace("Computing if mesh lies between points: " + str(point_1) + " " + str(point_2))

    # Compute line between points
    direction = point_2 - point_1
    direction = direction / np.linalg.norm(direction)

    intersect_point = None

    # Iterate over triangles to find any intersection
    for t in mesh_triangles:
        intersect, intersect_t = _rays_triangle_intersect(
            point_1, direction, mesh_vertices[t[0]], mesh_vertices[t[1]], mesh_vertices[t[2]]
        )
        # If / When found break the loop
        if intersect:
            intersect_point = point_1 + intersect_t * direction
            break

    # Check that the computed intersection is actually on the linesegment not infinite line
    if intersect_point is None:
        return False
    # True if intersection and between the points, otherwise not on the line segment
    return np.linalg.norm(intersect_point - point_1) < np.linalg.norm(point_2 - point_1)


def _rays_triangle_intersect(ray_o, ray_d, v0, v1, v2):
    """Möller-Trumbore intersection algorithm (vectorized).

    Computes whether a ray intersects a triangle.

    Taken from https://github.com/gomezzz/geodesyNets/blob/master/gravann/util/_hulls.py

    Args:
        ray_o (3D np.array): origin of the ray.
        ray_d (3D np.array): direction of the ray.
        v0, v1, v2 (3D np.array): triangle vertices

    Returns:
        boolean value if the intersection exist (includes the edges) and the t value
        of the intersection. (0 if no intersection)

    See: https://en.wikipedia.org/wiki/M%C3%B6ller%E2%80%93Trumbore_intersection_algorithm
    """
    if ray_o.shape != (3,):
        raise ValueError("Shape f ray_o input should be (3,)")
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(ray_d, edge2)

    a = np.dot(edge1, h)

    if a < 0.000001 and a > -0.000001:
        return False, 0

    f = 1.0 / a
    s = ray_o - v0
    u = np.dot(s, h) * f

    if u < 0 or u > 1:
        return False, 0

    q = np.cross(s, edge1)
    v = np.dot(ray_d, q) * f

    if v < 0 or u + v > 1:
        return False, 0

    t = f * np.dot(edge2, q)

    return t > 0, t
