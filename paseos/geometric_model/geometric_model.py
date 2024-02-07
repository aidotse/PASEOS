from loguru import logger
import trimesh


class GeometricModel:
    """This model describes the geometry of the spacecraft
    Currently it assumes the spacecraft to be a cuboid shape, with width, length and height
    """

    _actor = None
    _actor_mesh = None
    _actor_center_of_gravity = None
    _actor_moment_of_inertia = None

    def __init__(self, local_actor, actor_mass, vertices=None, faces=None, scale=1) -> None:
        """Describes the geometry of the spacecraft and outputs relevant parameters related to the spacecraft body.
        If no vertices or faces are provided, defaults to a cube with unit length sides. This is in the spacecraft body
        reference frame and can be transformed to the inertial/PASEOS reference frame by using the transformations in the
        attitude model.

        Args:
            local_actor (SpacecraftActor): Actor to model.
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

        self._actor = local_actor
        self._actor_mass = actor_mass
        self.vertices = vertices
        self.faces = faces
        self.scale = scale

    def set_mesh(self):
        """Creates the mesh of the satellite. If no vertices input is given, it defaults to a cuboid scaled by the
        scale value. The default without scale values is a cube with 1m sides. This uses the python module Trimesh.

        Returns:
            mesh: Trimesh mesh of the satellite
        """
        if self.vertices is None:
            # Defines the corners of the mesh, values are in meters, from the origin of the body frame.
            self.vertices = [
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
            self.faces = [
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

        mesh = trimesh.Trimesh(self.vertices, self.faces)
        # Scales the mesh by the scale factor.
        self._actor_mesh = mesh.apply_scale(self.scale)
        return self._actor_mesh

    @property
    def find_moment_of_inertia(self):
        """Gives the moment of inertia of the actor, assuming constant density.

        Returns:
            np.array: Mass moments of inertia for the actor

        I is the moment of inertia, in the form of [[Ixx Ixy Ixz]
                                                    [Iyx Iyy Iyx]
                                                    [Izx Izy Izz]]
        """
        self._actor_moment_of_inertia = self._actor_mesh.moment_inertia
        return self._actor_moment_of_inertia

    def find_center_of_gravity(self):
        """Gives the volumetric center of mass of the actor.

        Returns:
            np.array: Coordinates of the center of gravity of the mesh.
        """
        self._actor_center_of_gravity = self._actor_mesh.center_mass
        return self._actor_center_of_gravity
