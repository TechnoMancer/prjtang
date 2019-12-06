#! /usr/bin/env python3
"""
Fuzz the tile clock output routing for plb and pib tiles

This determines what the clock like tile signals can be output routed to.
This determines which of the CE, SR and CLK signals can be routed to the interconnect fabric and how.

Use tiles with at least 6 span neighbours in each direction to avoid finding
special case edge of grid pips.
"""
from fuzzconfig import FuzzConfig
import routing
import fuzzloops
import pytang

tile_loc = "x7y64"
cfg = FuzzConfig(job="TileClkOutputRouting", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc), "x8y64:pib"])

directions = ["e", "n","s", "w"]

destinations = [(1, "beg", 4), (2, "beg", 8), (6, "beg", 8)]
inputs = [("clk", 2),("ce", 4),("sr", 4)]

def main():
    pytang.load_database("../../../database")
    cfg.setup()
    empty_bitfile = cfg.build_design(cfg.pnl, {})
    cfg.pnl = "routing.pnl"

    def per_pip(pip):
        src, dst = pip
        def get_substs(tiles):
            routes = ""
            for tile in tiles:
                loc = tile.split(":")[0]
                route = loc + "_" + src + "." + loc + "_" + dst + "," + "\n"
                routes += route
            return dict(tile_loc=tile_loc,
                        route=routes)

        print("{}->{}".format(src, dst))
        #print(get_substs(cfg.tiles)["route"]))
        routing.fuzz_routing_pip(cfg, dst, src,
                            get_substs,
                            empty_bitfile)


    num_gclks = 16
    def gen_pips():
        for input in inputs:
            input, inp_num = input
            for input_int_num in range(inp_num):
                for dest_dir in directions:
                    for dest in destinations:
                        d_len, d_name, d_n = dest
                        for d_num in range(d_n):
                            src = "{}{}".format(input, input_int_num)
                            dest = "{}{}{}{}".format(dest_dir, d_len, d_name, d_num)
                            yield (src, dest)

    fuzzloops.parallel_foreach(gen_pips(), per_pip)


if __name__ == "__main__":
    main()
