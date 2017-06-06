from nose.tools import (assert_equal, assert_not_equal, assert_items_equal,
                        assert_almost_equal, raises, assert_true)
from nose.plugins.skip import Skip, SkipTest
import numpy.testing as npt

from test_helpers import data_filename

import openpathsampling as paths

from openpathsampling.engines.gromacs import *

import logging
import numpy as np


logging.getLogger('openpathsampling.initialization').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.ensemble').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.storage').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.netcdfplus').setLevel(logging.CRITICAL)

# check whether we have Gromacs 5 available; otherwise some tests skipped
# lazily use subprocess here; in case we ever change use of psutil
import subprocess
import os
devnull = open(os.devnull, 'w')
try:
    has_gmx = not subprocess.call(["gmx", "-version"], stdout=devnull,
                                  stderr=devnull)
except OSError:
    has_gmx = False
finally:
    devnull.close()


class TestGromacsEngine(object):
    # Files used (in test_data/gromacs_engine/)
    # conf.gro, md.mdp, topol.top : standard Gromacs input files
    # project_trr/0000000.trr : working file, 4 frames
    # project_trr/0000099.trr : 49 working frames, final frame partial
    def setup(self):
        self.test_dir = data_filename("gromacs_engine")
        self.engine = Engine(gro="conf.gro",
                             mdp="md.mdp",
                             top="topol.top",
                             options={},
                             base_dir=self.test_dir,
                             prefix="project")

    def test_read_frame_from_file_success(self):
        # when the frame is present, we should return it
        fname = os.path.join(self.test_dir, "project_trr", "0000000.trr")
        result = self.engine.read_frame_from_file(fname, 0)
        assert_true(isinstance(result, ExternalMDSnapshot))
        assert_equal(result.file_number, 0)
        assert_equal(result.file_position, 0)
        # TODO: add caching of xyz, vel, box; check that we have it now

        fname = os.path.join(self.test_dir, "project_trr", "0000000.trr")
        result = self.engine.read_frame_from_file(fname, 3)
        assert_true(isinstance(result, ExternalMDSnapshot))
        assert_equal(result.file_number, 0)
        assert_equal(result.file_position, 3)

    def test_read_frame_from_file_partial(self):
        # if a frame is partial, return 'partial'
        fname = os.path.join(self.test_dir, "project_trr", "0000099.trr")
        frame_2 = self.engine.read_frame_from_file(fname, 49)
        assert_true(isinstance(frame_2, ExternalMDSnapshot))
        frame_3 = self.engine.read_frame_from_file(fname, 50)
        assert_equal(frame_3, "partial")

    def test_read_frame_from_file_none(self):
        # if a frame is beyond the last frame, return None
        fname = os.path.join(self.test_dir, "project_trr", "0000000.trr")
        result = self.engine.read_frame_from_file(fname, 4)
        assert_equal(result, None)

    def test_write_frame_to_file_read_back(self):
        # write random frame; read back
        # sinfully, we start by reading in a frame to get the correct dims
        fname = os.path.join(self.test_dir, "project_trr", "0000000.trr")
        tmp = self.engine.read_frame_from_file(fname, 0)
        shape = tmp.xyz.shape
        xyz = np.random.randn(*shape)
        vel = np.random.randn(*shape)
        box = np.random.randn(3, 3)
        traj_50 = self.engine.trajectory_filename(50)
        # clear it out, in case it exists from a previous failed test
        if os.path.isfile(traj_50):
            os.remove(traj_50)
        snap = ExternalMDSnapshot(file_number=49, file_position=2,
                                  engine=self.engine)
        snap.set_details(xyz, vel, box)
        self.engine.write_frame_to_file(traj_50, snap)

        snap2 = self.engine.read_frame_from_file(traj_50, 0)
        assert_equal(snap2.file_number, 50)
        assert_equal(snap2.file_position, 0)
        npt.assert_array_almost_equal(snap.xyz, snap2.xyz)
        npt.assert_array_almost_equal(snap.velocities, snap2.velocities)
        npt.assert_array_almost_equal(snap.box_vectors, snap2.box_vectors)

        if os.path.isfile(traj_50):
            os.remove(traj_50)

    def test_set_filenames(self):
        test_engine = Engine(gro="conf.gro", mdp="md.mdp", top="topol.top",
                             options={}, prefix="proj")
        test_engine.set_filenames(0)
        assert_equal(test_engine.input_file, "initial_frame.trr")
        assert_equal(test_engine.output_file,
                     os.path.join("proj_trr", "0000001.trr"))
        assert_equal(test_engine.edr_file,
                     os.path.join("proj_edr", "0000001.edr"))
        assert_equal(test_engine.log_file,
                     os.path.join("proj_log", "0000001.log"))

        test_engine.set_filenames(99)
        assert_equal(test_engine.input_file, "initial_frame.trr")
        assert_equal(test_engine.output_file,
                     os.path.join("proj_trr", "0000100.trr"))
        assert_equal(test_engine.edr_file,
                     os.path.join("proj_edr", "0000100.edr"))
        assert_equal(test_engine.log_file,
                     os.path.join("proj_log", "0000100.log"))

    def test_engine_command(self):
        test_engine = Engine(gro="conf.gro", mdp="md.mdp", top="topol.top",
                             options={}, prefix="proj")
        test_engine.set_filenames(0)
        assert_equal(test_engine.engine_command(), "gmx mdrun -s topol.tpr "
                     + "-o proj_trr/0000001.trr -e proj_edr/0000001.edr "
                     + "-g proj_log/0000001.log ")

    def test_start_stop(self):
        if not has_gmx:
            raise SkipTest("Gromacs 5 (gmx) not found. Skipping test.")
        # run LengthEnsemble(3) with alanine dipeptide
        pass

    def test_prepare(self):
        if not has_gmx:
            raise SkipTest("Gromacs 5 (gmx) not found. Skipping test.")
        self.engine.set_filenames(0)
        files = ['topol.tpr', 'mdout.mdp']
        for f in files:
            if os.path.isfile(f):
                raise AssertionError("File " + str(f) + " already exists!")
        assert_equal(self.engine.prepare(), 0)
        for f in files:
            if not os.path.isfile(f):
                raise AssertionError("File " + str(f) + " was not created!")
        for f in files:
            os.remove(f)

    def test_open_file_caching(self):
        # read several frames from one file, then switch to another file
        # first read from 0000000, then 0000099
        pass
