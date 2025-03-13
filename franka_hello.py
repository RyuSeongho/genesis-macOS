import argparse
import genesis as gs


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

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
    r0 = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    ########################## cameras ##########################
    cam = scene.add_camera(
        res=(640, 480),
        pos=(3.5, 0.0, 2.5),
        lookat=(0, 0, 0.5),
        fov=30,
        GUI=False,
    )


    ########################## build ##########################
    scene.build()

    gs.tools.run_in_another_thread(fn=run_sim, args=(scene, cam, args.vis))
    if args.vis:
        scene.viewer.start()


def run_sim(scene, cam, enable_vis):
    from time import time
    cam.start_recording()
    t_prev = time()
    i = 0
    while True:
        i += 1

        scene.step()
        cam.render()

        t_now = time()
        print(1 / (t_now - t_prev), "FPS")
        t_prev = t_now
        if i > 200: # switched 200 to 20000
            break

    if enable_vis:
        scene.viewer.stop()

    cam.stop_recording(save_to_filename="franka_hello.mp4", fps=60)


if __name__ == "__main__":
    main()
