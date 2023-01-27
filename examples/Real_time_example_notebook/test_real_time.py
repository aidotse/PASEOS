import sys 
import os
sys.path.insert(1, os.path.join("..",".."))
sys.path.insert(1, "..")
from Sentinel_2_example_notebook.utils import acquire_data
import pykep as pk
import paseos
from paseos import ActorBuilder, SpacecraftActor, GroundstationActor
from paseos.utils.load_default_cfg import load_default_cfg
from paseos.communication.is_in_line_of_sight import is_in_line_of_sight
from Sentinel_2_example_notebook.utils import s2pix_detector, acquire_data
import asyncio
import urllib.request
import matplotlib.pyplot as plt
from matplotlib import patches

paseos.set_log_level("ERROR")
import argparse

try:
    import yappi
except: 
    raise ValueError("You need to install yappi to perform profiling. Please, refer to: https://github.com/sumerc/yappi")


#Activity function
async def detect_volcanic_eruptions_async(args):
    # Fetch the inputs
    images, images_coordinates = args[0],args[1]

    # Detecting volcanic eruptions, returning their bounding boxes and their coordinates.
    bboxes=[]
    #Please, refer to utils.py.
    for n in range(len(images)):
        bbox = s2pix_detector(images[n], images_coordinates[n])
        bboxes.append(bbox)
    # Store result
    args[2][0] = bboxes
    await asyncio.sleep(10)

# Constraint function
async def check_los_with_ground_station(args):
    sat=args[0]
    ground_station=args[1]
    # Stops the activity is the satellite is not in line with the ground station.
    ground_station_in_los=not(is_in_line_of_sight(sat, ground_station,sat.local_time))
    args[2][0]=ground_station_in_los
    return ground_station_in_los

# Termination function
async def transmit_to_ground_station(args):
    
    ground_station_in_los=args[0][0]

    if ground_station_in_los:  
        print("Transmitting to ground...")
    else:
        print("No ground station reached...")
    return True # Stops the activity is the satellite is not in line with the ground station.


def main():
    # Input parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--activity_timestep', type=float, help='Periodic time for activity checking.', default=1.0)
    parser.add_argument('--n_images', type=int, help='Number of images to process.', default=100)
    parser.add_argument('--test_iteration', type=str, help='Test iteration ID.', default="1")

    pargs=parser.parse_args()

    # Define local actor
    sat = ActorBuilder.get_actor_scaffold(name="sat", actor_type=SpacecraftActor, epoch=pk.epoch(0))

    # Define a ground station actor
    ground_station = GroundstationActor(name="grndStation", epoch=pk.epoch(0))

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    #Define today as pykep epoch (27-10-22)
    #please, refer to https://esa.github.io/pykep/documentation/core.html#pykep.epoch
    today = pk.epoch_from_string('2022-10-27 12:30:00.000')

    sentinel2B_line1 = "1 42063U 17013A   22300.18652110  .00000099  00000+0  54271-4 0  9998"
    sentinel2B_line2 = "2 42063  98.5693  13.0364 0001083 104.3232 255.8080 14.30819357294601"
    sentinel2B = pk.planet.tle(sentinel2B_line1, sentinel2B_line2)

    #Calculating S2B ephemerides.
    sentinel2B_eph=sentinel2B.eph(today)

    #Adding orbit around Earth based on previously calculated ephemerides
    ActorBuilder.set_orbit(actor=sat, 
                        position=sentinel2B_eph[0], 
                        velocity=sentinel2B_eph[1], 
                        epoch=today, central_body=earth)
    #Adding power device
    ActorBuilder.set_power_devices(actor=sat, 
                                battery_level_in_Ws=162000, 
                                max_battery_level_in_Ws=162000, 
                                charging_rate_in_W=10)
    
    #Add radiation model
    ActorBuilder.set_radiation_model(
        actor=sat,
        data_corruption_events_per_s=0,
        restart_events_per_s=0,
        failure_events_per_s=0,
    )

    #Add thermal model
    ActorBuilder.set_thermal_model(
        actor=sat,
        actor_mass=50.0,
        actor_initial_temperature_in_K=273.15,
        actor_sun_absorptance=1.0,
        actor_infrared_absorptance=1.0,
        actor_sun_facing_area=1.0,
        actor_central_body_facing_area=1.0,
        actor_emissive_area=1.0,
        actor_thermal_capacity=1000,
    )

    #Set the ground station (Maspalomas)
    ActorBuilder.set_ground_station_location(ground_station,
                                            latitude=-15.6338,
                                            longitude=27.7629,
                                            minimum_altitude_angle=5,
                                            elevation=205.1)

    #Initialize PASEOS
    cfg=load_default_cfg() # loading cfg to modify defaults
    cfg.sim.start_time=today.mjd2000 * pk.DAY2SEC # convert epoch to seconds
    cfg.sim.activity_timestep = pargs.activity_timestep  # update rate for plots. 
    sim = paseos.init_sim(sat, cfg)
    sim.add_known_actor(ground_station)

    #Download input data if needed.
    if not(os.path.isfile("Etna_00.tif")):
        print("Downloading the file: Etna_00.tif")
        urllib.request.urlretrieve("https://actcloud.estec.esa.int/actcloud/index.php/s/9Tw5pEbGbVO3Ttt/download", "Etna_00.tif")
    if not(os.path.isfile("La_Palma_02.tif")):
        print("Downloading the file: La_Palma_02.tif")
        urllib.request.urlretrieve("https://actcloud.estec.esa.int/actcloud/index.php/s/vtObKJOuYLgdPf4/download", "La_Palma_02.tif")
    if not(os.path.isfile("Mayon_02.tif")):
        print("Downloading the file: Mayon_02.tif")
        urllib.request.urlretrieve("https://actcloud.estec.esa.int/actcloud/index.php/s/e0MyilW1plYdehL/download", "Mayon_02.tif")

    #Parsing inputs
    # data to acquire
    data_to_acquire=["Etna_00.tif", "La_Palma_02.tif", "Mayon_02.tif"]
    # images placeholder
    imgs=[]
    # image coordimates placeholder
    imgs_coordinates=[]

    for n in range(len(data_to_acquire)):
        # Acquiring image
        img_n, img_coordinates_n=acquire_data(data_to_acquire[n])
        imgs.append(img_n)
        imgs_coordinates.append(img_coordinates_n)

    # Repeating images to get N_total_images
    imgs=imgs + [imgs[n % len(data_to_acquire)] for n in range(pargs.n_images - len(data_to_acquire))]
    imgs_coordinates = imgs_coordinates + [imgs_coordinates[n % len(data_to_acquire)] for n in range(pargs.n_images - len(data_to_acquire))]

    
    # Register an activity that emulate event detection
    sim.register_activity(
        "volcanic_event_detection",
        activity_function=detect_volcanic_eruptions_async,
        power_consumption_in_watt=10,
        constraint_function=check_los_with_ground_station,
        on_termination_function=transmit_to_ground_station
    )
    with yappi.run():
        #Placeholder for output bbox list.
        output_event_bbox_info = [None]

        #Ground station reached flag
        ground_station_in_los = [None]

        #Run the activity
        sim.perform_activity("volcanic_event_detection",  activity_func_args=[imgs, imgs_coordinates, output_event_bbox_info], constraint_func_args=[sat, ground_station, ground_station_in_los], termination_func_args=[ground_station_in_los])
   
    
    stats=yappi.get_func_stats()
    os.makedirs("tests", exist_ok=True)

    f = open(os.path.join("tests","profiling_activity_timestep_"+str(pargs.activity_timestep)+"_n_images_"+str(pargs.n_images)+"_test_iteration_"+str(pargs.test_iteration)+".txt"), 'w')
    f.write("---------------n_images_"+str(pargs.n_images)+"-----------activity_timestep_"+str(pargs.activity_timestep)+"-----------test_iteration_"+str(pargs.test_iteration)+"---------------")
    stats.print_all(out=f)

    f.close()


if __name__ == "__main__":
    main()
   