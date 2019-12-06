#! /usr/bin/env python3
"""
Fuzz the tile input routing for plb and pib tiles

Use tiles with at least 6 span neighbours in each direction to avoid finding
special case edge of grid pips.
"""
from fuzzconfig import FuzzConfig
import routing
import fuzzloops
import pytang

tile_loc = "x7y64"
cfg = FuzzConfig(job="TileInputRouting", family="eagle", device="eagle_s20", package="BG256", pnl="empty.pnl", tiles=["{}:plb".format(tile_loc), "x8y64:pib"])

directions = ["s", "w", "e", "n"]

inputs = [("a", 8),("b", 8),("c", 8),("d", 8),("mi", 8),("ce", 4),("sr", 4)]

offset = [0, 2]

endpoints = [(1, ["end"], 4), (2, ["mid","end"], 8), (6, ["mid", "end"], 8)]

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
        for input in inputs:
            input, inp_num = input
            for input_int_num in range(inp_num):
                for direction in directions:
                    for endpoint in endpoints:
                        length = endpoint[0]
                        for term in endpoint[1]:
                            for term_num in range(endpoint[2]):
                                dest = "{}{}".format(input, input_int_num)
                                src = "{}{}{}{}".format(direction, length, term, term_num)
                                yield (src, dest)
        input = "e"
        for input_int_num in range(4,8):
            for direction in directions:
                for endpoint in endpoints:
                    length = endpoint[0]
                    for term in endpoint[1]:
                        for term_num in range(endpoint[2]):
                            dest = "{}{}".format(input, input_int_num)
                            src = "{}{}{}{}".format(direction, length, term, term_num)
                            yield (src, dest)


    fuzzloops.parallel_foreach(gen_pips(), per_pip)


if __name__ == "__main__":
    main()
