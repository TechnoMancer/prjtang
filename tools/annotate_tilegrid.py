#!/usr/bin/env python3
"""
For each family and device, obtain a tilegrid and save it in the database
"""

import os
from os import path
import shutil

import database
import tangdinasty
import json

def annotate_eagle(tiles):
	for tilename, tile in tiles.items():
		type = tile["type"]
		if type in ["plb"]:
			tile["cols"] = 31
			tile["rows"] = 54
		if type in ["pib"]:
			tile["cols"] = 27
			tile["rows"] = 54
		if type.startswith("gclk_spine"):
			tile["rows"] = 8
		if type in ["miscs_mic_io_l","miscs_mic_io_r"]:
			tile["cols"] = 2
			tile["rows"] = 162
		if type in ["miscs_mic_io_b","miscs_mic_io_t"]:
			tile["cols"] = 4
			tile["rows"] = 54
		if type in ["emb_slice", "emb_32k"]:
			tile["cols"] = 2
			tile["rows"] = 486

def calc_locs_eagle(tiles, max_row, max_col):
    for tile_name, tile in tiles.items():
        y = tile["y"]
        x = tile["x"]
        tile["start_frame"] = tile["wl_beg"]
        tile["start_bit"] = tile["bl_beg"]
        if "rows" in tile:
            tile["start_frame"] = tile["wl_beg"]
            tile["start_bit"] = tile["bl_beg"]
            if y > 17:
                tile["start_bit"] += 6
            if y > 53:
                tile["start_bit"] += 6

def main():
	devices = database.get_devices()
	for family in devices["families"].keys():
		for device in devices["families"][family]["devices"].keys():
			selected_device = devices["families"][family]["devices"][device]
			package = selected_device["packages"][0]

			max_row = int(selected_device["max_row"])
			max_col = int(selected_device["max_col"])

			tiles = database.get_tilegrid(family, device)

			if family == "eagle":
				annotate_eagle(tiles)
				calc_locs_eagle(tiles, max_row, max_col)

			output_file = path.join(database.get_db_subdir(family, device), "tilegrid.json")
			with open(output_file, "wt") as fout:
				json.dump(tiles, fout, sort_keys=True, indent=4)

if __name__ == "__main__":
	main()
