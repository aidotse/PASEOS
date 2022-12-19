# PASEOS

PASEOS - PAseos Simulates the Environment for Operating multiple Spacecraft

![Alt Text](sat_gif.gif)

Disclaimer: This project is currently under development. Use at your own risk.

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About the Project</a></li>
    <li><a href="#paseos-space-environment-simulation">PASEOS space environment simulation</a></li>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#examples">Examples</a></li>
    <ul>
    <li><a href="#create-a-paseos-actor">Create a PASEOS actor</a></li>
    <li><a href="#set-an-orbit-for-a-paseos-spacecraftactor">Set an orbit for a PASEOS SpacecraftActor</a></li>
    <li><a href="#how-to-instantiate-paseos">How to instantiate PASEOS</a></li>
    <li><a href="#how-to-add-a-communication-device">How to add a communication device</a></li>
    <li><a href="#how-to-add-a-power-device">How to add a power device</a></li>
    <li><a href="#adding-other-actors-to-paseos">Adding other actors to PASEOS</a></li>
    <li><a href="#how-to-register-an-activity">How to register an activity</a></li>
    <li><a href="#faster-than-real-time-execution">Faster than real-time execution</a></li>
    <li><a href="#visualising-paseos">Visualising PASEOS</a></li>
    </ul>
    <li><a href="#system-design-of-paseos">System Design of PASEOS</a></li>
    <li><a href="#glossary">Glossary</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About the project

PASEOS is a `Python` module that simulates the environment to operate multiple specraft. In particular, PASEOS offers the user some utilities to run their own [activities](#activity) by taking into account both operational and onboard (e.g. limited-power-budget, radiation and thermal effects) constraints. <br> PASEOS is designed to be:

- **open-source**: the source code of PASEOS is available under a GPL license.
- **fully-decentralised**: one instance of `PASEOS` shall be executed in every node, i.e. individual spacecraft (actor), of the emulated spacecraft. Each instance of `PASEOS` is responsible for handling the user [activities](#activity) executed on that node (the local actor) while keeping track of the status of the other nodes. In this way, the design of `PASEOS` is completely decentralised and independent of the number of nodes of the constellation. Because of that, both single-node and multi-node scenarios are possibles.
- **application-agnostic**: each user operation that has to be executed on a node is modelled as an [activity](#activity). The user is only required to provide the code to run and some parameters (e.g., power-consumption) for each [activity](#activity). Thus, activities can be any code the user wants to simulate running on a spacecraft and thereby `PASEOS` is completely application-agnostic. Conceivable applications range from modelling constellation to training machine learning methods.

<br> The project is being developed by [$\Phi$-lab@Sweden](https://www.ai.se/en/data-factory/f-lab-sweden) in the frame of a collaboration between [AI Sweden](https://www.ai.se/en/) and the [European Space Agency](https://www.esa.int/) to explore distributed edge learning for space applications. For more information on `PASEOS` and $\Phi$-lab@Sweden, please take a look at the recording of the $\Phi$-lab@Sweden [kick-off event](https://www.youtube.com/watch?v=KuFRCcNxLgo&t=2365s).

## PASEOS space environment simulation

![Alt Text](PASEOS_constraints.png)
PASEOS allow simulating the effect of onboard and operational constraints on user-registered [activities](#activity). The image above showcases the different phenomena considered (or to be implemented) in PASEOS.

## Installation

`pip` and `conda` support will follow in the near future.

For now, first of all clone the [GitHub](https://github.com/aidotse/PASEOS.git) repository as follows ([Git](https://git-scm.com/) required):

```
git clone https://github.com/aidotse/PASEOS.git
```

To install PASEOS you can use [conda](https://docs.conda.io/en/latest/) as follows:

```
cd PASEOS
conda env create -f environment.yml
```

This will create a new conda environment called `PASEOS` and install the required software packages.
To activate the new environment, you can use:

```
conda activate paseos
```

Alternatively, you install PASEOS by using [PyPy](https://www.pypy.org/) as follows:

```
cd PASEOS
pip install -e .
```

## Examples

![Alt Text](PASEOS_Example.png)

The next examples will introduce you to the use of `PASEOS` through the case study shown in the image above. This is a general scenario made of two [SpacecraftActors](#spacecraftactor) (`SatelliteA` and `SatelliteB`) and one [GroundstationActor](#ground-stationactor). You can assume to execute the following code snippets onboard `SatelliteA`. In general, there is no a theoretical limitation on the number of satellites or ground stations used. Single-device simulations can be also implemented.

### Create a PASEOS actor

The code snippet below shows how to create a `PASEOS` [actor](#actor) named **SatA** of type [SpacecraftActor](#spacecraftactor). [pykep](https://esa.github.io/pykep/) is used to define the satellite [epoch](<https://en.wikipedia.org/wiki/Epoch_(astronomy)>) in format [mjd2000](https://en.wikipedia.org/wiki/Julian_day) format. <br>
[actors](#actor) are created by using an `ActorBuilder`. The latter is used to define the [actor](#actor) `scaffold` that includes the [actor](#actor) minimal properties. In this way, [actors](#actor) are build in a modular fashion that enable their use also for non-space applications.

```py
import pykep as pk
import paseos
from paseos import ActorBuilder, SpacecraftActor
# Define an actor of type SpacecraftActor of name SatA
satA = ActorBuilder.get_actor_scaffold(name="SatA",
                                       actor_type=SpacecraftActor,
                                       epoch=pk.epoch(0))
```

### Set an orbit for a PASEOS SpacecraftActor

Once you have defined a [SpacecraftActor](#spacecraftactor), you can assign a [Keplerian orbit](https://en.wikipedia.org/wiki/Kepler_orbit) to it. To this aim, you need to define central body the [SpacecraftActor](#spacecraftactor) is orbiting around and specify its position and velocity (in the central body's [inertial frame](https://en.wikipedia.org/wiki/Inertial_frame_of_reference) and an epoch. In this case, `satA` central body is `Earth`.

```py

# Define the central body as Earth by using pykep APIs.
earth = pk.planet.jpl_lp("earth")

# Let's set the SpacecraftActor orbit.
ActorBuilder.set_orbit(actor=satA,
                       position=[10000000, 0, 0],
                       velocity=[0, 8000.0, 0],
                       epoch=pk.epoch(0), central_body=earth)
```

### How to add a communication device

The following code snippet shows how to add a communication device to `SatA`. A communication device is needed to model the communication between [SpacecraftActors] (#spacecraftactor) or a [SpacecraftActor](#spacecraftactor) and [GroundstationActor](#ground-stationactor). Currently, given the maximum transmission data-rate of a communication device, PASEOS calculates the maximum data that can be transmitted by multiplying the transmission data-rate by the length of the communication window. The latter, is calculated by taking into account the period for which two actors are in line-of-sight.

```py
ActorBuilder.add_comm_device(actor=satA,
                             device_name="my_communication_device", # Communication device name
                             bandwidth_in_kbps=100000) # Bandwidth in kbps.
```

### How to add a power device

The following code snippet shows how to add a power device to `satA`. At the moment, only battery device is supported.
Moreover, PASEOS assumes that battery will be charged by solar panels, which will provide energy thanks to the incoming solar radiation when the spacecraft is not in eclipse.

```py
ActorBuilder.set_power_devices(actor=satA,
                               battery_level_in_Ws=100, # Battery level at the start of the simulation in Ws
                               max_battery_level_in_Ws=2000, # Max battery level in Ws
                               charging_rate_in_W=10) # Charging rate in W
```

## Thermal Modelling
To model thermal constraints on spacecraft we utilize a model inspired by the one-node model described in [Martínez - Spacecraft Thermal Modelling and Test](http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling%20and%20Testing.pdf). Thus, we model the change in temperature as 

$mc \, \frac{dT}{dt} = \dot{Q}_{solar} + \dot{Q}_{albedo} + \dot{Q}_{central_body_IR} - \dot{Q}_{dissipated} + \dot{Q}_{activity}.$

This means your spacecraft will heat up due to being in sunlight, albedo reflections, infrared radiation emitted by the central body as well as due to power consumption of activities. It will cool down due to heat dissipation.

The model is only available for a [SpacecraftActor](#spacecraftactor) and (like all the physical models) only evaluated for the [local actor](#local-actor).

The following parameters have to be specified for this:
* Spacecraft mass [kg], initial temperature [K], emissive area (for heat disspiation) and thermal capacity [J / (kg * K)]
* Spacecraft absorptance of Sun light, infrared light. [0 to 1]
* Spacecraft area [m^2] facing Sun and central body, respectively
* Solar irradiance in this orbit [W] (defaults to 1360W)
* Central body surface temperature [k] (defaults to 288K)
* Central body emissivity and reflectance [0 to 1] (defaults to 0.6 and 0.3)
* Ratio of power converted to heat (defaults to 0.5)

To use it, simply equip your [SpacecraftActor](#spacecraftactor) with a thermal model with:

```py
from paseos import SpacecraftActor, ActorBuilder
my_actor = ActorBuilder.get_actor_scaffold("my_actor", SpacecraftActor, pk.epoch(0))
ActorBuilder.set_thermal_model(
    actor=my_actor,
    actor_mass=50.0, # Setting mass to 50kg
    actor_initial_temperature_in_K=273.15, # Setting initialtemperature to 0°C
    actor_sun_absorptance=1.0, # Depending on material, define absorptance
    actor_infrared_absorptance=1.0, # Depending on material, define absorptance
    actor_sun_facing_area=1.0, # Area in m2
    actor_central_body_facing_area=1.0, # Area in m2
    actor_emissive_area=1.0, # Area in m2
    actor_thermal_capacity=1000, # Capacity in J / (kg * K)
    # ... leaving out default valued parameters, see docs for details
)
```

The model is evaluated automatically during [activities](#activity). You can check the spacecraft temperature with:

```py
print(my_actor.temperature)
```

### How to instantiate PASEOS

We will now show how to create an instance of PASEOS. In this case, `satA` is the [local actor](#local-actor).

```py
sim = paseos.init_sim(satA) # initialize PASEOS simulation.
```

### Adding other actors to PASEOS

Once you have instantiated a PASEOS simulation, you can add other spacecraft or ground stations as actors to the simulation. Let's start with `SatB`.

```py

satB = ActorBuilder.get_actor_scaffold(name="SatB",
                                      actor_type=SpacecraftActor,
                                      epoch=pk.epoch(0))

#Lets set the SpacecraftActor orbit.
ActorBuilder.set_orbit(actor=satB,
                       position=[-10000000, 0, 0],
                       velocity=[0, -8000.0, 0],
                       epoch=today, central_body=earth)

# Adding SatB to PASEOS.
sim.add_known_actor(satB)
```

You can similarly add a ground station actor (`grndStation`) at coordinates `(lat,lon)=(79.002723, 14.642972)` and elevation of 0 m. <br> You cannot add a power device and an orbit to a `GroundstationActor`.

```py

#Create GroundstationActor
grndStation = GroundstationActor(name="grndStation", epoch=today)

#Set the ground station at lat long 79.002723 / 14.642972 and ith elevation 0m
ActorBuilder.set_ground_station_location(grndStation, latitude=79.002723, longitude=14.642972, elevation=0)

# Adding SatB to PASEOS.
sim.add_known_actor(grndStation)
```

### How to register an activity

PASEOS enables the user to register their [activities](#activity) that will be executed on the `local actor`. <br>
To register an activity, it is first necessary to define an asynchronous [activity function](#activity-function). The following code snippet shows how to create an [activity function](#activity-function) `activity_function_A` that takes an input argument and returns its value multiplied by two. Then it waits 0.1 s before concluding the activity. <br>
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

### Faster than real-time execution

In some cases, you may be interested to simulate your spacecraft operating for an extended period. By default, PASEOS operates in real-time, thus this would take a lot of time. However, you can increase the rate of time passing (i.e. the spacecraft moving, power being charged / consumed etc.) using the `time_multiplier` parameter. Set it is as follows when initializing PASEOS.

```py

cfg = load_default_cfg() # loading cfg to modify defaults
cfg.sim.time_multiplier = 10 # setting the parameter so that in 1s real time, paseos models 10s having passed
paseos_instance = paseos.init_sim(my_local_actor, cfg) # initialize paseos instance

```

### Writing simulation results to a file

To evaluate your results, you will likely want to track the operational parameters, such as actor battery status, currently running activitiy etc. of actors over the course of your simulation. By default, PASEOS will log the current actor status every 10 seconds, however you can change that rate. You can save the current log to a \*.csv file at any point.

```py
cfg = load_default_cfg() # loading cfg to modify defaults
cfg.io.logging_interval = 0.25  # log every 0.25 seconds
paseos_instance = paseos.init_sim(my_local_actor, cfg) # initialize paseos instance

# Performing activities, running the simulation (...)

sim.save_status_log_csv("output.csv")
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

- ### Activity

  An activity is the abstraction that PASEOS uses to keep track of specific actions performed by a [SpacecraftActor](#spacecraftactor) upon a request from the user. To register an activity, an user shall first create an [activity function](#activity-function), which describes the operation to be performed, and provide information on the power-consumption due to the activity execution. <br>PASEOSis responsible for the execution of the activity and for updating the system status depending on the effects of the activity (e.g., by discharging they satellite battery).<br>
  When registering an activity, the user can specify a [constraint-function](#constraint-function) to specify constraints to be met during the execution of the activity and an an [on termination](#on-termination) function to specify additional operations to performed by PASEOS on termination of the activity function.

- ### Activity function

  User-defined function emulating any operation to be executed in a PASEOS a [SpacecraftActor](#spacecraftactor). Activity functions are necessayr to register [activities](#activity). Activity functions might include data transmission, house-keeping operations, onboard data acquisition and processing, and others.

- ### Actor

  Since PASEOS is fully-decentralised, each node of a PASEOS constellation shall run an instance of PASEOS modelling all the nodes of that constellation. The abstraction of a constellation node inside a PASEOS instace is a PASEOS `actor`.

- ### Constraint-function

  A constraint function is an asynchronous function that can be used by the PASEOS user to specify some constraints that shall be met during the execution of an activity.

- ### Ground stationActor

  `PASEOS actor` emulating a ground station.

- ### Local actor

  The `local actor` in a PASEOS instance is the `actor` that models the behavior and the status of the node that runs that PASEOS instance.

- ### On-termination function

  A on-termination function is an asynchronous function that can be used by the PASEOS user to specify some operations to be executed on termination of predefied PASEOS user.

- ### SpacecraftActor
  `PASEOS actor` emulating a spacecraft or a satellite.

## Contributing

The `PASEOS` project is open to contributions. To contribute, you can open an [issue](https://github.com/gomezzz/MSMatch/issues) to report a bug or to request a new feature. If you prefer discussing new ideas and applications, you can contact us via email (please, refer to [Contact](#contact)).
To contribute, please proceed as follow:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the GPL-3.0 License.

## Contact

Created by $\Phi$[-lab@Sweden](https://www.ai.se/en/data-factory/f-lab-sweden).

- Pablo Gómez - pablo.gomez at esa.int, pablo.gomez at ai.se
- Gabriele Meoni - gabriele.meoni at esa.int, gabriele.meoni at ai.se
- Johan Östman - johan.ostman at ai.se
- Vinutha Magal Shreenath - vinutha at ai.se
