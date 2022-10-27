import os
import pykep as pk
import numpy as np
from dotmap import DotMap
from typing import List
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.animation as animation
from matplotlib.artist import Artist
from loguru import logger

from paseos.actors.base_actor import BaseActor
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.ground_station_actor import GroundstationActor
from paseos.paseos import PASEOS
from paseos.visualization.animation import Animation




class SpaceAnimation(Animation):
    """This class visualizes the central body, local actor and known actors over time."""

    path = os.path.join(
        os.path.dirname(__file__) + "/../../resources/", "FontAwesome.otf"
    )
    fp = FontProperties(fname=path)
    symbols = DotMap(
        battery_100="\uf240",
        battery_75="\uf241",
        battery_50="\uf242",
        battery_25="\uf243",
        battery_0="\uf244",
        battery_charging="\uf376",
        communication="\uf1eb",
    )

    def __init__(self, sim: PASEOS) -> None:

        super().__init__(sim)
        logger.trace('Initializing animation')
        # Create list of objects to be plotted
        current_actors = self._make_actor_list(sim)
        self._norm_coeff = self._local_actor._central_body.radius

        local_time_d = self._local_actor.local_time.mjd2000
        for known_actor in current_actors:
            pos, _ = known_actor.get_position_velocity(pk.epoch(local_time_d))
            pos_norm = [x / self._norm_coeff for x in pos]
            self.objects.append(DotMap(actor=known_actor, positions=np.array(pos_norm)))

        # create figure
        self.fig = plt.figure(figsize=plt.figaspect(0.5) * 1.5)
        self.ax = plt.subplot(projection="3d")
        self.ax.set_title(self._sec_to_ddhhmmss(local_time_d / pk.SEC2DAY))
        self.ax.get_xaxis().set_ticks([])
        self.ax.get_yaxis().set_ticks([])
        self.ax.get_zaxis().set_ticks([])
        self.n_trajectory = 50  # how many samples from histories to visualize
        self._textbox_offset = 0.25  # how many samples from histories to visualize

        # plot the objects
        self._plot_central_body()
        self._plot_actors()

        plt.show(block=False)

    def _plot_central_body(self) -> None:
        """Plot the central object as a sphere of radius 1
        Args:
            None
        Returns:
            None
        """
        central_body = self._local_actor._central_body
        central_body.radius

        u, v = np.mgrid[0 : 2 * np.pi : 30j, 0 : np.pi : 20j]
        x = np.cos(u) * np.sin(v)
        y = np.sin(u) * np.sin(v)
        z = np.cos(v)
        self.ax.plot_surface(x, y, z, color="grey")

    def _populate_textbox(self, actor: BaseActor) -> str:
        """Extracts information from an actor and builds a string
        Args:
            actor (BaseActor): an actor
        Returns:
            str: text to populate the textbox.
        """
        if isinstance(actor, SpacecraftActor):
            battery_level = actor.battery_level_ratio * 100
            if battery_level < 12.5:
                battery_icon = self.symbols.battery_0
            elif battery_level < 37.5:
                battery_icon = self.symbols.battery_25
            elif battery_level < 62.5:
                battery_icon = self.symbols.battery_50
            elif battery_level < 87.5:
                battery_icon = self.symbols.battery_75
            else:
                battery_icon = self.symbols.battery_100
            
            # TODO: enable both text and icons in textbox
            #info_str = f"{actor.name} \n{battery_level:.0f}% {battery_icon} \n{self.symbols.communication}"
            
            # no icons included
            info_str = f"{actor.name} \nbat: {battery_level:.0f}%" 
            for name in actor.communication_devices.keys():
                info = actor.communication_devices[name]
                info_str += f'\n{name}: {info.bandwidth_in_kbps} kbps'
        

        elif isinstance(actor, GroundstationActor):
            # TODO: implement textbox for groundstation
            pass

        return info_str

    def _plot_actors(self) -> None:
        """Plots all the actors
        Args:
            None
        Returns:
            None
        """
        for obj in self.objects:
            data = obj.positions
            if data.ndim == 1:
                data = data[..., np.newaxis].T
            n_points = np.minimum(data.shape[0], self.n_trajectory)
        
            if "plot" in obj.keys():
                # spacecraft and ground stations behave differently and are plotted separately
                if isinstance(obj.actor, SpacecraftActor):
                    # update trajectory
                    obj.plot.trajectory.set_data(data[-n_points:, :2].T)
                    obj.plot.trajectory.set_3d_properties(data[-n_points:, 2].T)

                    # update satellite position
                    obj.plot.point.set_data_3d(data[-1, :])

                    # update text box
                    actor_info = self._populate_textbox(obj.actor)
                    obj.plot.text.set_position_3d(data[-1, :] + self._textbox_offset)
                    obj.plot.text.set_text(actor_info)
                    
                elif isinstance(obj.actor, GroundstationActor):
                    # TODO: implement update of groundstation object
                    pass
            else:
                if isinstance(obj.actor, SpacecraftActor):
                    trajectory = self.ax.plot3D(data[0, 0], data[0, 1], data[0, 2])[0]
                    obj.plot.trajectory = trajectory
                    obj.plot.point = self.ax.plot(
                        data[0, 0],
                        data[0, 1],
                        data[0, 2],
                        "*",
                        color=trajectory.get_color(),
                    )[0]
                    actor_info = self._populate_textbox(obj.actor)
                    obj.plot.text = self.ax.text(
                        data[0, 0] + self._textbox_offset,
                        data[0, 1] + self._textbox_offset,
                        data[0, 2] + self._textbox_offset,
                        actor_info,
                        #fontproperties=self.fp,
                        bbox=dict(facecolor="white"),
                        verticalalignment="bottom",
                        clip_on=True,
                    )
                    
                    
                elif isinstance(obj.actor, GroundstationActor):
                    # TODO: implement initial rendering of groundstation object
                    pass

        self.ax.set_box_aspect(
            (
                np.ptp(self.ax.get_xlim()),
                np.ptp(self.ax.get_ylim()),
                np.ptp(self.ax.get_zlim()),
            )
        )

    def _make_actor_list(self, sim: PASEOS) -> List[BaseActor]:
        """Arranges all actors (including the local) into a list
        Args:
        sim: simulation object.
        Returns:
            List[BaseActor]
        """
        if len(sim.known_actors) > 0:
            current_actors = [sim.local_actor] + list(sim.known_actors.values())
        else:
            current_actors = [sim.local_actor]
        return current_actors

    def _update(self, sim: PASEOS) -> None:
        """Updates the animation with the current actor information
        Args:
        sim (PASEOS): simulation object.
        Returns:
            None
        """
        logger.debug('Updating animation')
        local_time_d = self._local_actor.local_time.mjd2000
        # NOTE: the actors in sim are unique so make use of sets
        objects_in_plot = set([obj.actor for obj in self.objects])
        current_actors = set(self._make_actor_list(sim))

        objects_to_remove = list(
            objects_in_plot.difference(current_actors)
        )  # if objects do not exist in known actors, remove from plot next update.
        objects_to_add = list(
            current_actors.difference(objects_in_plot)
        )  # if known_actor does not exist in objects, add the actors and update in plot

        plot_objects_to_remove = [
            x for x in self.objects if x.actor in objects_to_remove
        ]
        for obj in plot_objects_to_remove:
            obj.plot.trajectory.remove()
            obj.plot.point.remove()
            obj.plot.text.remove()

        self.objects = [x for x in self.objects if x.actor not in objects_to_remove]

        for obj_to_add in objects_to_add:
            self.objects.append(DotMap(actor=obj_to_add))

        # update positions of objects
        for known_actor in current_actors:
            for obj in self.objects:
                if obj.actor == known_actor:
                    pos, _ = known_actor.get_position_velocity(pk.epoch(local_time_d))
                    pos_norm = [x / self._norm_coeff for x in pos]
                    if "positions" in obj:
                        obj.positions = np.vstack((obj.positions, pos_norm))
                    else:
                        obj.positions = np.array(pos_norm)
        self._plot_actors()

        # Step through trajectories to find max and min values in each direction
        coords_max = [0, 0, 0]
        coords_min = [0, 0, 0]
        for obj in self.objects:
            coords_max = np.maximum(obj.positions.max(axis=0), coords_max)
            coords_min = np.minimum(obj.positions.min(axis=0), coords_min)
        self.ax.set_xlim(coords_min[0], coords_max[0])
        self.ax.set_ylim(coords_min[1], coords_max[1])
        self.ax.set_zlim(coords_min[2], coords_max[2])

        self.ax.set_title(self._sec_to_ddhhmmss(local_time_d / pk.SEC2DAY))
        
        return

    def _animate(self, sim: PASEOS, dt: float) -> List[Artist]:
        """Advances the time of sim, updates the plot, and returns the axis objects
        Args:
        sim (PASEOS): simulation object.
        dt: size of time step
        Returns:
            List[Artist]: list of Artist objects
        """
        sim.advance_time(dt)
        self._update(sim)
        return self.ax.get_children()
    
    def _animation_wrapper(self, step:int, sim:PASEOS, dt:float) -> List[Artist]:
        """wrapper to allow for frame numbers from animation
        Args:
        steps: current frame number of the animation
        sim (PASEOS): simulation object.
        dt: size of time step
        Returns:
            List[Artist]: list of Artist objects
        """
        return self._animate(sim, dt)

    def animate(self, sim: PASEOS,  dt: float, steps: int=1, name:str=None, save_file:bool=False) -> None:
        """Animates paseos for a given number of steps with dt in each step. If save=True, result is saved into "{name}.mp4"
        Args:
        sim (PASEOS): simulation object.
        dt(float): size of time step
        steps (int): number of steps to animate
        name (str): filename to save animation 
        save_file (bool): should animation be saved
        Returns:
            None
        """
        if save_file is False:
            self._animate(sim, dt)
        else:
            anim = animation.FuncAnimation(self.fig, self._animation_wrapper, frames=steps, fargs=(sim,dt,), interval=20, blit=True,)
            anim.save(f"{name}.mp4", writer="ffmpeg", fps=10)
