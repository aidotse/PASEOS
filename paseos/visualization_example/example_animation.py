import sys
sys.path.append("../..")

from utils import test_setup
from paseos.visualization.space_animation import SpaceAnimation

def animation():
    sim, _, _, _ = test_setup()
    anim = SpaceAnimation(sim)
    anim.animate(sim, dt=200, steps=400, name="paseos_test", save_file=True)


if __name__ == "__main__":
    animation()
