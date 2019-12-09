"""
Utilities for fuzzing routing configuration. This is the counterpart to nonrouting.py

Adapted from Project Trellis interconnect fuzzing code.
"""

import threading
import tiles
import database
import pytang

import os
from os import path
from shutil import copyfile

def fuzz_routing_pip(config, dest, source, get_pnl_substs, empty_bitfile=None):
    """
    Fuzz a multi-bit setting, such as LUT initialisation

    :param config: FuzzConfig instance containing target device and tile of interest
    :param dest: dest of the setting to store in the database
    :param source: source for this routing pip
    :param get_pnl_substs: a callback function, that is first called with an array of bits to create a design with that setting
    :param empty_bitfile: a path to a bit file without the parameter included, optional, which is used to determine the
    default value
    """
    prefix = "thread{}_".format(threading.get_ident())
    logfile = path.join(config.workdir, prefix + "design.log")
    with open(logfile, "a") as logf:
        baseline_bitf = config.build_design(config.pnl, {}, prefix + "_base_")
        baseline_chip = pytang.Bitstream.read_bit(baseline_bitf).deserialise_chip()

        # Obtain the set of databases
        tile_dbs = {tile: pytang.get_tile_bitdata(
            pytang.TileLocator(config.family, config.device, tiles.type_from_fullname(tile))) for tile in
            config.tiles}

        # Build a bitstream and load it using libtrellis
        arc_bitf = config.build_design(config.pnl, get_pnl_substs(config.tiles), prefix)
        arc_chip = pytang.Bitstream.read_bit(arc_bitf).deserialise_chip()
        # Compare the bitstream with the arc to the baseline bitstream
        diff = arc_chip - baseline_chip
        if len(diff) == 0:
            # No difference means fixed interconnect
            # We consider this to be in the first tile if multiple tiles are being analysed
            # Do not do this for now since we do not have an a list of valid pips
            # TODO: Provide a callback or way to check if a pip should be included as a fixed connection.
            pass
            #if fc_predicate(arc, netnames):
                #norm_arc = normalise_arc_in_tile(config.tiles[0], arc)
                #fc = pytang.FixedConnection()
                #norm_arc = [fc_prefix + _ if not _.startswith("G_") else _ for _ in norm_arc]
                #norm_arc = [add_nonlocal_prefix(_) for _ in norm_arc]
                #fc.source, fc.sink = norm_arc
                #tile_dbs[config.tiles[0]].add_fixed_conn(fc)
        else:
            for tile in config.tiles:
                if tile in diff:
                    # Configurable interconnect in <tile>
                    ad = pytang.ArcData()
                    ad.source, ad.sink = (source, dest)
                    ad.bits = pytang.BitGroup(diff[tile])
                    tile_dbs[tile].add_mux_arc(ad)
        # Flush database to disk
        for tile, db in tile_dbs.items():
            db.save()
