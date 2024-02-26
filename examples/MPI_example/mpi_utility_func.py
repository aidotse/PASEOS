"""This file contains utility functions for the MPI example to maintain good readbility.

Currently actors cannot be pickled, so we have a simple function to encode them.
"""
from paseos import ActorBuilder, SpacecraftActor
import pykep as pk

earth = pk.planet.jpl_lp("earth")  # define our central body


def _encode_actor(actor):
    """Encode an actor in a list.

    Args:
        actor (SpaceActor): Actor to encode

    Returns:
        actor_data: [name,epoch,pos,velocity]
    """
    data = []
    data.append(actor.name)
    data.append(actor.local_time)
    r, v = actor.get_position_velocity(actor.local_time)
    data.append(r)
    data.append(v)
    return data


def _parse_actor_data(actor_data):
    """Decode an actor from a data list

    Args:
        actor_data (list): [name,epoch,pos,velocity]

    Returns:
        actor: Created actor
    """
    actor = ActorBuilder.get_actor_scaffold(name=actor_data[0], actor_type=SpacecraftActor, epoch=actor_data[1])
    ActorBuilder.set_orbit(
        actor=actor,
        position=actor_data[2],
        velocity=actor_data[3],
        epoch=actor_data[1],
        central_body=earth,
    )
    return actor


def exchange_actors(comm, paseos_instance, local_actor, other_ranks, rank, verbose=False):
    """This function exchanges the states of various actors among all MPI ranks.

    Args:
        comm (MPI_COMM_WORLD): The MPI comm world.
        paseos_instance (PASEOS): The local paseos instance.
        local_actor (SpacecraftActor): The rank's local actor.
        other_ranks (list of int): The indices of the other ranks.
        rank (int): Rank's index.
    """
    if verbose:
        print(f"Rank {rank} starting actor exchange.")
    send_requests = []  # track our send requests
    recv_requests = []  # track our receive request
    paseos_instance.empty_known_actors()  # forget about previously known actors

    # Send local actor to other ranks
    for i in other_ranks:
        actor_data = _encode_actor(local_actor)
        send_requests.append(comm.isend(actor_data, dest=i, tag=int(str(rank) + str(i))))

    # Receive from other ranks
    for i in other_ranks:
        recv_requests.append(comm.irecv(source=i, tag=int(str(i) + str(rank))))

    # Wait for data to arrive
    for recv_request in recv_requests:
        other_actor_data = recv_request.wait()
        other_actor = _parse_actor_data(other_actor_data)
        paseos_instance.add_known_actor(other_actor)

    # Wait until all other ranks have received everything.
    for send_request in send_requests:
        send_request.wait()

    if verbose:
        print(f"Rank {rank} completed actor exchange. Knows {paseos_instance.known_actor_names} now.")
