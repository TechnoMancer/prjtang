#!/usr/bin/env python3
"""
Project Tang Master HTML Generation Script

Usage:
html_all.py <output_folder>
"""

import os, sys, time
from os import path
from string import Template
import argparse
import database
import html_tilegrid
import html_bits
import pytang

tang_docs_index = """
<html>
<head>
<title>Project Tang HTML Documentation</title>
</head>
<body>
<h1>Project Tang HTML Documentation</h1>
<p>Project Tang is a project to document the Anlogic bitstream and internal architecture.</p>
<p>This repository contains HTML documentation automatically generated from the
<a href="https://github.com/mmicko/prjtang">Project Tang</a> database.
Data generated includes tilemap data and bitstream data for many tile types. Click on any tile to see its bitstream
documentation.
</p>

<p>This HTML documentation was generated at ${datetime} from prjtang commit
<a href="https://github.com/mmicko/prjtang/tree/${commit}">${commit}</a>.</p>
<hr/>
$docs_toc
<hr/>
<p>Licensed under a very permissive <a href="COPYING">CC0 1.0 Universal</a> license.</p>
</body>
</html>
"""

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('fld', type=str,
                    help="output folder")


def generate_device_docs(family, device, folder):
    html_tilegrid.main(["html_tilegrid", family, device, path.join(folder, "index.html")])


def generate_tile_docs(family, device, tile, folder):
    html_bits.main(["html_bits", family, device, tile, path.join(folder, "{}.html".format(tile))])


def get_device_tiles(family, devices):
    all_tiles = set()
    fd_tiles = {}
    for dev, devdata in sorted(devices.items()):
        if "fuzz" in devdata and devdata["fuzz"]:
            fd_tiles[family, dev] = []
            c = pytang.Chip(dev)
            for tile in c.get_all_tiles():
                tt = tile.info.type
                if tt not in all_tiles:
                    all_tiles.add(tt)
                    fd_tiles[family, dev].append(tt)
    return fd_tiles


def main(argv):
    args = parser.parse_args(argv[1:])
    if not path.exists(args.fld):
        os.mkdir(args.fld)
    commit_hash = database.get_db_commit()
    build_dt = time.strftime('%Y-%m-%d %H:%M:%S')
    docs_toc = ""
    pytang.load_database(database.get_db_root())
    for fam, fam_data in sorted(database.get_devices()["families"].items()):
        fdir = path.join(args.fld, fam)
        if not path.exists(fdir):
            os.mkdir(fdir)
        thdir = path.join(fdir, "tilehtml")
        if not path.exists(thdir):
            os.mkdir(thdir)
        docs_toc += "<h3>{} Family</h3>".format(fam)
        docs_toc += "<h4>Bitstream Documentation</h4>"
        docs_toc += "<ul>"
        tiles = get_device_tiles(fam, fam_data["devices"])
        for dev, devdata in sorted(fam_data["devices"].items()):
            if "fuzz" in devdata and devdata["fuzz"]:
                ddir = path.join(fdir, dev)
                if not path.exists(ddir):
                    os.mkdir(ddir)
                print("********* Generating documentation for device {}".format(dev))
                generate_device_docs(fam, dev, ddir)
                if (fam, dev) in tiles:
                    for tile in tiles[fam, dev]:
                        print("*** Generating documentation for tile {}".format(tile))
                        generate_tile_docs(fam, dev, tile, thdir)
                docs_toc += '<li><a href="{}">{} Documentation</a></li>'.format(
                    '{}/{}/index.html'.format(fam, dev),
                    dev
                )

        docs_toc += "</ul>"

    index_html = Template(tang_docs_index).substitute(
        datetime=build_dt,
        commit=commit_hash,
        docs_toc=docs_toc
    )
    with open(path.join(args.fld, "index.html"), 'w') as f:
        f.write(index_html)


if __name__ == "__main__":
    main(sys.argv)
