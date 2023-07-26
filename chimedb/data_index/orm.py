"""
Table definitions for the alpenhorn data index
"""
import logging
import calendar
import datetime
import numpy as np
import peewee as pw

from chimedb.core.orm import base_model, name_table, EnumField, JSONDictField


# Logging
# =======
_logger = logging.getLogger("chimedb")
_logger.addHandler(logging.NullHandler())


# Info base table
# ===============
class InfoBase(base_model):
    """Abstract base class for CHIME Info tables.

    The keyword parameters "node_" and "path_", if present, are passed,
    along with the ArchiveAcq or ArchiveFile, to the method `_set_info`
    which must be re-implemented by subclasses.

    The dict returned from this `_set_info` call is merged into the list of
    keyword parameters (after removing the keywords listed above).  These
    merged keyword parameters is passed to the `peewee.Model` initialiser.

    This _set_info() call is only performed if the "node_" and
    "path_" keywords are provided.  The trailing underscore on these
    keywords prevents the potential for clashes with field names of
    the underlying table.
    """

    # Should be set to True for Acq Info classes
    is_acq = False

    def __init__(self, *args, **kwargs):
        """initialise an instance.

        Parameters
        ----------
        node_ : alpenhorn.update.UpdateableNode or None
            The node on which the imported file is
        path_ : pathlib.Path or None
            Path to the imported file.  Relative to `node.root`.

        Raises
        ------
        ValueError
            the keyword "path_" was given, but "node_" was not.
        """

        # Remove keywords we consume
        path = kwargs.pop("path_", None)
        node = kwargs.pop("node_", None)
        name_data = kwargs.pop("name_data_", tuple())

        # If we were given an "item_", convert it to an acq or file as apporpriate
        item = kwargs.pop("item_", None)
        if item is not None:
            if self.is_acq:
                kwargs["acq"] = item
            else:
                kwargs["file"] = item

        # Call _set_info, if necessary
        if path is not None:
            if node is None:
                raise ValueError("no node_ specified with path_")

            # Info returned is merged into kwargs so the peewee model can
            # ingest it.
            kwargs |= self._set_info(path=path, node=node, name_data=name_data)

        # Continue init
        super().__init__(*args, **kwargs)

    def _set_info(self, path, node, re_groups):
        """Generate info table field data for this path.

        Calls to this method occur as part of object initialisation during
        an init() call.

        Subclasses must re-implement this method to generate metadata by
        inspecting the acqusition or file on disk given by `path`.  To
        access a file on the node, don't open() the path directly; use
        `node.io.open(path)`.

        Parameters
        ----------
        path : pathlib.Path
            path to the file being imported.  Note this is _always_
            the _file_ path, even for acqusitions.  Relative to
            `node.db.root`.
        node : alpenhorn.update.UpdateableNode
            node where the file has been imported
        re_groups : tuple
            For File Info classes, this is a possibly-empty tuple containing
            group matches from the pattern match that was performed on the
            file name.  For Acq Info classes, this is always an empty tuple.

        Returns
        -------
        info : dict
            table data to be passed on to the peewee `Model` initialiser.

        On error, implementations should raise an appropriate exception.
        """
        raise NotImplementedError("must be re-implemented by subclass")


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
        Name of the type.  This appears as the last element of
        an acqusition name.
    info_class : string or None
        Name of the associated Info class under `alpenhorn_chime.info`.
    notes : string or None
        A human-readable description.
    """

    name = pw.CharField(max_length=64, unique=True)
    info_class = pw.CharField(max_length=64, null=True)
    notes = pw.TextField(null=True)

    @property
    def file_types(self):
        """An iterator over the FileTypes supported by this AcqType."""
        return FileType.select().join(AcqFileTypes).where(AcqFileTypes.acq_type == self)

    @classmethod
    def corr(cls):
        """For getting the correlator acquisition type."""
        return cls.from_name("corr")

    @classmethod
    def hfb(cls):
        """For getting the HFB acquisition type."""
        return cls.from_name("hfb")

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

    name = pw.CharField(max_length=64, unique=True)
    inst = pw.ForeignKeyField(ArchiveInst, backref="acqs", null=True)
    type = pw.ForeignKeyField(AcqType, backref="acqs", null=True)
    comment = pw.TextField(null=True)

    @property
    def corr_files(self):
        return self.files.join(CorrFileInfo)

    @property
    def hfb_files(self):
        return self.files.join(HFBFileInfo)

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
        return (
            self.corr_files
            | self.hfb_files
            | self.hk_files
            | self.weather_files
            | self.rawadc_files
        )

    @property
    def n_timed_files(self):
        return (
            self.corr_files.count()
            + self.hfb_files.count()
            + self.hk_files.count()
            + self.weather_files.count()
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


# CHIME Acq Info Base Class
# =========================
class CHIMEAcqInfo(InfoBase):
    """Abstract base class for CHIME Acq Info tables.

    Add acq info base column `acq` and provides an implementation
    of `_set_info` for convenience which converts the call into a
    call to `_info_from_file`.

    Subclasses should add additional fields.  They should also
    either reimplement `_set_info` or else implement the method
    `_info_from_file` which will be passed an open, read-only
    file object.

    Attributes
    ----------
    acq : foreign key to ArchiveAcq (or ArchiveAcq)
        the corresponding acquisition record
    """

    is_acq = True

    acq = pw.ForeignKeyField(ArchiveAcq)

    def _set_info(self, path, node, name_data):
        """Set acq info from file `path` on node `node`.

        Calls `_info_from_file` to generate info data.

        Parameters
        ----------
        node : StorageNode
            the node we're importing on
        path : pathlib.Path
            the path relative to `node.root` of the file
            being imported in this acquistion
        name_data : dict
            ignored

        Returns
        -------
        info : dict
            any data returned by `_info_from_file`, if that
            method exists, or else an empty dict.

        Notes
        -----
        For acqusitions, the only key in `name_data` is "acqtime" which
        contains a `datetime` with the value of the acqusition timestamp.
        If that value is important, subclasses must re-implement this
        method to capture it.
        """
        if hasattr(self, "_info_from_file"):
            # Open the file
            with node.io.open(path) as file:
                # Get keywords from file
                return self._info_from_file(file)
        else:
            return dict()


# Acq Info Tables
# ===============
class CorrAcqInfo(CHIMEAcqInfo):
    """Information about a correlation acquisition.

    Attributes
    ----------
    acq : foreign key to ArchiveAcq
        The acquisition that the information is for.
    integration : float
        Integration time in seconds.
    nfreq : integer
        Number of frequency channels.
    nprod : integer
        Number of correlation products in acquisition.
    """

    integration = pw.DoubleField(null=True)
    nfreq = pw.IntegerField(null=True)
    nprod = pw.IntegerField(null=True)

    def _info_from_file(self, file):
        """Return corr acq info from a file in the acq.

        Copied from `auto_import.get_acqcorrinfo_keywords_from_h5`
        in alpenhorn-1.

        Parameters
        ----------
        file : open, read-only file being imported.
        """
        import h5py

        # Find the integration time from the median difference between timestamps.
        with h5py.File(file, "r") as f:
            dt = np.array([])
            t = f["/index_map/time"]
            for i in range(1, len(t)):
                dt = np.append(dt, float(t[i][1]) - float(t[i - 1][1]))
            integration = np.median(dt)
            n_freq = len(f["/index_map/freq"])
            n_prod = len(f["/index_map/prod"])

        return {"integration": integration, "nfreq": n_freq, "nprod": n_prod}


class HFBAcqInfo(CHIMEAcqInfo):
    """Information about a HFB acquisition.

    Attributes
    ----------
    acq : foreign key
        Reference to the acquisition that the information is for.
    integration : float
        Integration time in seconds.
    nfreq : integer
        Number of frequency channels.
    nsubfreq : integer
        Number of sub-frequencies in acquisition.
    nbeam : integer
        Number of beams in acquisition.

    """

    integration = pw.DoubleField(null=True)
    nfreq = pw.IntegerField(null=True)
    nsubfreq = pw.IntegerField(null=True)
    nbeam = pw.IntegerField(null=True)

    def _info_from_file(self, file):
        """Return HFB corr acq info from a file in the acq.

        Copied from `auto_import.get_acqhfbinfo_keywords_from_h5`
        in alpenhorn-1.

        Parameters
        ----------
        file : open, read-only file being imported.
        """
        import h5py

        # Find the integration time from the median difference between timestamps.
        with h5py.File(file, "r") as f:
            dt = np.array([])
            t = f["/index_map/time"]
            for i in range(1, len(t)):
                dt = np.append(dt, float(t[i][1]) - float(t[i - 1][1]))
            integration = np.median(dt)
            n_freq = len(f["/index_map/freq"])
            n_sub_freq = len(f["/index_map/subfreq"])
            n_beam = len(f["/index_map/beam"])

        return {
            "integration": integration,
            "nfreq": n_freq,
            "nsubfreq": n_sub_freq,
            "nbeam": n_beam,
        }


# This class is deprecated and kept here for legacy support
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


class RawadcAcqInfo(CHIMEAcqInfo):
    """Information about a raw ADC acquisition.

    Attributes
    ----------
    acq : foreign key to ArchiveAcq
        The acquisition that the information is for.
    start_time : double
        When the raw ADC acquisition was performed, in UNIX time.
    """

    start_time = pw.DoubleField(null=True)

    def _set_info(self, path, node, name_data):
        """Generate acq info.

        Parameters
        ----------
        node : StorageNode
            the node we're importing on
        path : pathlib.Path
            the path relative to `node.root` of the file
            being imported in this acquistion
        name_data : dict
            the value associated with key "acqtime" is used for "start_time"
        """

        info = super()._set_info(path=path, node=node, name_data=name_data)
        info["start_time"] = calendar.timegm(name_data["acqtime"].utctimetuple())
        return info


class FileType(base_model):
    """A file type.

    Attributes
    ----------
    name : string
        The name of this file type.
    info_class : string or None
        If not None, the name of the associated Info class, or an
        Info-class-providing function, located under `alpenhorn_chime.info`.
    pattern : string or None
        If not None, a regular expression to match against the filename.  This
        is the primary method of determining the type of a file.  If this is
        None, no matching is done, and alpenhorn will be unable to import a file
        of this type.
    notes: string
        Any notes or comments about this file type.
    """

    name = pw.CharField(max_length=64)
    info_class = pw.CharField(max_length=64, null=True)
    pattern = pw.CharField(max_length=64, null=True)
    notes = pw.TextField(null=True)


class AcqFileTypes(base_model):
    """FileTypes supported by an AcqType.

    A junction table providing the many-to-many relationship
    indicating which FileTypes are supported by which AcqTypes.

    Attributes
    ----------
    acq_type : foreign key to AcqType
    file_type : foreign key to FileType

    Notes
    -----
    As this is a junction table, there is no id column.  The
    tuple (acq_type, file_type) itself is the primary key.
    """

    acq_type = pw.ForeignKeyField(AcqType, backref="acq_types")
    file_type = pw.ForeignKeyField(FileType, backref="file_types")

    class Meta:
        primary_key = pw.CompositeKey("acq_type", "file_type")


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
    registered : datetime
        The UTC time when the file was registered in the database.
    """

    acq = pw.ForeignKeyField(ArchiveAcq, backref="files")
    type = pw.ForeignKeyField(FileType, null=True, backref="files")
    name = pw.CharField(max_length=64)
    size_b = pw.BigIntegerField(null=True)
    md5sum = pw.CharField(null=True, max_length=32)
    registered = pw.DateTimeField(default=datetime.datetime.utcnow)


# File Info Base Class
# ====================
class CHIMEFileInfo(InfoBase):
    """Abstract base info class for a CHIME file

    Subclasses must re-implement `_parse_filename` to implement
    type detection, and optionally data gathering.

    Subclasses should add additional fields.  They should also
    either reimplement `_set_info` or else implement the method
    `_info_from_file` which will be passed an open, read-only
    file object.
    """

    file = pw.ForeignKeyField(ArchiveFile)

    group_keys = tuple()

    def _set_info(self, path, node, name_data):
        """Set file info from file `path` on node `node`.

        If defined in the class, calls `_info_from_file` to
        populate the info record.

        Additional fields provided in `name_data` are also merged
        into the returned dict.

        Parameters
        ----------
        node : UpdateableNode
            the node we're importing on
        path : pathlib.Path
            the path relative to `node.root` of the file being imported
        name_data : dict
            other dict entries merged into the returned dict.  May be empty.

        Returns
        -------
        info : dict
            A dict containing data from `_info_from_file` and/or
            `name_data`.
        """
        if hasattr(self, "_info_from_file"):
            # Open the file
            with node.io.open(path) as file:
                # Get keywords from file
                info = self._info_from_file(file)
        else:
            info = dict()

        return info | name_data


# File Info Tables
# ================
class CorrFileInfo(CHIMEFileInfo):
    """Information about a correlation data file.

    Attributes
    ----------
    file : foreign key to ArchiveFile
        The file this information is about.
    chunk_number : integer
        Label for where in the acquisition this file is.
    freq_number : integer
        Which frequency slice this file is.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    chunk_number = pw.IntegerField(null=True)
    freq_number = pw.IntegerField(null=True)

    def _info_from_file(self, file):
        """Get corr file info.

        Parameters
        ----------
        file : open, read-only file
            the file being imported.
        """
        import h5py

        with h5py.File(file, "r") as f:
            start_time = f["/index_map/time"][0][1]
            finish_time = f["/index_map/time"][-1][1]

        return {
            "start_time": start_time,
            "finish_time": finish_time,
        }


class HFBFileInfo(CHIMEFileInfo):
    """Information about a HFB data file.

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

    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    chunk_number = pw.IntegerField(null=True)
    freq_number = pw.IntegerField(null=True)

    def _info_from_file(self, file):
        """Get HFB file info.

        Parameters
        ----------
        file : open, read-only file
            the file being imported.
        """
        import h5py

        with h5py.File(file, "r") as f:
            start_time = f["/index_map/time"][0][1]
            finish_time = f["/index_map/time"][-1][1]

        return {
            "start_time": start_time,
            "finish_time": finish_time,
        }


# This class is deprecated and kept here for legacy support
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


# This class is deprecated and kept here for legacy support
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


class CalibrationFileInfo(CHIMEFileInfo):
    """Base class for all calibration data types.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """

    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)

    def _info_from_file(self, file):
        """Get cal file info.

        Parameters
        ----------
        file : open, read-only file
            the file being imported.
        """
        import h5py

        with h5py.File(file, "r") as f:
            start_time = f["index_map/update_time"][0]
            finish_time = f["index_map/update_time"][-1]

        return {
            "start_time": start_time,
            "finish_time": finish_time,
        }


class DigitalGainFileInfo(CalibrationFileInfo):
    """Digital gain data file info.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """


class CalibrationGainFileInfo(CalibrationFileInfo):
    """Gain data file info.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """


class FlagInputFileInfo(CalibrationFileInfo):
    """Flag input file info.

    Attributes
    ----------
    file : foreign key
        Reference to the file this information is about.
    start_time : float
        Start of data in the file in UNIX time.
    finish_time : float
        End of data in the file in UNIX time.
    """


class RawadcFileInfo(CHIMEFileInfo):
    """Information about a rawadc data file.

    Attributes
    ----------
    file : foreign key to ArchiveFile
        The file this information is about.
    start_time : float
        Start of acquisition in UNIX time.
    finish_time : float
        End of acquisition in UNIX time.
    """

    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)

    def _info_from_file(self, file):
        """Get rawadc file info.

        Parameters
        ----------
        file : open, read-only file
            the file being imported.
        """
        import h5py

        with h5py.File(file, "r") as f:
            times = f["timestamp"]["ctime"]
            start_time = times.min()
            finish_time = times.max()

        return {"start_time": start_time, "finish_time": finish_time}


class WeatherFileInfo(CHIMEFileInfo):
    """CHIME weather file info.

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

    start_time = pw.DoubleField(null=True)
    finish_time = pw.DoubleField(null=True)
    date = pw.CharField(null=True, max_length=8)

    def _set_info(self, node, path, name_data):
        """Generate weather file info."""

        date = name_data["date"]
        dt = datetime.datetime.strptime(date, "%Y%m%d")
        start_time = calendar.timegm(dt.utctimetuple())
        finish_time = calendar.timegm(
            (
                dt + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
            ).utctimetuple()
        )

        return {"start_time": start_time, "finish_time": finish_time, "date": date}


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
    HFBFileInfo,
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
    name : string, unique
        The group that this node belongs to (Scinet, DRAO hut, . . .).
    io_class : string
        The I/O class for this node.  See below.  If this is NULL,
        the value "Default" is used.
    notes : string, optional
        Any notes about this storage group.
    io_config : string
        An optional JSON blob of configuration data interpreted by the
        I/O class.  If given, must be a JSON object literal.
    """

    name = pw.CharField(max_length=64, unique=True)
    io_class = pw.CharField(max_length=255, null=True)
    notes = pw.TextField(null=True)
    io_config = pw.TextField(null=True)


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
    active : bool
        Is the node active?
    auto_import : bool
        Should files that appear on this node be automatically added?
    suspect : bool
        Deprecated
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

    name = pw.CharField(max_length=64, unique=True)
    root = pw.CharField(max_length=255, null=True)
    host = pw.CharField(max_length=64, null=True)
    username = pw.CharField(max_length=64, null=True)
    address = pw.CharField(max_length=255, null=True)
    io_class = pw.CharField(max_length=255, null=True)
    group = pw.ForeignKeyField(StorageGroup, backref="nodes")
    active = pw.BooleanField(default=False)
    auto_import = pw.BooleanField(default=False)
    auto_verify = pw.IntegerField(default=0)
    suspect = pw.BooleanField(default=False, null=True)
    storage_type = EnumField(["A", "T", "F"], default="A")
    max_total_gb = pw.FloatField(null=True)
    min_avail_gb = pw.FloatField(default=0)
    avail_gb = pw.FloatField(null=True)
    avail_gb_last_checked = pw.DateTimeField(null=True)
    min_delete_age_days = pw.FloatField(default=30, null=True)
    notes = pw.TextField(null=True)
    io_config = pw.TextField(null=True)


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
    size_b : integer
        Allocated size of file in bytes.
    last_update : datetime
        The UTC time when the record was last updated.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="copies")
    node = pw.ForeignKeyField(StorageNode, backref="copies")
    has_file = EnumField(["N", "Y", "M", "X"], default="N")
    wants_file = EnumField(["Y", "M", "N"], default="Y")
    size_b = pw.BigIntegerField()
    last_update = pw.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        indexes = ((("file", "node"), True),)


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
        Deprecated
    completed : bool
        Set to true when the copy has succeeded.
    cancelled : bool
        Set to true if the copy is no longer wanted.
    n_requests : integer
        Deprecated
    timestamp : datetime
        The time the most recent request was made.
    transfer_started : datetime
        The time the transfer was started.
    transfer_completed : datetime
        The time the transfer was completed.
    """

    file = pw.ForeignKeyField(ArchiveFile, backref="requests")
    group_to = pw.ForeignKeyField(StorageGroup, backref="requests_to")
    node_from = pw.ForeignKeyField(StorageNode, backref="requests_from")
    nice = pw.IntegerField(null=True)
    completed = pw.BooleanField()
    cancelled = pw.BooleanField(default=False)
    n_requests = pw.IntegerField(null=True)
    timestamp = pw.DateTimeField()
    transfer_started = pw.DateTimeField(null=True)
    transfer_completed = pw.DateTimeField(null=True)
