import sys

sys.path.append("../")

from paseos.actors.base_actor import BaseActor
from paseos.actors.ground_station_actor import GroundstationActor
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.paseos import PASEOS
import paseos
from animation import Animation

import pykep as pk
import numpy as np
from dotmap import DotMap

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


class SpaceAnimation(Animation):
    """This class visualizes the central body, local actor and known actors over time."""

    fp = FontProperties(fname=r"./visualization/FontAwesome.otf")
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

        # Create list of objects to be plotted
        current_actors = self._make_actor_list(sim)
        self._norm_coeff = self._local_actor._central_body.radius

        for known_actor in current_actors:
            pos, _ = known_actor.get_position_velocity(pk.epoch(sim.state.time))
            pos_norm = [x / self._norm_coeff for x in pos]
            self.objects.append(DotMap(actor=known_actor, positions=np.array(pos_norm)))

        # create figure
        self.fig = plt.figure(figsize=plt.figaspect(0.5) * 1.5)
        self.ax = plt.subplot(projection="3d")
        self.ax.set_title(self._sec_to_ddhhmmss(sim.state.time))
        self.ax.get_xaxis().set_ticks([])
        self.ax.get_yaxis().set_ticks([])
        self.ax.get_zaxis().set_ticks([])
        self.n_trajectory = 50  # how many samples from histories to visualize
        self._textbox_offset = 0.05  # how many samples from histories to visualize

        # plot the objects
        self._plot_central_body()
        self._plot_actors()

        plt.show(block=False)

    def _plot_central_body(self) -> None:
        central_body = self._local_actor._central_body
        central_body.radius

        u, v = np.mgrid[0: 2 * np.pi: 30j, 0: np.pi: 20j]
        x = np.cos(u) * np.sin(v)
        y = np.sin(u) * np.sin(v)
        z = np.cos(v)
        self.ax.plot_surface(x, y, z, color="grey")

    def _populate_textbox(self, actor: BaseActor) -> str:
        if isinstance(actor, SpacecraftActor):
            battery_level = actor.battery_level * 100
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

            # TODO: insert communication link info

            info_str = f"{actor.name} \n{battery_level:.0f}% {battery_icon} \n{self.symbols.communication}"

        elif isinstance(actor, GroundstationActor):
            # TODO: implement textbox for groundstation
            pass

        return info_str

    def _plot_actors(self) -> None:
        for obj in self.objects:
            data = obj.positions
            if data.ndim == 1:
                data = data[..., np.newaxis].T
            n_points = np.minimum(data.shape[0], self.n_trajectory)

            if "plot" in obj.keys():
                # only spacecraft actor moves in aninmation
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

            else:
                if isinstance(obj.actor, SpacecraftActor):
                    trajectory = self.ax.plot3D(data[0, 0], data[0, 1], data[0, 2])[0]
                    obj.plot.trajectory = trajectory
                    obj.plot.point = self.ax.plot(
                        data[0, 0], data[0, 1], data[0, 2], "*", color=trajectory.get_color()
                    )[0]
                    actor_info = self._populate_textbox(obj.actor)
                    obj.plot.text = self.ax.text(
                        data[0, 0] + self._textbox_offset,
                        data[0, 1] + self._textbox_offset,
                        data[0, 2] + self._textbox_offset,
                        actor_info,
                        fontproperties=self.fp,
                        bbox=dict(facecolor="white"),
                        verticalalignment="bottom",
                        clip_on=True,
                    )

        self.ax.set_box_aspect((np.ptp(self.ax.get_xlim()), np.ptp(self.ax.get_ylim()), np.ptp(self.ax.get_zlim())))

    def _make_actor_list(self, sim):
        if len(sim.known_actors) > 0:
            current_actors = [sim.local_actor] + list(sim.known_actors.values())
        else:
            current_actors = [sim.local_actor]
        return current_actors

    def update(self, sim):

        # NOTE: the actors in sim are unique so make use of sets
        objects_in_plot = set([obj.actor for obj in self.objects])
        current_actors = set(self._make_actor_list(sim))

        objects_to_remove = list(
            objects_in_plot.difference(current_actors)
        )  # if objects do not exist known actors, remove from plot next update.
        objects_to_add = list(
            current_actors.difference(objects_in_plot)
        )  # if known_actor does not exist in objects, add the actors and update in plot
        self.objects = [x for x in self.objects if x.actor not in objects_to_remove]

        for obj_to_add in objects_to_add:
            self.objects.append(DotMap(actor=obj_to_add))

        # update positions of objects
        for known_actor in current_actors:
            for obj in self.objects:
                if obj.actor == known_actor:
                    pos, _ = known_actor.get_position_velocity(pk.epoch(sim.state.time))
                    pos_norm = [x / self._norm_coeff for x in pos]
                    if "positions" in obj:
                        obj.positions = np.vstack((obj.positions, pos_norm))
                    else:
                        obj.positions = np.array(pos_norm)
        self._plot_actors()
<<<<<<< HEAD
        self.ax.set_title(self._sec_to_ddhhmmss(sim.state.time / pk.SEC2DAY))
        return 
=======
        self.ax.set_title(self._sec_to_ddhhmmss(sim.state.time))
>>>>>>> 6206dd7 (First implementation of visualization for PASEOS)


def test_animation():
    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = SpacecraftActor("sat1", [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth, 8000, 10000, 1)
    # init simulation
    sim = paseos.init_sim(sat1)

    sat2 = SpacecraftActor("sat2", [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth, 1, 1, 1)
    sim.add_known_actor(sat2)
    sat3 = SpacecraftActor("sat3", [0, -10000000, 0], [0, 0, -8000.0], pk.epoch(0), earth, 1, 1, 1)

<<<<<<< HEAD
    space_anim = SpaceAnimation(sim)

    import matplotlib.animation as animation

    def animate(frame_number):
        dt = 300
        sim.advance_time(dt * pk.SEC2DAY)
        space_anim.update(sim)
        
        if frame_number == 20:
            sim.add_known_actor(sat3)
        
        return space_anim.ax.get_children()
        
        
    
    anim = animation.FuncAnimation(space_anim.fig, animate, frames=400, 
                               interval=20, blit=True)
    anim.save('paseos.mp4', writer = 'ffmpeg', fps = 10)
    
    dt = 1 
    for t in range(1, 10000):
        sim.advance_time(dt * pk.SEC2DAY)
        animation.update(sim)

        
=======
    animation = SpaceAnimation(sim)

    dt = 1 / 1e3
    for t in range(1, 10000):
        sim.advance_time(dt)
        animation.update(sim)

        if t == 10:
            sim.add_known_actor(sat3)
>>>>>>> 6206dd7 (First implementation of visualization for PASEOS)

        plt.pause(0.1)


if __name__ == "__main__":
    test_animation()
