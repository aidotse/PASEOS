""" This example showcases how you can run PASEOS on a high-performance computing infrastructure
using MPI (see also https://mpi4py.readthedocs.io/en/stable/tutorial.html).

Please run the example with mpiexec -n 4 python mpi_example.py

In the example, we model four satellites in low-Earth orbit which are only very infrequently in
line of sight of each other. For simplicity, the modelled task here will be to count the number of
window encounters for each satellite. 

N.B. There are some simplifications in this example. Running this on a larger scale
you would want to minimize communications between ranks more. For clarity, we stay simple.
For details on the MPI parts also have a look at the mpi_utility_func.py in this folder.

Let's start by importing the required packages, in addition to PASEOS' requirements 
we also need mpi4py (install via conda install mpi4py -c conda-forge )
"""

import sys
import time

sys.path.append("..")
sys.path.append("../..")

from mpi4py import MPI

import pykep as pk
import paseos
from paseos import ActorBuilder, SpacecraftActor
from utils.get_constellation import get_constellation
from mpi_utility_func import exchange_actors

# Use this to turn on/off printing of individual windows and communications between ranks.
SHOW_ALL_WINDOWS = True
SHOW_ALL_COMMS = False

############ MPI INIT #############
# Now we will initialize MPI, for more details please refer to the mpi4py docs.
# In MPI "rank" indicates the index of the compute node (so 0-3 in our example).
comm = MPI.COMM_WORLD
assert (
    comm.Get_size() == 4
), "Please run the example with mpiexec -n 4 python mpi_example.py"
rank = comm.Get_rank()
other_ranks = [x for x in range(4) if x != rank]
print(f"Started rank {rank}, other ranks are {other_ranks}")
start = time.time()

############ ORBIT INIT #############
# Let's give each rank a slightly different orbit.
# (We use a utility function for constellation for this purpose)
altitude = (250 + rank * 20) * 1000  # altitude above the Earth's ground [m]
inclination = rank * 50.0  # inclination of the orbit
nPlanes = 1  # the number of orbital planes
nSats = 1  # the number of satellites per orbital plane
t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")  # the starting date of our simulation

# Compute the orbit of each rank
planet_list, sats_pos_and_v, _ = get_constellation(
    altitude, inclination, nSats, nPlanes, t0, verbose=False
)
print(
    f"Rank {rank} set up its orbit with altitude={altitude}m and inclination={inclination}deg"
)

############ PASEOS INIT #############
# We will now initialize the PASEOS instance on each rank
earth = pk.planet.jpl_lp("earth")  # define our central body
pos, v = sats_pos_and_v[0]  # get our position and velocity

# Create the local actor, name will be the rank
local_actor = ActorBuilder.get_actor_scaffold(
    name="Sat_" + str(rank), actor_type=SpacecraftActor, epoch=t0
)
ActorBuilder.set_orbit(
    actor=local_actor, position=pos, velocity=v, epoch=t0, central_body=earth
)

paseos_instance = paseos.init_sim(local_actor=local_actor)
print(f"Rank {rank} set up its PASEOS instance for its local actor {local_actor}")

# Let us exchange actors with the other ranks now as a sanity check
# This should give you a terminal output like
# "Rank 0 completed actor exchange. Knows dict_keys(['Sat_1', 'Sat_2', 'Sat_3']) now."
exchange_actors(comm, paseos_instance, local_actor, other_ranks, rank, verbose=True)


############ SIMULATION SETUP #############
# Now, we will propagate each rank for 2.5 min simulation time unless it encounters another
# actor on its way (according to the regularly information about their trajectories)

# Let's define the variable to track the actors we see
total_seen_actors = 0

# We will (ab)use PASEOS constraint function to track all the actors
# we see in an evaluation window. Turn on verbose if you want to see each window
def constraint_func(verbose=SHOW_ALL_WINDOWS):
    # For simplicity we use a global variable here
    global total_seen_actors
    local_t = paseos_instance.local_actor.local_time

    # Count when we see an actor and forget about it for the rest of this window
    # (It will be readded during actor exchange, but we should not count the same actor
    # again if we still see it a few seconds later)
    known_actors = paseos_instance.known_actors.values()
    actors_to_remove = (
        []
    )  # we track keys to remove so the size doesn't change in iteration
    for actor in known_actors:
        if paseos_instance.local_actor.is_in_line_of_sight(actor, local_t):
            if verbose:
                print(f"Rank {rank} can see {actor} at {local_t}.")
            actors_to_remove.append(actor.name)
            total_seen_actors += 1

    # Forget about actors we already met
    for actor_to_remove in actors_to_remove:
        paseos_instance.remove_known_actor(actor_to_remove)

    return True


############ SIMULATION MAIN LOOP #############
# We advance the simulation an hour to move satellites away from their initial positions.
paseos_instance.advance_time(3600, current_power_consumption_in_W=0)

simulation_time = 1.0 * 3600  # simulation interval in seconds
t = 0  # starting time in seconds
timestep = 150  # how often we synchronize actors' trajectories

# Run until end of simulation
while t <= simulation_time:

    # Advance the simulation state of this rank
    # Note how we pass the "constraint_func" to tell paseos
    # to track windows
    paseos_instance.advance_time(
        timestep, current_power_consumption_in_W=0, constraint_function=constraint_func
    )
    t += timestep

    # Exchange actors between all ranks
    exchange_actors(
        comm, paseos_instance, local_actor, other_ranks, rank, verbose=SHOW_ALL_COMMS
    )

# Wait until all ranks finished
print(f"Rank {rank} finished the simulation. Waiting for all to finish.")

# Synchronize between and print some stats.
comm.Barrier()
end = time.time()
sys.stdout.flush()

if rank == 0:
    print()
    print(f"########## Simulation completed ###########")
    print(
        f"Simulation ran {end-start:.2f}s to simulate {simulation_time:.2f}s. {simulation_time / (end-start):.2f}x real-time."
    )
sys.stdout.flush()
comm.Barrier()
print(f"Rank {rank} saw a total of {total_seen_actors} actors during the simulation.")
