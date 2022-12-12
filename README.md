# PASEOS
PASEOS - PAseos Simulates the Environment for Operating multiple Spacecraft 

![Alt Text](sat_gif.gif)

This project is currently under development. Use at your own risk. :)

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About the Project</a></li>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#examples">Examaples</a></li>
    <ul>
    <li><a href="#create-a-paseos-actor">Create a PASEOS actor</a></li>
    <li><a href="#set-an-orbit-for-a-paseos-spacecraftactor">Set an orbit for a PASEOS SpacecraftActor</a></li>
    <li><a href="#how-to-instantiate-paseos">How to instantiate PASEOS</a></li>
    <li><a href="#how-to-add-a-communication-device">How to add a communication device</a></li>
    <li><a href="#how-to-add-a-power-device">How to add a power device</a></li>
    <li><a href="#adding-other-actors-to-paseos">Adding other actors to PASEOS</a></li>
    <li><a href="#how-to-register-an-activity">How to register an activity</a></li>
    <li><a href="#visualising-paseos">Visualising PASEOS</a></li>
    </ul>
    <li><a href="#paseos-space-environment-simulation">PASEOS space environment simulation</a></li>
    <li><a href="#system-design-of-paseos">System Design of PASEOS</a></li>
    <li><a href="#glossary">Glossary</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About the project

`PASEOS` is a `Python` module that simulates the environment to operate multiple specraft. In particular, `PASEOS` offers the user some utilities to run their own [activities](#activity) by taking into account both operational and onboard (e.g. limited-power-budget, radiation and thermal effects) constraints. <br>  `PASEOS` is designed to:

* **open-source**: the source of `PASEOS` are available at this [GitHub](https://github.com/aidotse/PASEOS.git) repository. 
* **fully-decentralised**:  one instance of `PASEOS` shall be executed in every node of the emulated spacecraft swarm. Each instance of `PASEOS` is responsible of the user [activities](#activity) executed in that node while keeping track of the status of the other nodes. In this way, the design of `PASEOS` is completely decentralised and independent on the number of nodes of the constellation. Because of that, both single-node and multi-node scenarios are possibles.
* **application-agnostic**: each user operation that has to be executed in a node is modelled as an [activity](#activity). The user is required to provide the code and some parameters (e.g., power-consumption) for each [activity](#activity) that shall be executed in a `PASEOS` node. In this way, `PASEOS` is completely application-agnostic.

<br> The project was developed by [$\Phi$-lab@Sweden](https://www.ai.se/en/data-factory/f-lab-sweden) in the frame of the collbaboration between [AI Sweden](https://www.ai.se/en/) and the [European Space Agency](https://www.esa.int/) to explore distributed edge learning for space applications. For more information on `PASEOS` and $\Phi$-lab@Sweden, please take a look at the recordings on the $\Phi$-lab@Sweden [kick-off event](https://www.youtube.com/watch?v=KuFRCcNxLgo&t=2365s).

## Installation
First of all clone the [GitHub](https://github.com/aidotse/PASEOS.git) repository as follows ([Git](https://git-scm.com/) required):

```
git clone https://github.com/aidotse/PASEOS.git
```

To install `PASEOS` you can use [conda](https://docs.conda.io/en/latest/) as follow:

```
cd PASEOS
conda env create -f environment.yml
```
This will create a new conda environment called ```paseos``` and install the required software packages.
To activate the new environment, you can use:

```
conda activate paseos
```

Alternatively, you install `PASEOS` by using [PyPy](https://www.pypy.org/) as follows:

```
cd PASEOS
pip install -e .
```

## Contributing
The ```PASEOS``` project is open to contributions. To contribute, you can open an [issue](https://github.com/gomezzz/MSMatch/issues) to report a bug or to request a new feature. If you prefer discussing new ideas and applications, you can contact us via email (please, refer to [Contact](#contact)).
To contribute, please proceed as follow:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## PASEOS space environment simulation
![Alt Text](PASEOS_constraints.png)
`PASEOS` allow simulating the effect of onboard and operational constraints on user-registered [activities](#activity). The image above showcases the different phenomena considered (or to be implemented) in `PASEOS`.

## Examples
![Alt Text](PASEOS_example.png)

The next examples will introduce you to the use of `PASEOS` through the case study shown in the image above. This is a general scenario made of two [SpacecraftActors](#spacecraftactor) (`SatelliteA` and `SatelliteB`) and one [GroundstationActor](#ground-stationactor). You can assume to execute the following code snippets onboard `SatelliteA`. In general, there is no a theoretical limitation on the number of satellites or ground stations used. Single-device simulations can be also implemented.

### Create a PASEOS actor
The code snippet below shows how to create a `PASEOS` [actor](#actor) named **SatA** of type [SpacecraftActor](#spacecraftactor). [pykep](https://esa.github.io/pykep/) is used to define the satellite [epoch](https://en.wikipedia.org/wiki/Epoch_(astronomy)) in format [mjd2000](https://en.wikipedia.org/wiki/Julian_day) format. 
 
```py 
import pykep as pk
import paseos
from paseos import ActorBuilder, SpacecraftActor
# Define an actor pf type SpacecraftActor of name my_first_actor
SatA = ActorBuilder.get_actor_scaffold(name="SatA", actor_type=SpacecraftActor, epoch=pk.epoch(0))
```

### Set an orbit for a PASEOS SpacecraftActor
Once you have defined a [SpacecraftActor](#spacecraftactor), you can assign an orbit to it. To this aim, you need to specify the position and the velocity of the spacecraft with respect to an [Earth-centered_inertial](https://en.wikipedia.org/wiki/Earth-centered_inertial) reference frame and a date. In this case, `satA` central body is `Earth`.

```py 
#Let's define the date of today (27/10/2022) as pk.epoch
#please, refer to https://esa.github.io/pykep/documentation/core.html#pykep.epoch
#Using this will overwrite the previously set epoch
today = pk.epoch_from_string('2022-10-27 12:00:00.000')

# Define the central body as Earth by using pykep APIs.
earth = pk.planet.jpl_lp("earth")

#Actor position [m] and velocity [m/s]
satA_position=[-6912275.638799771, -1753638.1454079857, 734768.7737737056]
satA_velocity=[-1015.9539197253205, 894.2090554272667, -7334.877725365646]

#Lets set the SpacecraftActor orbit.
ActorBuilder.set_orbit(actor=SatA, 
                       position=satA_position, 
                       velocity=satA_velocity, 
                       epoch=today, central_body=earth)
```
### How to add a communication device
The following code snippet shows how to add a communication device to `SatA`. 

```py
ActorBuilder.add_comm_device(actor=SatA, 
                             device_name="my_communication_device", # Communication device name
                             bandwidth_in_kbps=100000) # Bandwidth in kbps. 
```

### How to add a power device
The following code snippet shows how to add a power device to `SatA`. 

```py
ActorBuilder.set_power_devices(actor=SatA, 
                               battery_level_in_Ws=100, # Battery level at the start of the simulation in Ws
                               max_battery_level_in_Ws=2000, # Max battery level in Ws
                               charging_rate_in_W=10) # Charging rate in W
```

### How to instantiate PASEOS
We will now show how to create an instance of `PASEOS`. As previously described, you can image to instantiate this simulation onboard `SatA`. In this case, `SatA` is the [local actor](#local-actor).
```py 
cfg=load_default_cfg() # loading cfg to modify defaults
cfg.sim.start_time=today.mjd2000 * pk.DAY2SEC # convert epoch to seconds.
sim = paseos.init_sim(local_actor, cfg) # initialize PASEOS simulation.
```
### Adding other actors to PASEOS
Once you have instantiated a `PASEOS` simulation, yu can can now add the other satellites as actors to the simulation. Let's start with `SatB`. The actor `SatB` will be placed in the same orbit of `SatA`, with 180 degree phase difference and moving in the opposite direction, to emulate the behaviour of `SatelliteA` and `SatelliteB` in the image above.

```py 

satB = ActorBuilder.get_actor_scaffold(name="SatB", actor_type=SpacecraftActor, epoch=pk.epoch(0))

#Actor position [m] and velocity [m/s]
satB_position=[6903448.606615168, 1765298.4893694564, -804473.4057320235]
satB_velocity=[1070.5779954343407, -879.0974287694968, 7326.987310088407]

#Lets set the SpacecraftActor orbit.
ActorBuilder.set_orbit(actor=SatB, 
                       position=satB_position, 
                       velocity=satB_velocity, 
                       epoch=today, central_body=earth)

# Adding SatB to PASEOS.  
sim.add_known_actor(satB)                     
```

Let's add now the ground station actor (`grndStation`) at coordinates `(lat,lon)=(79.002723, 14.642972)` and elevation of 0 m.

```py 

#Create GroundstationActor
grndStation = GroundstationActor(name="grndStation", epoch=today)

#Set the ground station at lat long 79.002723 / 14.642972 and ith elevation 0m
ActorBuilder.set_ground_station_location(grndStation, latitude=79.002723, longitude=14.642972, elevation=0)

# Adding SatB to PASEOS.  
sim.add_known_actor(grndStation)    
```
### How to register an activity
`PASEOS` will enable the user to register their [activities](#activity) that will be executed on the `local actor`. In this case, since we are assuming to run this instance of `PASEOS` on `SatelliteA` that is modelled through the [SpacecraftActor](#spacecraftactor) `satA`, the latter is the `local actor`. <br> 
To register an activity, it is first necessary to define an asynchronous [activity function](#activity-function). The following code snippet shows how to create an [activity function](#activity-function) `activity_function_A` that takes the as input an argument and returns it's values multiplied by two. Then it waits 0.1 s before concluding the activity. <br>
Please, notice that the output value is placed in `args[1][0]`, which is returned as reference.

```py 

#Activity function
async def activity_function_A(args):
  activity_in=args[0]
  activity_out=activity_in * 2
  args[1][0]=activity_out
  await asyncio.sleep(0.1) #Await is needed inside an async function.
```

It is possible to associate a [constraint function](#constraint-function) with each [activity](#activity) to ensure that some particular constraints are met during the [activity](#activity) execution. When constraints are not met, the activity is interrupted. 
The next code snippet shows how to create a [constraint function](#constraint-function) that returns `True` when its input is positive and `False` otherwise.

```py 

#Activity function
async def constraint_function_A(args):
  constraint_in=args[0]
  return (constraint_in > 0)

```

It is also possible to define an [on termination](#on-termination-function) to perform some specific operations when on termination of the [activity](#activity). The next code snippet shows how to create an [on termination](#on-termination-function) that prints "activity ended" on termination. 

```py 

#Activity function
async def on_termination_function_A(args):
  print("Satellite ready to acquire data again.")

```

Finally, you can register an activity `activity_A` by using the previously defined [activity function](#activity-function), [constraint function](#constraint-function) and [on termination](#on-termination-function). The user needs to specify the power consumption associated with the activity. 

```py 

# Register an activity that emulate event detection
sim.register_activity(
    "activity_A", 
    activity_function=activity_function_A, 
    power_consumption_in_watt=10, 
    constraint_function=constraint_function_A,
    on_termination_function=on_termination_function_A
)

```



### Visualising PASEOS
Navigate to paseos/visualization to find a jupyter notebook containing examples of how to visualize PASEOS.
Visualization can be done in interactive mode or as an animation that is saved to disc.
In the figure below, Earth is visualized in the center as a blue sphere with different spacecraft in orbit.
Each spacecraft has a name and if provided, a battery level and a communications device.
The local device is illustrated with white text.
In the upper-right corner, the status of the communication link between each spacecraft is shown.
Finally, the time in the lower left and lower right corners correspond to the epoch and the PASEOS local simulation time.

<p align="center">
  <a href="https://github.com/aidotse/PASEOS/">
    <img src="resources/images/animation.png" alt="Scheme"  width="900" height="500">
  </a>
  <p align="center">
    Snapshot of PASEOS visualization
  </p>
</p>

## System Design of PASEOS

<p align="center">
  <a href="https://github.com/aidotse/PASEOS/">
    <img src="resources/images/datastructure.svg" alt="Scheme"  width="910" height="459">
  </a>
  <p align="center">
    Description of PASEOS data structure
  </p>
</p>

<p align="center">
  <a href="https://github.com/aidotse/PASEOS/">
    <img src="resources/images/flowchart.svg" alt="Scheme"  width="910" height="459">
  </a>
  <p align="center">
    Description of PASEOS workflow on an individual device
  </p>
</p>

## Glossary
* ### Activity
  An activity is the abstraction that `PASEOS` uses to keep track of specific actions performed by a [SpacecraftActor](#spacecraftactor) upon a request from the user. To register an activity, an user shall first create an [activity function](#activity-function), which describes the operation to be performed, and provide information on the power-consumption due to the activity execution. <br>`PASEOS`is responsible for the execution of the activity and for updating the system status depending on the effects of the activity (e.g., by discharging they satellite battery).<br>
  When registering an activity, the user can specify a [constraint-function](#constraint-function) to specify constraints to be met during the execution of the activity and an an [on termination](#on-termination) function to specify additional operations to performed by `PASEOS` on termination of the activity function.


* ### Activity function
  User-defined function emulating any operation to be executed in a `PASEOS` a [SpacecraftActor](#spacecraftactor). Activity functions are necessayr to register [activities](#activity). Activity functions might include data transmission, house-keeping operations, onboard data acquisition and processing, and others.

* ### Actor
  Since `PASEOS` is fully-decentralised, each node of a `PASEOS` constellation shall run an instance of `PASEOS` modelling all the nodes of  that constellation.  The abstraction of a constellation node inside a `PASEOS` instace is a `PASEOS` `actor`. 

* ### Constraint-function
  A constraint function is an asynchronous function that can be used by the `PASEOS` user to specify some constraints that shall be met during the execution of an activity.

* ### Ground stationActor
  `PASEOS actor` emulating a ground station.  

* ### Local actor
  The `local actor` in a `PASEOS` instance is the `actor` that models the behavior and the status of the node that runs that `PASEOS` instance.

* ### On-termination function
  A on-termination function is an asynchronous function that can be used by the `PASEOS` user to specify some operations to be executed on termination of predefied `PASEOS` user.

* ### SpacecraftActor
  `PASEOS actor` emulating a spacecraft or a satellite. 




## Contact
Created by [$\Phi$-lab@Sweden](https://www.ai.se/en/data-factory/f-lab-sweden).

* Pablo Gómez - pablo.gomez at esa.int, pablo.gomez at ai.se
* Gabriele Meoni - gabriele.meoni at esa.int, gabriele.meoni at ai.se
* Johan Östman - johan.ostman at ai.se
* Vinutha Magal Shreenath - vinutha at ai.se