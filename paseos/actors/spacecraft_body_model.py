from loguru import logger
import numpy as np
import trimesh


class SpacecraftBodyModel:
    """This model describes the geometry of the spacecraft
    Currently it assumes the spacecraft to be a cuboid shape, with width, length and height
    """

    _body_mesh = None
    _body_center_of_gravity = None
    _body_moment_of_inertia = None

    def __init__(self, actor_mass, vertices=None, faces=None, scale=1) -> None:
        """Describes the geometry of the spacecraft and outputs relevant parameters related to the spacecraft body.
        If no vertices or faces are provided, defaults to a cube with unit length sides. This is in the spacecraft body
        reference frame and can be transformed to the inertial/PASEOS reference frame by using the transformations in the
        attitude model.

        Args:
            actor_mass (float): Actor's mass in kg.
            vertices (list): List of all vertices of the mesh in terms of distance (in m) from origin of body frame.
                Coordinates of the corners of the object. If not selected, it will default to a cube that can be scaled
                by the scale. Uses Trimesh to create the mesh from this and the list of faces.
            faces (list): List of the indexes of the vertices of a face. This builds the faces of the satellite by
                defining the three vertices to form a triangular face. For a cuboid each face is split into two
                triangles. Uses Trimesh to create the mesh from this and the list of vertices.
            scale (float): Parameter to scale the cuboid by, defaults to 1.
        """
        logger.trace("Initializing cuboid geometrical model.")

        self._body_mass = actor_mass
        self._body_mesh = self._create_body_mesh(
            vertices=vertices, faces=faces, scale=scale
        )
        self._body_moment_of_inertia = self._body_mesh.moment_inertia * self._body_mass
        self._body_center_of_gravity = self._body_mesh.center_mass

    def _create_body_mesh(self, vertices=None, faces=None, scale=1):
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

        else:
            assert (
                len(np.asarray(vertices).shape) == 2
                and np.asarray(vertices).shape[1] == 3
            ), "Vertices shall be [N, 3] shaped."
            assert np.asarray(faces).shape[0] < len(
                vertices
            ), "All the entries in faces are < len(vertices)"

        # Create mesh
        logger.trace("Creating the spacecraft body mesh.")
        mesh = trimesh.Trimesh(vertices, faces).apply_scale(scale)

        return mesh

    @property
    def body_mesh(self) -> np.array:
        """Gives the mesh of the satellite.

        Returns:
            np.array: Mesh of the satellite.
        """
        return self._body_mesh

    @property
    def body_moment_of_inertia(self) -> np.array:
        """Gives the moment of inertia of the actor, assuming constant density.

        Returns:
            np.array: Mass moments of inertia for the actor

        I is the moment of inertia, in the form of [[Ixx Ixy Ixz]
                                                    [Iyx Iyy Iyx]
                                                    [Izx Izy Izz]]
        """
        return self._body_moment_of_inertia

    @property
    def body_center_of_gravity(self) -> np.array:
        """Gives the volumetric center of mass of the actor.

        Returns:
            np.array: Coordinates of the center of gravity of the mesh.
        """
        return self._body_center_of_gravity
