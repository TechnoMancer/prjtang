#! /usr/bin/env python3
"""
Fuzz the register configuration for a plb.
This was originally adapted from the reg config fuzzer in project Trellis.
"""
from fuzzconfig import FuzzConfig
import nonrouting
import fuzzloops
import pytang

tile_loc = "x1y70"
cfg = FuzzConfig(job="PLBREG", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc)])

models = ["mslice", "mslice", "lslice", "lslice"]

def main():
    pytang.load_database("../../../database")
    cfg.setup()
    empty_bitfile = cfg.build_design(cfg.pnl, {})
    cfg.pnl = "reg.pnl"

    def per_slice(slicen):
        r = 0
        model = models[slicen]
        slicename = model.upper() + str(slicen)

        def get_substs(regset="RESET", sd="MI", cemux="CE", clkmux="CLK", srmux="SR", srmode="SYNC", dffmode="FF", gsr="ENABLE"):
            return dict(slice=str(slicen), r=str(r), model=model, tile_loc=tile_loc,
                        regset=regset,
                        sd=sd,
                        cemux=cemux,
                        clkmux=clkmux,
                        srmux=srmux,
                        srmode=srmode,
                        dffmode=dffmode,
                        gsr=gsr)

        for r in range(2):
            nonrouting.fuzz_enum_setting(cfg, "{}.REG{}.REGSET".format(slicename, r), ["RESET", "SET"],
                                         lambda x: get_substs(regset=x),
                                         empty_bitfile)
            nonrouting.fuzz_enum_setting(cfg, "{}.REG{}.SD".format(slicename, r), ["F", "FX", "MI"],
                                         lambda x: get_substs(sd=x),
                                         empty_bitfile)
        nonrouting.fuzz_enum_setting(cfg, "{}.CEMUX".format(slicename), ["0", "1", "CE", "INV"],
                                     lambda x: get_substs(cemux=x),
                                     empty_bitfile, include_zeros=False)
        nonrouting.fuzz_enum_setting(cfg, "{}.CLKMUX".format(slicename), ["CLK", "INV"],
                                     lambda x: get_substs(clkmux=x),
                                     empty_bitfile, include_zeros=False)
        nonrouting.fuzz_enum_setting(cfg, "{}.SRMUX".format(slicename), ["0", "1", "SR", "INV"],
                                     lambda x: get_substs(srmux=x),
                                     empty_bitfile, include_zeros=False)
        nonrouting.fuzz_enum_setting(cfg, "{}.SRMODE".format(slicename), ["SYNC", "ASYNC"],
                                     lambda x: get_substs(srmode=x),
                                     empty_bitfile)
        nonrouting.fuzz_enum_setting(cfg, "{}.DFFMODE".format(slicename), ["FF", "LATCH"],
                                     lambda x: get_substs(dffmode=x),
                                     empty_bitfile)
        nonrouting.fuzz_enum_setting(cfg, "{}.GSR".format(slicename), ["ENABLE", "DISABLE"],
                                     lambda x: get_substs(gsr=x),
                                     empty_bitfile)


    fuzzloops.parallel_foreach(range(4), per_slice)


if __name__ == "__main__":
    main()
