"""
Helper routines for parsing CHIME data archive records

.. currentmodule:: chimedb.data_index.util

This module contains utility routines for parsing CHIME data archive metadata


Routines
========

.. autosummary::
    :toctree: generated/

    detect_file_type
    md5sum_file
    parse_acq_name
    parse_corrfile_name
    parse_hfbfile_name
    parse_hkfile_name
    parse_weatherfile_name
    populate_types
"""
# === Start Python 2/3 compatibility
from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *  # noqa  pylint: disable=W0401, W0614
from future.builtins.disabled import *  # noqa  pylint: disable=W0401, W0614

# === End Python 2/3 compatibility

from past.builtins import basestring
import chimedb.core as db
import os
import peewee as pw
import re

from . import orm

# Global variables
# ================

fname_atmel = "atmel_id.dat"

_fmt_acq = re.compile("([0-9]{8})T([0-9]{6})Z_([A-Za-z0-9]*)_([A-Za-z]*)")
_fmt_corr = re.compile("([0-9]{8})_([0-9]{4})\.h5")
_fmt_hfb = re.compile("hfb_([0-9]{8})_([0-9]{4})\.h5")
_fmt_hk = re.compile("([A-Za-z]*)_([0-9]{8})\.h5")
_fmt_hkp = re.compile("hkp_prom_([0-9]{8})\.h5")
_fmt_atmel = re.compile("atmel_id\.dat")
_fmt_log = re.compile("ch_(master|hk)\.log")
_fmt_rawadc = re.compile("rawadc\.npy")
_fmt_rawadc_hist = re.compile("histogram_chan([0-9]{1,2})\.pdf")
_fmt_rawadc_spec = re.compile("spectrum_chan([0-9]{1,2})\.pdf")
_fmt_rawadc_h5 = re.compile("[0-9]{6}\.h5")
_fmt_raw_gains = re.compile("(gains|gains_noisy)\.pkl")
_fmt_weather = re.compile("(20[12][0-9][01][0-9][0123][0-9])\.h5")
_fmt_calib_data = re.compile(r"\d{8}\.h5")
_fmt_misc_tar = re.compile(
    "([0-9]{8})_([A-Za-z][A-Za-z0-9_+-]*)\.misc\.tar(?:\.gz|\.bz2|\.xz)"
)


# Routines for setting up the database
# ====================================


def populate_types():
    """Populate the AcqType, FileType and StorageGroup tables with standard
    entries."""

    with db.proxy.atomic():
        for t in [
            {
                "id": 1,
                "name": "corr",
                "notes": "Traditionally hand-tooled correlation products from a correlator.",
            },
            {"id": 2, "name": "hk", "notes": "Housekeeping data."},
            {
                "id": 3,
                "name": "rawadc",
                "notes": "Raw ADC data taken for testing the status of a correlator.",
            },
            {
                "id": 5,
                "name": "weather",
                "notes": "Weather data scraped from the wview archive provided by DRAO.",
            },
            {
                "id": 6,
                "name": "hkp",
                "notes": "New prometheus based scheme for recording housekeeping data.",
            },
            {
                "id": 7,
                "name": "digitalgain",
                "notes": "FPGA digital gains from the F-Engine.",
            },
            {
                "id": 8,
                "name": "gain",
                "notes": "Complex gains from the calibration broker.",
            },
            {
                "id": 9,
                "name": "flaginput",
                "notes": "Good correlator input flags from the flagging broker.",
            },
            {"id": 10, "name": "misc", "notes": "Miscellaneous data products."},
            {
                "id": 11,
                "name": "hfb",
                "notes": "21cm absorber (Hyper Fine Beam) data taken from a correlator.",
            },
        ]:
            if not orm.AcqType.select().where(orm.AcqType.name == t["name"]).count():
                orm.AcqType.insert(**t).execute()

    with db.proxy.atomic():
        for t in [
            {
                "id": 1,
                "name": "corr",
                "notes": "Traditionally hand-tooled correlation products from a correlator.",
            },
            {
                "id": 2,
                "name": "log",
                "notes": "A human-readable log file produced by acquisition software.",
            },
            {"id": 3, "name": "hk", "notes": "A housekeeping file."},
            {
                "id": 4,
                "name": "atmel_id",
                "notes": "A short file listing the ATMEL ID's and human readable names in an HK acquisition.",
            },
            {
                "id": 5,
                "name": "rawadc",
                "notes": "A python numpy array with raw ADC values.",
            },
            {"id": 6, "name": "pdf", "notes": "A portable document file."},
            {"id": 10, "name": "weather", "notes": "DRAO weather data."},
            {
                "id": 11,
                "name": "hkp",
                "notes": "Archive of the prometheus housekeeping data.",
            },
            {"id": 12, "name": "calibration", "notes": "Calibration data products."},
            {
                "id": 13,
                "name": "miscellaneous",
                "notes": "A tarball of miscellaneous data files.",
            },
            {
                "id": 14,
                "name": "hfb",
                "notes": "21cm absorber (Hyper Fine Beam) data taken from a correlator.",
            },
        ]:
            if not orm.FileType.select().where(orm.FileType.name == t["name"]).count():
                orm.FileType.insert(**t).execute()


# Helper routines for adding files
# ================================


def md5sum_file(filename, hr=True, cmd_line=False):
    """Find the md5sum of a given file.

    Output should reproduce that of UNIX md5sum command.

    Parameters
    ----------
    filename: string
        Name of file to checksum.
    hr: boolean, optional
        Should output be a human readable hexstring (default is True).
    cmd_line: boolean, optional
        If True, then simply do an os call to md5sum (default is False).

    See Also
    --------
    http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-
    python
    """
    if cmd_line:
        p = os.popen("md5sum %s 2> /dev/null" % filename, "r")
        res = p.read()
        p.close()
        md5 = res.split()[0]
        assert len(md5) == 32
        return md5
    else:
        import hashlib

        block_size = 256 * 128

        md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(block_size), b""):
                md5.update(chunk)
        if hr:
            return md5.hexdigest()
        return md5.digest()


def parse_acq_name(name):
    """Validate and parse an acquisition name.

    Parameters
    ----------
    name : The name of the acquisition.

    Returns
    -------
    A tuple of timestamp, instrument and type.

    """
    if not re.match(_fmt_acq, name):
        raise db.ValidationError('Bad acquisition name format for "%s".' % name)
    ret = tuple(name.split("_"))
    if len(ret) != 3:
        raise db.ValidationError('Bad acquisition name format for "%s".' % name)
    return ret


def parse_corrfile_name(name):
    """Validate and parse a correlation file name.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    A tuple of seconds from start and freqency index.
    """
    m = re.match(_fmt_corr, name)
    if not m:
        raise db.ValidationError('Bad correlator file name format for "%s".' % name)

    return int(m.group(1)), int(m.group(2))


def parse_hfbfile_name(name):
    """Validate and parse a HFB file name.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    A tuple of seconds from start and freqency index.
    """
    m = re.match(_fmt_hfb, name)
    if not m:
        raise db.ValidationError('Bad HFB file name format for "%s".' % name)

    return int(m.group(1)), int(m.group(2))


def parse_weatherfile_name(name):
    """Validate and parse a weather file name.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    The date string, of format YYYYMMDD.
    """
    m = re.match(_fmt_weather, name)
    if not m:
        raise db.ValidationError('Bad weather file name format for "%s".' % name)

    return name[0:8]


def parse_miscfile_name(name):
    """Validate and parse a misc file name.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    A tuple of containing the eight-digit serial number and the misc data
    type.
    """
    m = re.match(_fmt_misc_tar, name)
    if not m:
        raise db.ValidationError(
            'Bad miscellaneous file name format for "{0}".'.format(name)
        )
    return int(m.group(1)), m.group(2)


def parse_hkfile_name(name):
    """Validate and parse a correlation file name.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    A tuple of seconds from start and the ATMEL name.
    """
    m = re.match(_fmt_hk, name)
    if not m:
        raise db.ValidationError('Bad correlator file name format for "%s".' % name)

    return int(m.group(2)), m.group(1)


def detect_file_type(name):
    """Figure out what kind of file this is.

    Parameters
    ----------
    name : The name of the file.

    Returns
    -------
    An object of FileType, or None if unrecognised.

    """

    if re.match(_fmt_corr, name):
        return orm.FileType.get(name="corr")
    elif re.match(_fmt_hfb, name):
        return orm.FileType.get(name="hfb")
    elif re.match(_fmt_hk, name):
        return orm.FileType.get(name="hk")
    elif re.match(_fmt_hkp, name):
        return orm.FileType.get(name="hkp")
    elif re.match(_fmt_log, name):
        return orm.FileType.get(name="log")
    elif re.match(_fmt_atmel, name):
        return orm.FileType.get(name="atmel_id")
    elif re.match(_fmt_rawadc, name) or re.match(_fmt_rawadc_h5, name):
        return orm.FileType.get(name="rawadc")
    elif re.match(_fmt_rawadc_hist, name) or re.match(_fmt_rawadc_spec, name):
        return orm.FileType.get(name="pdf")
    elif re.match(_fmt_raw_gains, name):
        return orm.FileType.get(name="pkl")
    elif re.match(_fmt_weather, name):
        return orm.FileType.get(name="weather")
    elif re.match(_fmt_calib_data, name):
        return orm.FileType.get(name="calibration")
    elif re.match(_fmt_misc_tar, name):
        return orm.FileType.get(name="miscellaneous")
    else:
        return None
