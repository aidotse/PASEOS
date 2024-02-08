import csv

import matplotlib.pyplot as plt
import pykep as pk
from dotmap import DotMap
from loguru import logger

from paseos.actors.base_actor import BaseActor


class OperationsMonitor:
    """This class is used to track actor status and activities over time."""

    def __init__(self, actor_name):
        """Initializes the OperationsMonitor

        Args:
            actor_name (str): Name of the local actor.
        """
        logger.trace("Initializing OperationsMonitor for " + actor_name)
        self._actor_name = actor_name
        self._log = DotMap(_dynamic=False)
        self._log.timesteps = []
        self._log.current_activity = []
        self._log.temperature = []
        self._log.state_of_charge = []
        self._log.is_in_eclipse = []
        self._log.known_actors = []
        self._log.position = []
        self._log.velocity = []
        self._log.custom_properties = DotMap(_dynamic=False)

    def __getitem__(self, item):
        """Get a logged attributes values.

        Args:
            item (str): Name of item. Available are "timesteps","current_activity","state_of_charge",
            "is_in_eclipse","known_actors","position","velocity","temperature"
        """
        assert item in (
            list(self._log.keys()) + list(self._log.custom_properties.keys())
        ), f"Untracked quantity. Available are {self._log.keys() + self._log.custom_properties.keys()}"
        if item in self._log.custom_properties.keys():
            return self._log.custom_properties[item]
        return self._log[item]

    def plot(self, item):
        assert item in (
            list(self._log.keys()) + list(self._log.custom_properties.keys())
        ), f"Untracked quantity. Available are {self._log.keys() + self._log.custom_properties.keys()}"
        if item in self._log.custom_properties.keys():
            values = self._log.custom_properties[item]
        else:
            values = self._log[item]
        plt.Figure(figsize=(6, 2), dpi=150)
        t = self._log.timesteps
        plt.plot(t, values)
        plt.xlabel("Time [s]")
        plt.ylabel(item.replace("_", " "))

    def log(self, local_actor: BaseActor, known_actors: list, communication_links=None):
        """Log the current time step.

        Args:
            local_actor (BaseActor): The local actors whose status we are monitoring.
            known_actors (list): List of names of the known actors.
            communication_links: List of communication links.
        """
        logger.trace("Logging iteration")
        assert local_actor.name == self._actor_name, (
            "Expected actor's name was" + self._actor_name
        )
        self._log.timesteps.append(local_actor.local_time.mjd2000 * pk.DAY2SEC)
        self._log.current_activity.append(local_actor.current_activity)
        self._log.position.append(local_actor._previous_position)
        self._log.velocity.append(local_actor._previous_velocity)
        self._log.known_actors.append(known_actors)
        if local_actor.has_thermal_model:
            self._log.temperature.append(local_actor.temperature_in_K)
        else:
            self._log.temperature.append(-1)
        if local_actor.has_power_model:
            self._log.state_of_charge.append(local_actor.state_of_charge)
        else:
            self._log.state_of_charge.append(1.0)

        if local_actor._previous_eclipse_status is None:
            self._log.is_in_eclipse.append(False)
        else:
            self._log.is_in_eclipse.append(local_actor._previous_eclipse_status)

        if communication_links is not None:
            for link in communication_links:
                link.save_state()

        # Track all custom properties
        for key, value in local_actor.custom_properties.items():
            if key not in self._log.custom_properties.keys():
                logger.info(f"Property {key} was not tracked beforem, adding now.")
                self._log.custom_properties[key] = []
            self._log.custom_properties[key].append(value)

    def save_to_csv(self, filename):
        """Write the created log file to a csv file.

        Args:
            filename (str): File to store the log in.
        """
        logger.trace("Writing status log file to " + filename)
        with open(filename, "w", newline="") as f:
            w = csv.DictWriter(
                f, list(self._log.keys()) + list(self._log.custom_properties.keys())
            )
            w.writeheader()
            for i in range(len(self._log.timesteps)):
                row = {
                    "timesteps": self._log.timesteps[i],
                    "current_activity": self._log.current_activity[i],
                    "position": self._log.position[i],
                    "velocity": self._log.velocity[i],
                    "known_actors": self._log.known_actors[i],
                    "temperature": self._log.temperature[i],
                    "state_of_charge": self._log.state_of_charge[i],
                    "is_in_eclipse": self._log.is_in_eclipse[i],
                }
                # Append custom properties
                for key, value in self._log.custom_properties.items():
                    # If quantity only started to be track during simulation
                    # we need to fill the previous values with None
                    if len(value) < len(self._log.timesteps):
                        # Add None to the beginning of the list
                        if i < len(self._log.timesteps) - len(value):
                            row[key] = None
                        else:
                            row[key] = value[
                                i - (len(self._log.timesteps) - len(value))
                            ]
                    else:
                        row[key] = value[i]

                w.writerow(row)
