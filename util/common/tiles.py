import re

pos_name_re = re.compile("x(\d+)y(\d+)")


def pos_from_name(tile, chip_size, bias):
    """
    Extract the tile position as a (row, column) tuple from its name
    """
    pos_match = pos_name_re.match(tile)
    return int(pos_match[1]), int(pos_match[2])


def type_from_fullname(tile):
    """
    Extract the type from a full tile name (in name:type) format
    """
    return tile.split(":")[1]
