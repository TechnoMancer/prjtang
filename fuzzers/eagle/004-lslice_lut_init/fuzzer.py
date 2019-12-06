#! /usr/bin/env python3
"""
Fuzz the initialisation bits for the LSLICE LUTs.
The LSLICE has four LUT4s where the F and G LUTs for each half can be combined into a LUT5 or used as two LUT4s which share inputs.
This was originally adapted from the lut init fuzzer in project Trellis.
"""
from fuzzconfig import FuzzConfig
import nonrouting
import fuzzloops
import pytang
import re

tile_loc = "x1y70"

cfg = FuzzConfig(job="lsliceLUTInit", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc)])


def get_lut_function(init_bits):
    sop_terms = []
    lut_inputs = ["A", "B", "C", "D"]
    for i in range(16):
        if init_bits[i]:
            p_terms = []
            for j in range(4):
                if i & (1 << j) != 0:
                    p_terms.append(lut_inputs[j])
                else:
                    p_terms.append("~" + lut_inputs[j])
            sop_terms.append("({})".format("*".join(p_terms)))
    if len(sop_terms) == 0:
        lut_func = "0"
    else:
        lut_func = "+".join(sop_terms)
    return lut_func


def main():
    pytang.load_database("../../../database")

    cfg.setup()
    empty_bitfile = cfg.build_design(cfg.pnl, {})
    cfg.pnl = "lut.pnl"

    def per_slice(slicen):
        for lut in ["F", "G"]:
            for k in range(2):
                def get_substs(bits):
                    return dict(slice=slicen, k=str(k), lut=lut, lut_func=get_lut_function(bits), tile_loc=tile_loc)
                nonrouting.fuzz_word_setting(cfg, "LSLICE{}.LUT{}{}.INIT".format(slicen, lut, k), 16, get_substs, empty_bitfile)

    fuzzloops.parallel_foreach([2, 3], per_slice)

if __name__ == "__main__":
    main()
