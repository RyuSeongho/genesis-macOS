import argparse

import torch

import genesis as gs

import numpy as np



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-p", "--pd_control", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 960),
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0.0, 0.0, -10.0),
        ),
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())
    franka = scene.add_entity(
        gs.morphs.MJCF(
            file  = 'xml/franka_emika_panda/panda.xml',
            pos   = (1.0, 1.0, 0.0),
            euler = (0, 0, 0),
        ),
    )

    ########################## cameras ##########################
    cam = scene.add_camera(
        res=(640, 480),
        pos=(4.5, 1.0, 2.5),
        lookat=(1.0, 1.0, 0.5),
        fov=30,
        GUI=False,
    )

    ########################## build ##########################
    scene.build()

    ########################## control ##########################
    jnt_names = [
        'joint1',
        'joint2',
        'joint3',
        'joint4',
        'joint5',
        'joint6',
        'joint7',
        'finger_joint1',
        'finger_joint2',
    ]
    dofs_idx = [franka.get_joint(name).dof_idx_local for name in jnt_names]

    ############ Optional: set control gains ############
    # set positional gains
    franka.set_dofs_kp(
        kp             = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
        dofs_idx_local = dofs_idx,
    )
    # set velocity gains
    franka.set_dofs_kv(
        kv             = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
        dofs_idx_local = dofs_idx,
    )
    # set force range for safety
    franka.set_dofs_force_range(
        lower          = np.array([-87, -87, -87, -87, -12, -12, -12, -100, -100]),
        upper          = np.array([ 87,  87,  87,  87,  12,  12,  12,  100,  100]),
        dofs_idx_local = dofs_idx,
    )

    gs.tools.run_in_another_thread(fn=run_sim, args=(scene, franka, cam, args.vis, dofs_idx, args.pd_control))
    if args.vis:
        scene.viewer.start()


def hard_reset(franka, dofs_idx, i):
    if i < 50:
        franka.set_dofs_position(np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]), dofs_idx)
    elif i < 100:
        franka.set_dofs_position(np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]), dofs_idx)
    else:
        franka.set_dofs_position(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]), dofs_idx)


def pd_control(franka, dofs_idx, i):
    if i == 0:
        franka.control_dofs_position(
            np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]),
            dofs_idx,
        )
    elif i == 250:
        franka.control_dofs_position(
            np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]),
            dofs_idx,
        )
    elif i == 500:
        franka.control_dofs_position(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
            dofs_idx,
        )
    elif i == 750:
        # control first dof with velocity, and the rest with position
        franka.control_dofs_position(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])[1:],
            dofs_idx[1:],
        )
        franka.control_dofs_velocity(
            np.array([1.0, 0, 0, 0, 0, 0, 0, 0, 0])[:1],
            dofs_idx[:1],
        )
    elif i == 1000:
        franka.control_dofs_force(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
            dofs_idx,
        )
    

def run_sim(scene, franka, cam, enable_vis, dofs_idx, is_pd_control):
    from time import time
    limit = 1250 if is_pd_control else 150
    cam.start_recording()
    t_prev = time()
    i = 0
    while True:
        i += 1

        if is_pd_control:
            pd_control(franka, dofs_idx, i)
        else:
            hard_reset(franka, dofs_idx, i)

        scene.step()
        cam.render()

        t_now = time()
        print(1 / (t_now - t_prev), "FPS")
        t_prev = t_now
        if i > limit:
            break

    if enable_vis:
        scene.viewer.stop()
    record_name = "franka_control_pd.mp4" if is_pd_control else "franka_control_hard_reset.mp4"

    cam.stop_recording(save_to_filename=record_name, fps=60)


if __name__ == "__main__":
    main()
