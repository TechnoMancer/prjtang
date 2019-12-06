#! /usr/bin/env python3
"""
Fuzz the various MUX settings for the LSLICE LUTs.
The LSLICE has a pair of muxes to determine the output of the F and FX signals.
The purpose of the DEMUX and CMIMUX are currently unknown.
This was originally adapted from a fuzzer in project Trellis.
"""
from fuzzconfig import FuzzConfig
import nonrouting
import fuzzloops
import pytang

tile_loc = "x2y70"
cfg = FuzzConfig(job="PLBLSICEMUX", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc)])

models = ["mslice", "mslice", "lslice", "lslice"]

def main():
    pytang.load_database("../../../database")
    cfg.setup()
    empty_bitfile = cfg.build_design(cfg.pnl, {})
    cfg.pnl = "lslice_mux.pnl"

    def per_slice(slicen):
        r = 0
        model = models[slicen]
        slicename = model.upper() + str(slicen)

        def get_substs(demux="E", cmimux="C", lsfmux="SUM", lsfxmux="SUM"):
            return dict(slice=str(slicen), r=str(r), model=model, tile_loc=tile_loc,
                        demux=demux,
                        cmimux=cmimux,
                        lsfmux=lsfmux,
                        lsfxmux=lsfxmux)

        for r in range(2):
                nonrouting.fuzz_enum_setting(cfg, "{}.DEMUX{}".format(slicename, r), ["D", "E"],
                                         lambda x: get_substs(demux=x),
                                         empty_bitfile)
                nonrouting.fuzz_enum_setting(cfg, "{}.CMIMUX{}".format(slicename, r), ["C", "MI"],
                                         lambda x: get_substs(cmimux=x),
                                         empty_bitfile)
                nonrouting.fuzz_enum_setting(cfg, "{}.LSFMUX{}".format(slicename, r), ["LUTF", "SUM", "FUNC5"],
                                         lambda x: get_substs(lsfmux=x),
                                         empty_bitfile)
                nonrouting.fuzz_enum_setting(cfg, "{}.LSFXMUX{}".format(slicename, r), ["LUTG", "SUM", "FUNC5"],
                                         lambda x: get_substs(lsfxmux=x),
                                         empty_bitfile)


    fuzzloops.parallel_foreach(range(2,4), per_slice)


if __name__ == "__main__":
    main()
