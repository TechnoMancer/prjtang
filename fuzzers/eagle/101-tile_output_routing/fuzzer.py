#! /usr/bin/env python3
"""
Fuzz the tile output routing for plb and pib tiles

This also fuzzes the connections of the local wires to the interconnect

Use tiles with at least 6 span neighbours in each direction to avoid finding
special case edge of grid pips.
"""
from fuzzconfig import FuzzConfig
import routing
import fuzzloops
import pytang

tile_loc = "x7y64"
cfg = FuzzConfig(job="TileOutputRouting", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc), "x8y64:pib"])

outputs = ["f", "fx", "q", "local"]

directions = ["e", "n","s", "w"]
sources = [(1, ["end"], 4), (2, ["mid","end"], 8), (6, ["mid", "end"], 8)]
destinations = [(1, "beg", 4), (2, "beg", 8), (6, "beg", 8)]

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



    def gen_pips():
        for dest_dir in directions:
            for dest in destinations:
                d_len, d_name, d_n = dest
                for d_num in range(d_n):
                    for output in outputs:
                        for out_num in range(8):
                            dest = "{}{}{}{}".format(dest_dir, d_len, d_name, d_num)
                            src = "{}{}".format(output, out_num)
                            yield (src, dest)

    fuzzloops.parallel_foreach(gen_pips(), per_pip)


if __name__ == "__main__":
    main()
