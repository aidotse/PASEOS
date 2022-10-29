import pykep as pk
import numpy as np
from dotmap import DotMap
from typing import List
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.artist import Artist
from matplotlib.colors import LinearSegmentedColormap
from loguru import logger

from paseos.actors.base_actor import BaseActor
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.ground_station_actor import GroundstationActor
from paseos.paseos import PASEOS
from paseos.visualization.animation import Animation


class SpaceAnimation(Animation):
    """This class visualizes the central body, local actor and known actors over time."""

    def __init__(self, sim: PASEOS, n_trajectory: int = 50) -> None:
        """Initialize the space animation object

        Args:
            sim (PASEOS): simulation object
            n_trajectory (int): number of samples in tail of actor
        """
        super().__init__(sim)
        logger.trace("Initializing animation")
        # Create list of objects to be plotted
        current_actors = self._make_actor_list(sim)
        self._norm_coeff = self._local_actor._central_body.radius

        local_time_d = self._local_actor.local_time.mjd2000
        for known_actor in current_actors:
            pos, _ = known_actor.get_position_velocity(pk.epoch(local_time_d))
            pos_norm = [x / self._norm_coeff for x in pos]
            self.objects.append(DotMap(actor=known_actor, positions=np.array(pos_norm)))

        # create figures
        # Create figure for 3d animation
        self.fig = plt.figure(figsize=plt.figaspect(0.5) * 1.5)
        self.ax_3d = plt.subplot(1, 2, 1, projection="3d")
        self.ax_3d.set_title(self._sec_to_ddhhmmss(local_time_d / pk.SEC2DAY))
        self.ax_3d.get_xaxis().set_ticks([])
        self.ax_3d.get_yaxis().set_ticks([])
        self.ax_3d.get_zaxis().set_ticks([])
        self.n_trajectory = n_trajectory  # how many samples from histories to visualize
        self._textbox_offset = 0.25  # how many samples from histories to visualize

        # Create figure for LOS
        self.ax_los = plt.subplot(1, 2, 2)
        xaxis = np.arange(len(current_actors))
        self.ax_los.set_xticks(xaxis)
        self.ax_los.set_yticks(xaxis)
        self.ax_los.set_xticklabels(current_actors)
        self.ax_los.set_yticklabels(current_actors)

        # plot the objects
        self._plot_central_body()
        self._plot_actors()
        los_matrix = self._get_los_matrix(current_actors)
        self._plot_los(los_matrix)

        plt.ion()
        plt.show()

    def _plot_central_body(self) -> None:
        """Plot the central object as a sphere of radius 1"""
        central_body = self._local_actor._central_body
        central_body.radius

        u, v = np.mgrid[0 : 2 * np.pi : 30j, 0 : np.pi : 20j]
        x = np.cos(u) * np.sin(v)
        y = np.sin(u) * np.sin(v)
        z = np.cos(v)
        self.ax_3d.plot_surface(x, y, z, color="grey")

    def _get_los_matrix(self, current_actors: List[BaseActor]) -> np.ndarray:
        """Compute line-of-sight (LOS) between all actors

        Args:
            current_actors (List[BaseActor]): All actors in the simulation

        Returns:
            np.ndarray: LOS matrix with nonzero elements if actors are in LOS
        """
        local_time = self._local_actor.local_time
        los_matrix = np.identity(len(current_actors))

        for i, a1 in enumerate(current_actors):
            for j, a2 in enumerate(current_actors[i + 1 :]):
                if a1.is_in_line_of_sight(a2, local_time) is True:
                    los_matrix[i, j + i + 1] = 1.0

        # make los_matrix symmetric with diagonal entries equal to 0.5 to make colorbar nicer
        los_matrix = los_matrix + los_matrix.T - 1.5 * np.diag(np.diag(los_matrix))
        return los_matrix

    def _populate_textbox(self, actor: BaseActor) -> str:
        """Extracts information from an actor and builds a string

        Args:
            actor (BaseActor): an actor

        Returns:
            str: text to populate the textbox.
        """
        info_str = f"{actor.name}"
        if isinstance(actor, SpacecraftActor):
            # TODO: enable both text and icons in textbox

            if actor.battery_level_in_Ws is not None:
                battery_level = actor.battery_level_ratio * 100
                info_str += f"\nbat: {battery_level:.0f}%"

            for name in actor.communication_devices.keys():
                info = actor.communication_devices[name]
                info_str += f"\n{name}: {info.bandwidth_in_kbps} kbps"

        elif isinstance(actor, GroundstationActor):
            # TODO: implement textbox for groundstation
            pass

        return info_str

    def _plot_los(self, los_matrix: np.ndarray) -> None:
        """Plot the LOS links in a heat map

        Args:
            los_matrix (np.ndarray): matrix telling what satellites can see each other.
        """
        # Create new colormap, with white for two
        colors = [(255, 0, 0), (255, 255, 255), (0, 255, 0)]
        new_map = LinearSegmentedColormap.from_list("new_map", colors, N=3)
        self._los_plot = self.ax_los.matshow(los_matrix, cmap=new_map, vmin=0, vmax=1)
        cbar = self.fig.colorbar(self._los_plot, ticks=[0, 1])
        cbar.ax.set_yticklabels(["No LOS", "LOS"])

    def _plot_actors(self) -> None:
        """Plots all the actors"""
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
                    trajectory = self.ax_3d.plot3D(data[0, 0], data[0, 1], data[0, 2])[
                        0
                    ]
                    obj.plot.trajectory = trajectory
                    obj.plot.point = self.ax_3d.plot(
                        data[0, 0],
                        data[0, 1],
                        data[0, 2],
                        "*",
                        color=trajectory.get_color(),
                    )[0]
                    actor_info = self._populate_textbox(obj.actor)
                    obj.plot.text = self.ax_3d.text(
                        data[0, 0] + self._textbox_offset,
                        data[0, 1] + self._textbox_offset,
                        data[0, 2] + self._textbox_offset,
                        actor_info,
                        bbox=dict(facecolor="white"),
                        verticalalignment="bottom",
                        clip_on=True,
                    )

                elif isinstance(obj.actor, GroundstationActor):
                    # TODO: implement initial rendering of groundstation object
                    pass

        self.ax_3d.set_box_aspect(
            (
                np.ptp(self.ax_3d.get_xlim()),
                np.ptp(self.ax_3d.get_ylim()),
                np.ptp(self.ax_3d.get_zlim()),
            )
        )

    def _make_actor_list(self, sim: PASEOS) -> List[BaseActor]:
        """Arranges all actors (including the local) into a list

        Args:
            sim (PASEOS): simulation object.

        Returns:
            List[BaseActor]: list of all the actors known to local actor (including itself)
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
        """
        logger.trace("Updating animation")
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
                        if obj.positions.shape[0] > self.n_trajectory:
                            obj.positions = np.roll(obj.positions, shift=-1, axis=0)
                            obj.positions[-1, :] = pos_norm
                        else:
                            obj.positions = np.vstack((obj.positions, pos_norm))
                    else:
                        obj.positions = np.array(pos_norm)
        self._plot_actors()

        # Step through trajectories to find max and min values in each direction
        coords_max = [
            self.ax_3d.get_xlim()[1],
            self.ax_3d.get_ylim()[1],
            self.ax_3d.get_zlim()[1],
        ]
        coords_min = [
            self.ax_3d.get_xlim()[0],
            self.ax_3d.get_ylim()[0],
            self.ax_3d.get_zlim()[0],
        ]
        for obj in self.objects:
            coords_max = np.maximum(obj.positions.max(axis=0), coords_max)
            coords_min = np.minimum(obj.positions.min(axis=0), coords_min)
        self.ax_3d.set_xlim(coords_min[0], coords_max[0])
        self.ax_3d.set_ylim(coords_min[1], coords_max[1])
        self.ax_3d.set_zlim(coords_min[2], coords_max[2])

        # Update LOS heatmap
        current_actors = list(current_actors)
        los_matrix = self._get_los_matrix(current_actors)
        self._los_plot.set_data(los_matrix)
        xaxis = np.arange(len(current_actors))
        self.ax_los.set_xticks(xaxis)
        self.ax_los.set_yticks(xaxis)
        self.ax_los.set_xticklabels(current_actors)
        self.ax_los.set_yticklabels(current_actors)
        self.fig.canvas.draw_idle()

        self.ax_3d.set_title(self._sec_to_ddhhmmss(local_time_d / pk.SEC2DAY))

    def _animate(self, sim: PASEOS, dt: float) -> List[Artist]:
        """Advances the time of sim, updates the plot, and returns the axis objects

        Args:
            sim (PASEOS): simulation object.
            dt (float): size of time step

        Returns:
            List[Artist]: list of Artist objects
        """
        sim.advance_time(dt)
        self._update(sim)
        return self.ax_3d.get_children() + self.ax_los.get_children()

    def _animation_wrapper(self, step: int, sim: PASEOS, dt: float) -> List[Artist]:
        """Wrapper to allow for frame numbers from animation

        Args:
            step (int): current frame number of the animation
            sim (PASEOS): simulation object.
            dt (float): size of time step

        Returns:
            List[Artist]: list of Artist objects
        """
        return self._animate(sim, dt)

    def animate(self, sim: PASEOS, dt: float, steps: int = 1, name: str = None) -> None:
        """Animates paseos for a given number of steps with dt in each step.

        Args:
            sim (PASEOS): simulation object.
            dt (float): size of time step
            steps (int, optional): number of steps to animate. Defaults to 1.
            name (str, optional): filename to save the animation. Defaults to None.
        """
        if name is None:
            self._animate(sim, dt)
        else:
            anim = animation.FuncAnimation(
                self.fig,
                self._animation_wrapper,
                frames=steps,
                fargs=(
                    sim,
                    dt,
                ),
                interval=20,
                blit=True,
            )  # blit means to only redraw parts that changed
            anim.save(f"{name}.mp4", writer="ffmpeg", fps=10)
