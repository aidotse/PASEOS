import numpy as np
import pandas as pd


def get_known_actor_comms_status(values):
    """Helper function to track comms status"""
    conv_values = []
    for val in values:
        status = ["No signal", "Ground only", "CommSat only", "Ground + Sat"]
        idx = ("comms_1" in val) * 2 + 1 * ("gs_1" in val)
        conv_values.append(status[idx])
    return conv_values

def get_bitrate_status(link):
    """Helper function to get bitrate status history"""
    return link.bitrate_history

def get_line_of_sight_status(link):
    """Helper function to get line of sight status history"""
    return link.line_of_sight_history

def get_distance_status(link):
    """Helper function to distance status history"""
    return link.distance_history

def get_elevation_angle_status(link):
    """Helper function to get elevation angle status history"""
    return link.elevation_angle_history


def get_closest_entry(df, t, id):
    df_id = df[df.ID == id]
    return df_id.iloc[(df_id["Time"] - t).abs().argsort().iloc[:1]]


def get_analysis_df(df, timestep=60, orbital_period=1):
    t = np.round(np.linspace(0, df.Time.max(), int(df.Time.max() // timestep)))
    sats = df.ID.unique()
    df["known_actors"] = pd.Categorical(df.known_actors)
    df["comm_cat"] = df.known_actors.cat.codes
    standby = []
    processing = []
    is_in_eclipse = []
    comm_stat = [[], [], [], []]

    for idx, t_cur in enumerate(t):
        n_c = 0
        n_ec = 0
        for c in comm_stat:
            c.append(0)
        for sat in sats:
            vals = get_closest_entry(df, t_cur, sat)
            n_c += vals.current_activity.values[0] == "Standby"
            n_ec += vals.is_in_eclipse.values[0]
            c_idx = vals.comm_cat.values[0]
            comm_stat[c_idx][idx] += 1
        standby.append(n_c)
        processing.append(len(sats) - n_c)
        is_in_eclipse.append(n_ec)

    ana_df = pd.DataFrame(
        {
            "Time[s]": t,
            "# of Standby": standby,
            "# of Processing": processing,
            "# in Eclipse": is_in_eclipse,
            "# of " + df.known_actors.cat.categories[0]: comm_stat[0],
            "# of " + df.known_actors.cat.categories[1]: comm_stat[1],
            "# of " + df.known_actors.cat.categories[2]: comm_stat[2],
            # "# of " + df.known_actors.cat.categories[3]: comm_stat[3],
        }
    )
    ana_df["Completed orbits"] = ana_df["Time[s]"] / orbital_period
    ana_df = ana_df.round({"Completed orbits": 2})
    ana_df["Share Processing"] = ana_df["# of Processing"] / len(sats)
    ana_df["Share in Eclipse"] = ana_df["# in Eclipse"] / len(sats)

    return ana_df
