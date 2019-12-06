#! /usr/bin/env python3
"""
Fuzz the modes for slices in a plb

This was originally adapted from a fuzzer in project Trellis.
"""
from fuzzconfig import FuzzConfig
import nonrouting
import fuzzloops
import pytang

tile_loc = "x1y70"
cfg = FuzzConfig(job="PLBMODE", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc)])

models = ["mslice", "mslice", "lslice", "lslice"]
slice_modes = { "mslice": ["LOGIC","RIPPLE", "DPRAM"],
                "lslice": ["LOGIC","RIPPLE", "RAMW"]
              }

def main():
    pytang.load_database("../../../database")
    cfg.setup()
    empty_bitfile = cfg.build_design(cfg.pnl, {})
    cfg.pnl = "modes.pnl"

    def per_slice(slicen):
        slicename = models[slicen].upper() + str(slicen)
        def get_substs(mode="LOGIC"):
            return dict(slice=str(slicen), model=models[slicen], tile_loc=tile_loc, mode=mode)
        modes=slice_modes[models[slicen]]
        nonrouting.fuzz_enum_setting(cfg, "{}.MODE".format(slicename), modes,
                                     lambda x: get_substs(mode=x),
                                     empty_bitfile, True)

    fuzzloops.parallel_foreach(range(4), per_slice)


if __name__ == "__main__":
    main()
