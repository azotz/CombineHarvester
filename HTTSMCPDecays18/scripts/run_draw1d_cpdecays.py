import oyaml as yaml
import pandas as pd
import numpy as np
import argparse

from plotting import (
    draw_1d, 
    create_df,
    var_kw,
    process_kw,
    nbins_kw,
)

def parse_arguments():
    epilog = (
        "Example:\n \n"
        "python3 scripts/run_draw1d_cpdecays.py --channel mt --year 2016 "
        "--signal-scale 50 --mode prefit --datacard shapes_sm_eff.root "
        "--alt-datacard shapes_ps_eff.root "
    )
    parser = argparse.ArgumentParser(epilog=epilog)

    parser.add_argument(
        "--channel", default="tt", choices=["tt", "mt"],
        help="Which channel to use",
    )
    parser.add_argument(
        "--year", default=2018,
        help="Which year to use",
    )
    parser.add_argument(
        "--signal-scale", default=1.,
        help="Scale the signal by this value (not for 'unrolled' plots)",
    )
    parser.add_argument(
        "--mode", default="prefit", choices=["prefit", "postfit"],
        help="Which histograms to use",
    )
    parser.add_argument(
        "--datacard", default="shapes_eff.root",
        help="Path to PostFitShapes datacard",
    )
    parser.add_argument(
        "--alt-datacard", default=None,
        help="If set, use alternative template (for signal) found at this path",
    )
    parser.add_argument(
        "--no-ff", action="store_true", default=False,
        help="Don't use fake factors",
    )
    parser.add_argument(
        "--no-embedding", action="store_true", default=False,
        help="Don't use embedded samples",
    )

    arguments = parser.parse_args()

    # Use ff and embedding by default, but making it less confusing
    # for users
    arguments.ff = not arguments.no_ff
    del arguments.no_ff

    arguments.embedding = not arguments.no_embedding
    del arguments.no_embedding

    return arguments

def draw1d_cpdecays(
    channel, year, signal_scale, ff, embedding, mode, datacard, alt_datacard,
):

    # Plotting SM and PS template
    signals = ["H_sm"]
    if alt_datacard is not None:
        signals = ["H_sm", "H_ps"]

    leg_kw = {"offaxis": True, "fontsize": 9, "labelspacing":0.12,}

    ch_kw = {}
    with open("scripts/plot_kw.yaml", "r") as f:
        ch_kw = yaml.safe_load(f)
    if ff: # always use FF
        ch_kw = {}
        with open("scripts/plot_kw_postfit.yaml", "r") as f:
            ch_kw = yaml.safe_load(f)
    if embedding: # always use embedding
        for ch, proc in ch_kw.items():
            if ch in ["tt", "mt", "et", "em",]:
                proc["EmbedZTT"] = ["EmbedZTT"]
                del proc["ZTT"]

    # Histogram processes to load in
    if embedding and ff:
        processes = ['data_obs', 'EmbedZTT', 'ZL', 'TTT', 'VVT', 'jetFakes',]
    elif ff:
        processes = ['data_obs', 'ZTT', 'ZL', 'TTT', 'VVT', 'jetFakes', 'EWKZ',]
    elif embedding:
        processes = [
            'data_obs', 'EmbedZTT', 'ZL', 'TTT', 'VVT', 'VVJ', 'W', 'QCD', 'ZJ'
        ]
    else:
        processes = [
            'data_obs', 'ZTT', 'ZL', 'ZJ', 'TTT', 'TTJ', 'VVT', 'VVJ', 
            'W', 'QCD', 'EWKZ',
        ]

    if len(signals) > 0:
        processes.extend([
            "ggH_sm_htt", "qqH_sm_htt", #"ZH_sm_htt", "WH_sm_htt",
            "ggH_ps_htt", "qqH_ps_htt", #"ZH_ps_htt", "WH_ps_htt",
        ])
        
    # Draw categories (defined in nbins_kw):
    # 1-2: backgrounds, 3+: higgs categories
    if channel == "tt":
        unrolled_bins = list(range(1, 12))
    elif channel == "mt":
        unrolled_bins = list(range(1,7))
    for bin_number in unrolled_bins:

        category = nbins_kw[channel][bin_number][3]

        if channel == "tt":
            plot_var = "IC_15Mar2020_max_score"
        elif channel == "mt":
            plot_var = "NN_score"

        directory = f"htt_{channel}_{year}_{bin_number}_13TeV_{mode}"

        print(f"Doing category {category}")
        if category in ["embed", "fakes"]:
            if channel == "tt":
                plot_var = "IC_15Mar2020_max_score"
            elif channel == "mt":
                plot_var = "NN_score"
            partial_blind = False
            unrolled = False
            norm_bins = True
            signal_scale = 50.
        else:
            plot_var = "Bin_number"
            partial_blind = True
            unrolled = True
            norm_bins = False
            signal_scale = 1.

        df_plot = create_df(datacard, directory, channel, processes, ch_kw)
        df_plot_alt = create_df(alt_datacard, directory, channel, processes, ch_kw)
        if df_plot_alt is not None:
            df_plot = pd.concat([
                df_plot,
                df_plot_alt.loc[
                    df_plot_alt.index.get_level_values("parent") == "H_ps"
                ]
            ], axis='index', sort=False)
        if partial_blind:
            # Unblind first window of unrolled bins only (for now)
            data_mask = df_plot.index.get_level_values("parent") == "data_obs"
            blind_mask = df_plot.index.get_level_values("binvar0") >= \
                nbins_kw[channel][bin_number][1]
            df_plot.loc[data_mask & blind_mask, "sum_w"] = np.nan
        draw_1d(
            df_plot, plot_var, channel, year, blind=False,
            sigs=signals, signal_scale=signal_scale, ch_kw=ch_kw, process_kw=process_kw, 
            var_kw=var_kw, leg_kw=leg_kw, unrolled=unrolled, norm_bins=norm_bins,
            nbins=nbins_kw[channel][bin_number], mcstat=True, mcsyst=True,
        )

if __name__ == "__main__":
    draw1d_cpdecays(**vars(parse_arguments()))
