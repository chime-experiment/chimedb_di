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
import os
import peewee as pw
import re

from . import orm

# Global variables
# ================

fname_atmel = "atmel_id.dat"

_fmt_acq = re.compile("([0-9]{8})T([0-9]{6})Z_([A-Za-z0-9]*)_([A-Za-z]*)")
_fmt_corr = re.compile("([0-9]{8})_([0-9]{4}).h5")
_fmt_hk = re.compile("([A-Za-z]*)_([0-9]{8}).h5")
_fmt_hkp = re.compile("hkp_prom_([0-9]{8}).h5")
_fmt_atmel = re.compile("atmel_id\.dat")
_fmt_log = re.compile("ch_(master|hk)\.log")
_fmt_rawadc = re.compile("rawadc\.npy")
_fmt_rawadc_hist = re.compile("histogram_chan([0-9]{1,2})\.pdf")
_fmt_rawadc_spec = re.compile("spectrum_chan([0-9]{1,2})\.pdf")
_fmt_rawadc_h5 = re.compile("[0-9]{6}.h5")
_fmt_raw_gains = re.compile("(gains|gains_noisy)\.pkl")
_fmt_weather = re.compile("(20[12][0-9][01][0-9][0123][0-9]).h5")
_fmt_calib_data = re.compile(r"\d{8}\.h5")


# Routines for setting up the database
# ====================================


def populate_types():
    """Populate the AcqType, FileType and StorageGroup tables with standard
    entries."""

    for t in ["corr", "rawadc", "hk", "raw", "weather", "hkp"]:
        if not orm.AcqType.select().where(orm.AcqType.name == t).count():
            orm.AcqType.insert(name=t).execute()

    for t in [
        "corr",
        "raw",
        "log",
        "hk",
        "atmel_id",
        "rawadc",
        "pdf",
        "gains",
        "settings",
        "weather",
        "hkp",
        "calibration",
    ]:
        if not orm.FileType.select().where(orm.FileType.name == t).count():
            orm.FileType.insert(name=t).execute()

    for g in ["collection_server"]:
        if not orm.StorageGroup.select().where(orm.StorageGroup.name == g).count():
            orm.StorageGroup.insert(name=g).execute()


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

    return int(m.group(1).lstrip("0") or "0"), int(m.group(2).lstrip("0") or "0")


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

    return int(m.group(2).lstrip("0") or "0"), m.group(1)


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
    else:
        return None
