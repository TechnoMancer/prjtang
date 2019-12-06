"""
This module provides a structure to define the fuzz environment

Adapted from Project Trellis
"""
import os
from os import path
from string import Template
import tangdinasty
import database


class FuzzConfig:
    def __init__(self, job, family, device, package, tiles, pnl):
        """
        :param job: user-friendly job name, used for folder naming etc
        :param family: Target family name
        :param device: Target device name
        :param tiles: List of tiles to consider during fuzzing
        :param pnl: Minimal PNL file to use as a base for interconnect fuzzing
        """
        self.job = job
        self.family = family
        self.device = device
        self.package = package
        self.tiles = tiles
        self.pnl = pnl

    @property
    def workdir(self):
        return path.join(".", "work", self.job)

    def make_workdir(self):
        """Create the working directory for this job, if it doesn't exist already"""
        os.makedirs(self.workdir, exist_ok=True)

    def setup(self, skip_specimen=False):
        """
        Create a working directory, and run Diamond on a minimal pnl file to create a ncd/prf for Tcl usage
        """
        self.make_workdir()
        if not skip_specimen:
            self.build_design(self.pnl, {})

    def build_design(self, des_template, substitutions, prefix="", substitute=True):
        """
        Run Tang Dynasty on a given design template, applying a map of substitutions, plus some standard substitutions
        if not overriden.

        :param des_template: path to template PNL/Verilog file
        :param substitutions: dictionary containing template subsitutions to apply to PNL/Verilog file
        :param prefix: prefix to append to filename, for running concurrent jobs without collisions

        Returns the path to the output bitstream
        """
        subst = dict(substitutions)
        if "route" not in subst:
            subst["route"] = ""
        if "sysconfig" not in subst:
            subst["sysconfig"] = ""
        if "part" not in subst:
            subst["part"] = self.device
        if "package" not in subst:
            subst["package"] = self.package
        ext = des_template.split(".")[-1]
        tcl_template = des_template.replace("." + ext, ".tcl")
        if not path.exists(tcl_template):
            tcl_template = path.join(database.get_tang_root(), "templates/pnl2bit.tcl")

        desfile = path.join(self.workdir, prefix + "design." + ext)
        if ext == "pnl" and "pnl_file" not in subst:
            subst["pnl_file"] = path.relpath(desfile, self.workdir)
        if ext == "v" and "v_file" not in subst:
            subst["v_file"] = path.relpath(desfile, self.workdir)
        bitfile = path.join(self.workdir, prefix + "design.bit")
        subst["bit_file"] = path.relpath(bitfile, self.workdir)
        tclfile = path.join(self.workdir, prefix + "design.tcl")

        if path.exists(bitfile):
            os.remove(bitfile)
        with open(des_template, "r") as inf:
            with open(desfile, "w") as ouf:
                if substitute:
                    ouf.write(Template(inf.read()).substitute(**subst))
                else:
                    ouf.write(inf.read())
        with open(tcl_template, "r") as inf:
            with open(tclfile, "w") as ouf:
                if substitute:
                    ouf.write(Template(inf.read()).substitute(**subst))
                else:
                    ouf.write(inf.read())
        tangdinasty.run(path.relpath(tclfile, self.workdir), self.workdir)
        return bitfile
