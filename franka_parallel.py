
import torch

import genesis as gs


def main():


    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################

    scene = gs.Scene(
        show_viewer=False,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())
    franka = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    ########################## build ##########################
    scene.build(n_envs=30000)

    franka.control_dofs_position(
        torch.tile(
            torch.tensor([0, 0, 0, -1.0, 0, 0, 0, 0.02, 0.02], device=gs.device), (30000, 1)
        ),
    )

    gs.tools.run_in_another_thread(fn=run_sim, args=(scene,))


def run_sim(scene):
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
