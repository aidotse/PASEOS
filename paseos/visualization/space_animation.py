import numpy as np
from dotmap import DotMap
from typing import List
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.artist import Artist
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
from loguru import logger

from paseos.actors.base_actor import BaseActor
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.ground_station_actor import GroundstationActor
from paseos.paseos import PASEOS
from paseos.visualization.animation import Animation


class SpaceAnimation(Animation):
    """This class visualizes the central body, local actor and known actors over time."""

    def __init__(self, sim: PASEOS, n_trajectory: int = 32) -> None:
        """Initialize the space animation object

        Args:
            sim (PASEOS): simulation object
            n_trajectory (int): number of samples in tail of actor
        """
        super().__init__(sim)
        logger.debug("Initializing animation")
        # Create list of objects to be plotted
        current_actors = self._make_actor_list(sim)
        self._norm_coeff = self._local_actor._central_body._planet.radius

        for known_actor in current_actors:
            pos = known_actor.get_position(self._local_actor.local_time)
            pos_norm = [x / self._norm_coeff for x in pos]
            self.objects.append(DotMap(actor=known_actor, positions=np.array(pos_norm)))

        with plt.style.context("dark_background"):
            # Create figure for 3d animation
            self.fig, default_ax = plt.subplots(
                1,
                2,
                figsize=(10, 5),
                facecolor="black",
                dpi=100,
                layout="constrained",
                gridspec_kw={"width_ratios": [3.5, 1]},
            )

            # Removing defaultax to add projection
            default_ax[0].remove()
            self.ax_3d = plt.subplot(121, projection="3d")

            # Get rid of the panes
            self.ax_3d.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            self.ax_3d.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            self.ax_3d.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

            # Get rid of the spines
            self.ax_3d.xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.ax_3d.yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.ax_3d.zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.ax_3d.get_xaxis().set_ticks([])
            self.ax_3d.get_yaxis().set_ticks([])
            self.ax_3d.get_zaxis().set_ticks([])

            # how many samples from histories to visualize
            self.n_trajectory = n_trajectory
            self._textbox_offset = 0.1

            # Create figure for LOS
            default_ax[1].remove()
            self.ax_los = plt.subplot(122)
            xaxis = np.arange(len(current_actors))
            self.ax_los.set_position([0.75, 0.7, 0.2, 0.2])
            self.ax_los.set_xticks(xaxis)
            self.ax_los.set_yticks(xaxis)
            self.ax_los.set_xticklabels(current_actors, fontsize=8)
            self.ax_los.set_yticklabels(current_actors, fontsize=8)

            # plot the objects
            self._plot_central_body()
            self._plot_actors()
            los_matrix = self._get_los_matrix(current_actors)
            self._plot_los(los_matrix)

            # Write text labels
            self.date_label = plt.annotate(
                self._local_actor.local_time,
                xy=(0.01, 0.01),
                xycoords="figure fraction",
            )
            self.time_label = plt.annotate(
                f"t={sim._state.time:<10.2e}",
                xy=(0.99, 0.01),
                xycoords="figure fraction",
                horizontalalignment="right",
            )

            plt.ion()
            plt.show()
            plt.pause(0.0001)

    def _plot_central_body(self) -> None:
        """Plot the central object as a sphere of radius 1"""
        central_body = self._local_actor._central_body
        central_body.radius

        u, v = np.mgrid[0 : 2 * np.pi : 30j, 0 : np.pi : 20j]
        x = np.cos(u) * np.sin(v)
        y = np.sin(u) * np.sin(v)
        z = np.cos(v)
        self.ax_3d.plot_surface(x, y, z, color="blue", alpha=0.5)

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
                # Skip LOS between groundstations (leads to crash)
                if isinstance(a1, GroundstationActor) and isinstance(a2, GroundstationActor):
                    continue
                elif a1.is_in_line_of_sight(a2, local_time) is True:
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
        if isinstance(actor, SpacecraftActor) or isinstance(actor, GroundstationActor):
            if actor.has_power_model:
                battery_level = actor.state_of_charge * 100
                info_str += f"\nBattery: {battery_level:.0f}%"

            if actor.has_thermal_model:
                info_str += f"\nTemperature: {actor.temperature_in_K:.2f}K,{actor.temperature_in_K-273.15:.2f}C"

            for name in actor.communication_devices.keys():
                info = actor.communication_devices[name]
                info_str += f"\nCommDevice1: {info.bandwidth_in_kbps} kbps"
        else:
            raise NotImplementedError(
                "SpacePlot is currently not implemented for actor type" + type(actor)
            )

        cur_act = actor._current_activity
        if cur_act is not None:
            info_str += f"\n({cur_act})"

        return info_str

    def _plot_los(self, los_matrix: np.ndarray) -> None:
        """Plot the LOS links in a heat map

        Args:
            los_matrix (np.ndarray): matrix telling what satellites can see each other.
        """
        # Create new colormap, with black for two
        colors = [(255, 0, 0), (0, 0, 0), (0, 255, 0)]
        new_map = LinearSegmentedColormap.from_list("new_map", colors, N=3)
        self._los_plot = self.ax_los.matshow(los_matrix, cmap=new_map, vmin=0, vmax=1)

        divider = make_axes_locatable(self.ax_los)
        cax = divider.append_axes("right", size="5%", pad=0.05)

        cbar = self.fig.colorbar(self._los_plot, ticks=[0, 1], cax=cax)
        cbar.ax.set_yticklabels(["no signal", "signal"])

    def _plot_actors(self) -> None:
        """Plots all the actors"""
        logger.trace("Updating actors.")

        for obj in self.objects:
            data = obj.positions
            if data.ndim == 1:
                data = data[..., np.newaxis].T
            n_points = np.minimum(data.shape[0], self.n_trajectory)

            logger.trace(f"Position for object: {data}")
            if "plot" in obj.keys():
                # spacecraft and ground stations behave differently and are plotted separately
                if isinstance(obj.actor, SpacecraftActor) or isinstance(
                    obj.actor, GroundstationActor
                ):
                    logger.trace("Updating SpacecraftActor.")

                    # update trajectory
                    obj.plot.trajectory.set_data(data[-n_points:, :2].T)
                    obj.plot.trajectory.set_3d_properties(data[-n_points:, 2].T)

                    # update satellite position
                    data_point = list(map(lambda el: [el], data[-1, :]))
                    obj.plot.point.set_data_3d(data_point)

                    # update text box
                    actor_info = self._populate_textbox(obj.actor)
                    obj.plot.text.set_position_3d(data[-1, :] + self._textbox_offset)
                    obj.plot.text.set_text(actor_info)
            else:
                if isinstance(obj.actor, SpacecraftActor) or isinstance(
                    obj.actor, GroundstationActor
                ):
                    trajectory = self.ax_3d.plot3D(data[0, 0], data[0, 1], data[0, 2])[0]
                    obj.plot.trajectory = trajectory
                    obj.plot.point = self.ax_3d.plot(
                        data[0, 0],
                        data[0, 1],
                        data[0, 2],
                        "x",
                        color=trajectory.get_color(),
                    )[0]
                    actor_info = self._populate_textbox(obj.actor)
                    if obj.actor == self._local_actor:
                        obj.plot.text = self.ax_3d.text(
                            data[0, 0] + self._textbox_offset,
                            data[0, 1] + self._textbox_offset,
                            data[0, 2] + self._textbox_offset,
                            actor_info,
                            # bbox=dict(facecolor="mediumspringgreen"),
                            verticalalignment="bottom",
                            clip_on=True,
                            fontsize=8,
                        )

                    else:
                        obj.plot.text = self.ax_3d.text(
                            data[0, 0] + self._textbox_offset,
                            data[0, 1] + self._textbox_offset,
                            data[0, 2] + self._textbox_offset,
                            actor_info,
                            # bbox=dict(facecolor="white"),
                            color="lightskyblue",
                            verticalalignment="bottom",
                            clip_on=True,
                            fontsize=8,
                        )

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

    def update(self, sim: PASEOS, creating_animation=False) -> None:
        """Updates the animation with the current actor information

        Args:
            sim (PASEOS): simulation object.
            creating_animation (bool): If currently creating an animation. Then draw_idle will be used. Defaults to False.
        """
        logger.trace("Updating animation")
        # NOTE: the actors in sim are unique so make use of sets
        objects_in_plot = set([obj.actor for obj in self.objects])
        current_actors = set(self._make_actor_list(sim))

        # if objects do not exist in known actors, remove from plot next update.
        objects_to_remove = list(objects_in_plot.difference(current_actors))

        # if known_actor does not exist in objects, add the actors and update in plot
        objects_to_add = list(current_actors.difference(objects_in_plot))

        plot_objects_to_remove = [x for x in self.objects if x.actor in objects_to_remove]
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
                    pos = known_actor.get_position(self._local_actor.local_time)
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
            overhead = 1.1  # Give some more space to fit text
            coords_max = np.maximum(obj.positions.max(axis=0) * overhead, coords_max)
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
        self.ax_los.set_xticklabels(current_actors, fontsize=8, rotation=90)
        self.ax_los.set_yticklabels(current_actors, fontsize=8)

        if creating_animation:
            self.fig.canvas.draw_idle()
        else:
            self.fig.canvas.draw()
        plt.pause(0.0001)

        # on some systems the below line throws an error. presumably due to pykep?
        try:
            self.date_label.set_text(self._local_actor.local_time)
        except RuntimeError:
            logger.trace("Animation date label could not be updated.")

        self.time_label.set_text(f"t={sim._state.time - sim._cfg.sim.start_time:<10.2e}")

        logger.debug("Plot updated.")

    def _animate(self, sim: PASEOS, dt: float) -> List[Artist]:
        """Advances the time of sim, updates the plot, and returns the axis objects

        Args:
            sim (PASEOS): simulation object.
            dt (float): size of time step

        Returns:
            List[Artist]: list of Artist objects
        """
        sim.advance_time(dt, 0)
        self.update(sim, creating_animation=True)
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

    def animate(self, sim: PASEOS, dt: float, steps: int = 1, save_to_file: str = None) -> None:
        """Animates paseos for a given number of steps with dt in each step.

        Args:
            sim (PASEOS): simulation object.
            dt (float): size of time step
            steps (int, optional): number of steps to animate. Defaults to 1.
            save_to_file (str, optional): filename to save the animation. Defaults to None.
        """
        if save_to_file is None:
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
            anim.save(f"{save_to_file}.mp4", writer="ffmpeg", fps=30)
