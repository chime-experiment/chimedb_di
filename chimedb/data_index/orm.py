"""
Table definitions for the alpenhorn data index
"""
# === Start Python 2/3 compatibility
from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *  # noqa  pylint: disable=W0401, W0614
from future.builtins.disabled import *  # noqa  pylint: disable=W0401, W0614

# === End Python 2/3 compatibility

from chimedb.core.orm import base_model, name_table, EnumField, JSONDictField

import peewee as pw

# Logging
# =======

import logging

_logger = logging.getLogger("chimedb")
_logger.addHandler(logging.NullHandler())


# Tables pertaining to the data index.
# ====================================


class ArchiveInst(base_model):
    """Instrument that took the data.

    Attributes
    ----------
    name : string
        Name of instrument.
    """

    name = pw.CharField(max_length=64)
    notes = pw.TextField(null=True)


class AcqType(name_table):
    """The type of data that is being taken in the acquisition.

    Attributes
    ----------
    name : string
        Short name of type. e.g. `raw`, `vis`
    notes : string
        Human-readable description
    """

    name = pw.CharField(max_length=64)
    notes = pw.TextField(null=True)

    @classmethod
    def corr(cls):
        """For getting the correlator acquisition type."""
        return cls.from_name("corr")

    @classmethod
    def hk(cls):
        """For getting the housekeeping acquisition type."""
        return cls.from_name("hk")

    @classmethod
    def weather(cls):
        """For getting the weather acquisition type."""
        return cls.from_name("weather")

    @classmethod
    def rawadc(cls):
        """For getting the rawadc acquisition type."""
        return cls.from_name("rawadc")

    @classmethod
    def gain(cls):
        """For getting the calibrationgain acquisition type."""
        return cls.from_name("gain")

    @classmethod
    def flaginput(cls):
        """For getting the flaginput acquisition type."""
        return cls.from_name("flaginput")

    @classmethod
    def digitalgain(cls):
        """For getting the digitalgain acquisition type."""
        return cls.from_name("digitalgain")


class ArchiveAcq(base_model):
    """Describe the acquisition.

    Attributes
    ----------
    name : string
        Name of acquisition.
    inst : foreign key
        Reference to the instrument that took the acquisition.
    type : foreign key
        Reference to the data type type.
    comment : string

    Properties
    ----------
    timed_files
    n_timed_files
    """

    name = pw.CharField(max_length=64)
    inst = pw.ForeignKeyField(ArchiveInst, backref="acqs")
    type = pw.ForeignKeyField(AcqType, backref="acqs")
    comment = pw.TextField(null=True)

    @property
    def corr_files(self):
        return self.files.join(CorrFileInfo)

    @property
    def hk_files(self):
        return self.files.join(HKFileInfo)

    @property
    def weather_files(self):
        return self.files.join(WeatherFileInfo)

    @property
    def misc_files(self):
        return self.files.join(MiscFileInfo)

    @property
    def rawadc_files(self):
        return self.files.join(RawadcFileInfo)

    @property
    def timed_files(self):
        return self.corr_files | self.hk_files | self.weather_files | self.rawadc_files

    @property
    def n_timed_files(self):
        return (
            self.corr_files.count() + self.hk_files.count() + self.weather_files.count()
        )

    @property
    def finish_time(self):
        finish = -1e99
        for model in file_info_table:
            this_finish = (
                self.files.select(pw.fn.Max(model.finish_time)).join(model).scalar()
            )
            finish = max(finish, this_finish or -1e99)
        return finish

    @property
    def start_time(self):
        start = 1e99
        for model in file_info_table:
            this_start = (
                self.files.select(pw.fn.Min(model.start_time)).join(model).scalar()
            )
            start = min(start, this_start or 1e99)
        return start


class CorrAcqInfo(base_model):
    """Information about a correlation acquisition.

    Attributes
    ----------
    acq : foreign key
        Reference to the acquisition that the information is for.
    integration : float
        Integration time in seconds.
    nfreq : integer
        Number of frequency channels.
    nprod : integer
        Number of correlation products in acquisition.

    """

    acq = pw.ForeignKeyField(ArchiveAcq, backref="corrinfos")
    integration = pw.DoubleField(null=True)
    nfreq = pw.IntegerField(null=True)
    nprod = pw.IntegerField(null=True)


class HKAcqInfo(base_model):
    """Information about a housekeeping acquisition.
    There should be one of these for each ATMEL board in the acquisition.

    Attributes
    ----------
     acq : foreign key
           Reference to the acquisition that the information is for.
    atmel_id : string
           The eleven-digit ATMEL ID number.
    atmel_name : string
           The human-readable name of the ATMEL board.
    """

    acq = pw.ForeignKeyField(ArchiveAcq, backref="hkinfos")
    atmel_id = pw.CharField(max_length=64)
    atmel_name = pw.CharField(max_length=64)


class RawadcAcqInfo(base_model):
    """Information about a raw ADC acquisition.

    Attributes
    ----------
    acq : foreign key
           Reference to the acquisition that the information is for.
    start_time : double
           When the raw ADC acquisition was performed, in UNIX time.
    """

    acq = pw.ForeignKeyField(ArchiveAcq, backref="rawadcinfos")
    start_time = pw.DoubleField(null=True)


class FileType(base_model):
    """A file type.

    Attributes
    ----------
    name : string
        The name of this file type.
    notes: string
        Any notes or comments about this file type.
    """

    name = pw.CharField(max_length=64)
    notes = pw.TextField(null=True)


class ArchiveFile(base_model):
    """A file in an acquisition.

    Attributes
    ----------
    acq : foreign key
        Reference to the acquisition this file is part of.
    type : foreign key
        Reference to the type of file that this is.
    name : string
        Name of the file.
    size_b : integer
        Size of file in bytes.
    md5sum : string
        md5 checksum of file. Used for verifying integrity.
    """

    acq = pw.ForeignKeyField(ArchiveAcq, backref="files")
    type = pw.ForeignKeyField(FileType, backref="files")
    name = pw.CharField(max_length=64)
    size_b = pw.BigIntegerField(null=True)
    md5sum = pw.CharField(null=True, max_length=32)


class CorrFileInfo(base_model):
    """Information about a correlation data file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    chunk_number : integer
        Label for where in the acquisition this file is.
    freq_number : integer
        Which frequency slice this file is.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="corrinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    chunk_number = pw.IntegerField(null=True)
    freq_number = pw.IntegerField(null=True)


class HKFileInfo(base_model):
    """Information about a housekeeping data file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    atmel_name : string
        The human readable name of this ATMEL board.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="hkinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    atmel_name = pw.CharField(max_length=64)
    chunk_number = pw.IntegerField(null=True)


class HKPFileInfo(base_model):
    """Information about a housekeeping data file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    atmel_name : string
        The human readable name of this ATMEL board.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="hkpinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)


class DigitalGainFileInfo(base_model):
    """Information about a digital gain data file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="digitalgaininfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)


class CalibrationGainFileInfo(base_model):
    """Information about a gain data file from the calibration broker.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="calibrationgaininfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)


class FlagInputFileInfo(base_model):
    """Information about a flag input data file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="flaginputinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)


class RawadcFileInfo(base_model):
    """Information about a raw ADC sample file.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="rawadcinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)


class WeatherFileInfo(base_model):
    """Information about DRAO weather data.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    date : string
        The date of the weather data, in the form YYYYMMDD.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="weatherinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    date = pw.CharField(null=True, max_length=8)


class MiscFileInfo(base_model):
    """Information about miscellaneous data tarballs.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    data_type : string
        The miscellaneous data type.
    metdata : dict
        Metadata describing the data in the tarball.  Extracted from the
        METADATA.json file.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="miscinfos")
    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    data_type = pw.CharField()
    metadata = JSONDictField()


# List of info models, used in some local code.
file_info_table = [
    CorrFileInfo,
    HKFileInfo,
    WeatherFileInfo,
    RawadcFileInfo,
    HKPFileInfo,
    DigitalGainFileInfo,
    CalibrationGainFileInfo,
    FlagInputFileInfo,
    MiscFileInfo,
]


class StorageGroup(base_model):
    """Storage group for the archive.

    Attributes
    ----------
    name : string
        The name of the group
    small_size : integer
        The threshold size (in bytes) for small files.
        Ignored if small_group is not also defined.
    small_group : foreign key
        The StorageGroup used for small-file storage, or None.
    notes : string
        Any notes about this storage group.
    """

    name = pw.CharField(max_length=64)
    small_size = pw.IntegerField(default=0)
    small_group = pw.ForeignKeyField('self', backref="large_group", null=True)
    notes = pw.TextField(null=True)


class StorageNode(base_model):
    """A path on a disc where archives are stored.

    Attributes
    ----------
    name : string
        The name of this node.
    root : string
        The root directory for data in this node.
    host : string
        The hostname that this node lives on.
    address : string
        The internet address for the host (e.g., mistaya.phas.ubc.ca)
    group : foreign key
        The group to which this node belongs.
    mounted : bool
        Is the node mounted?
    auto_import : bool
        Should files that appear on this node be automatically added?
    suspect : bool
        Could this node be corrupted?
    storage_type : enum
        What is the type of storage?
        - 'A': archive for the data
        - 'T': for transiting data
        - 'F': for data in the field (i.e acquisition machines)
    max_total_gb : float
        The maximum amout of storage we should use.
    min_avail_gb : float
        What is the minimum amount of free space we should leave on this node?
    avail_gb : float
        How much free space is there on this node?
    avail_gb_last_checked : datetime
        When was the amount of free space last checked?
    min_delete_age_days : float
        What is the minimum amount of time a file must remain on the node before
        we are allowed to delete it?
    notes : string
        Any notes or comments about this node.
    """

    name = pw.CharField(max_length=64)
    root = pw.CharField(max_length=255, null=True)
    host = pw.CharField(max_length=64, null=True)
    username = pw.CharField(max_length=64, null=True)
    address = pw.CharField(max_length=255, null=True)
    group = pw.ForeignKeyField(StorageGroup, backref="nodes")
    mounted = pw.BooleanField(default=False)
    auto_import = pw.BooleanField(default=False)
    suspect = pw.BooleanField(default=False)
    storage_type = EnumField(["A", "T", "F"], default="A")
    max_total_gb = pw.FloatField(default=-1.0)
    min_avail_gb = pw.FloatField()
    avail_gb = pw.FloatField(null=True)
    avail_gb_last_checked = pw.DateTimeField(null=True)
    min_delete_age_days = pw.FloatField(default=30)
    notes = pw.TextField(null=True)


class ArchiveFileCopy(base_model):
    """Information about a file.

    Attributes
    ----------
    file : foreign key
        Reference to the file of which this is a copy.
    node : foreign key
        The node on which this copy lives (or should live).
    has_file : string
        Is the node on the file?
        - 'Y': yes, the node has the file.
        - 'N': no, the node does not have the file.
        - 'M': maybe: we've tried to copy/erase it, but haven't yet verified.
        - 'X': the file is there, but has been verified to be corrupted.
    wants_file : enum
        Does the node want the file?
        - 'Y': yes, keep the file around
        - 'M': maybe, can delete if we need space
        - 'N': no, attempt to delete
        In all cases we try to keep at least two copies of the file around.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="copies")
    node = pw.ForeignKeyField(StorageNode, backref="copies")
    has_file = EnumField(["N", "Y", "M", "X"], default="N")
    wants_file = EnumField(["Y", "M", "N"], default="Y")


class ArchiveFileCopyRequest(base_model):
    """Requests for file copies.

    Attributes
    ----------
    file : foreign key
        Reference to the file to be copied.
    group_to : foreign key
        The storage group to which the file should be copied.
    node_from : foreign key
        The node from which the file should be copied.
    nice : integer
        For nicing the copy/rsync process if resource management is needed.
    completed : bool
        Set to true when the copy has succeeded.
    cancelled : bool
        Set to true if the copy is no longer wanted.
    n_requests : integer
        The number of previous requests that have been made for this copy.
    timestamp : datetime
        The time the most recent request was made.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="requests")
    group_to = pw.ForeignKeyField(StorageGroup, backref="requests_to")
    node_from = pw.ForeignKeyField(StorageNode, backref="requests_from")
    nice = pw.IntegerField()
    completed = pw.BooleanField()
    cancelled = pw.BooleanField(default=False)
    n_requests = pw.IntegerField()
    timestamp = pw.DateTimeField()

    class Meta(object):
        primary_key = pw.CompositeKey("file", "group_to", "node_from")
