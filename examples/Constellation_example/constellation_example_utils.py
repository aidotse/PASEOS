import pandas as pd
import numpy as np


def convert_known_actors_to_categorical(values):
    """Helper function to track comms status"""
    conv_values = []
    for val in values:
        status = ["No signal", "Ground only", "CommSat only", "Ground + Sat"]
        idx = ("comms_1" in val) * 2 + 1 * ("gs_1" in val)
        conv_values.append(status[idx])
    return conv_values


def get_closest_entry(df, t, id):
    df_id = df[df.ID == id]
    return df_id.iloc[(df_id["Time"] - t).abs().argsort().iloc[:1]]


def get_analysis_df(df, timestep=60):

    t = np.round(np.linspace(0, df.Time.max(), int(df.Time.max() // timestep)))
    sats = df.ID.unique()
    df["known_actors"] = pd.Categorical(df.known_actors)
    df["comm_cat"] = df.known_actors.cat.codes

    charging = []
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
            n_c += vals.current_activity.values[0] == "Charging"
            n_ec += vals.is_in_eclipse.values[0]
            c_idx = vals.comm_cat.values[0]
            comm_stat[c_idx][idx] += 1
        charging.append(n_c)
        processing.append(len(sats) - n_c)
        is_in_eclipse.append(n_ec)

    ana_df = pd.DataFrame(
        {
            "Time[s]": t,
            "# of Charging": charging,
            "# of Processing": processing,
            "# in Eclipse": is_in_eclipse,
            "# of " + df.known_actors.cat.categories[0]: comm_stat[0],
            "# of " + df.known_actors.cat.categories[1]: comm_stat[1],
            "# of " + df.known_actors.cat.categories[2]: comm_stat[2],
            "# of " + df.known_actors.cat.categories[3]: comm_stat[3],
        }
    )

    return ana_df
