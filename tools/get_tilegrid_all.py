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

def prepare_tcl(file_loc, out_file, device, package):
	with open(file_loc, "rt") as fin:
		with open(out_file, "wt") as fout:
			for line in fin:
				line = line.replace('{part}', device)
				line = line.replace('{package}', package)
				fout.write(line)

def prepare_pnl(family, device, package, max_row, max_col):
	tiles = ''
	for x in range(max_col):
		for y in range(max_row):
			tiles += '          x{}y{}_n1end0.x{}y{}_n1beg0\n'.format(x,y,x,y)      
	file_loc = path.join(database.get_tang_root(), "minitests", "tilegrid", "wire.pnl")
	with open(file_loc, "rt") as fin:
		with open("work_tilegrid/wire.pnl", "wt") as fout:
			for line in fin:
				line = line.replace('{architecture}', family)
				line = line.replace('{part}', device)
				line = line.replace('{package}', package)
				line = line.replace('{tiles}', tiles)
				fout.write(line)

def extract_elements(infile, tiles, max_row):
	with open(infile, "rt") as fin:
		for line in fin:				
			if (line.startswith('//')):
				inst = line.split(':')[1].split(',')[0]
				type = line.split('type=')[1].split(',')[0]
				wl_beg = line.split('wl_beg=')[1].split(',')[0]
				bl_beg = line.split('bl_beg=')[1].split(',')[0].rstrip('\n')
				loc = inst.split('_')[-1]
				val = loc.split('y')
				x = int(val[0].lstrip('x'))
				y = max_row - 1 - int(val[1])
				tile_name = loc + ":" + type
				current_tile = {
					"x": x,
					"y": y,
					"loc": loc,
					"inst": inst,
					"type": type,
					"wl_beg": int(wl_beg),
					"bl_beg": int(bl_beg),
					"sites": []
				}
				if tile_name not in tiles:
					tiles[tile_name] = current_tile
	
def extract_fuses(infile, family, device):
	frames = 0
	bits_per_frame = 0
	with open(infile, "rt") as fin:
		for line in fin:
			frames = frames + 1
			bits_per_frame = len(line.strip())
	data = {}
	data["frames"] = frames
	data["bits"] = bits_per_frame
	output_file = path.join(database.get_db_subdir(family, device), "fuses.json")
	with open(output_file, "wt") as fout:
		json.dump(data, fout, sort_keys=True, indent=4)


def main():
	devices = database.get_devices()
	for family in devices["families"].keys():
		for device in devices["families"][family]["devices"].keys():
			shutil.rmtree("work_tilegrid", ignore_errors=True)
			os.mkdir("work_tilegrid")
			selected_device = devices["families"][family]["devices"][device]
			package = selected_device["packages"][0]

			max_row = int(selected_device["max_row"])
			max_col = int(selected_device["max_col"])

			tiles = {}
			prepare_tcl(path.join(database.get_tang_root(), "minitests", "tilegrid", "wire.tcl"), "work_tilegrid/wire.tcl", device, package)
			prepare_pnl(family, device, package, max_row, max_col)
			tangdinasty.run("wire.tcl", "work_tilegrid", stdout=True)
			extract_elements("work_tilegrid/wire.log", tiles, max_row)
			
			file_loc = path.join(database.get_tang_root(), "minitests", "tilegrid", device + ".v")
			if os.path.exists(file_loc):
				shutil.copyfile(file_loc,path.join("work_tilegrid", device + ".v"))
				prepare_tcl(path.join(database.get_tang_root(), "minitests", "tilegrid", "specific.tcl"), "work_tilegrid/specific.tcl", device, package)
				tangdinasty.run("specific.tcl", "work_tilegrid", stdout=True)
				extract_elements("work_tilegrid/" + device + ".log", tiles, max_row)

			output_file = path.join(database.get_db_subdir(family, device), "tilegrid.json")
			with open(output_file, "wt") as fout:
				json.dump(tiles, fout, sort_keys=True, indent=4)
			extract_fuses("work_tilegrid/wire.fuse", family, device)

if __name__ == "__main__":
	main()
