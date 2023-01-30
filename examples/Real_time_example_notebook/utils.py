import platform
def clean_list(list_to_clean):
    """Clean list of tasks-profile removing empty elements.

    Args:
        list_to_clean (list): list to clean.
    Returns:
        list list: cleaned list.
    """
    list_clean=[]
    for x in list_to_clean:
        if x != "":
            list_clean.append(x)

    return list_clean


def extract_cpu_time_from_file(file_name):
    """Extracts CPU time for each task from a file.

    Args:
        file_name (str): file to parse.

    Returns:
        dict: {computing_part_name : cpu_time}
    """
    task_name_list=["PASEOS.perform_activity", "detect_volcanic_eruptions_async", "PASEOS.advance_time", "check_los_with_ground_station", "ThermalModel.update_temperature", "RadiationModel.did_device_restart", "..odel.did_device_experience_failure"]

    f=open(file_name,"r")
    profiling_results_text=f.read()
    f.close()
    if platform.system() == "Windows":
        profiling_results_list=profiling_results_text.split("\n\n")
    else:
        profiling_results_list=profiling_results_text.split("\n")
        
    profiling_results_list=profiling_results_list[5:]

    profiling_results=[]
    for x in profiling_results_list:
        profiling_results.append(clean_list(x.split(" ")))
    
    task_to_track_idx_list=[]
    for idx in range(len(profiling_results)):
        for elem in profiling_results[idx]:
            for task in task_name_list:
                if task in elem:
                    task_to_track_idx_list.append(idx)
                    break

    task_name_list_sorted=[profiling_results[idx][-5] for idx in  task_to_track_idx_list]
    task_name_id_dict=dict(zip(task_name_list_sorted, task_to_track_idx_list))
    total_time=float(profiling_results[task_name_id_dict["PASEOS.perform_activity"]][-2])
    time_activity=float(profiling_results[task_name_id_dict["detect_volcanic_eruptions_async"]][-2])
    paseos_activity=float(profiling_results[task_name_id_dict["PASEOS.advance_time"]][-2])
    los_check=float(profiling_results[task_name_id_dict["check_los_with_ground_station"]][-2])
    thermal_model=float(profiling_results[task_name_id_dict["ThermalModel.update_temperature"]][-2])/2
    charge_model=thermal_model
    radiation_time=float(profiling_results[task_name_id_dict["RadiationModel.did_device_restart"]][-2])+float(profiling_results[task_name_id_dict["..odel.did_device_experience_failure"]][-2])
    return dict(zip(["total_time","activity", "paseos", "charge", "radiation", "thermal", "los_check"],[total_time, time_activity, paseos_activity, charge_model, radiation_time, thermal_model, los_check]))