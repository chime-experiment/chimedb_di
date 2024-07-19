"""alpenhorn (data index) table definitions"""
from . import orm, util

from .orm import (
    AcqType,
    ArchiveAcq,
    ArchiveFile,
    ArchiveFileCopy,
    ArchiveFileCopyRequest,
    ArchiveInst,
    CalibrationGainFileInfo,
    CorrAcqInfo,
    CorrFileInfo,
    DigitalGainFileInfo,
    FileType,
    FlagInputFileInfo,
    HFBAcqInfo,
    HFBFileInfo,
    HKAcqInfo,
    HKFileInfo,
    HKPFileInfo,
    MiscFileInfo,
    RawadcAcqInfo,
    RawadcFileInfo,
    StorageGroup,
    StorageNode,
    WeatherFileInfo,
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("chimedb.data_index")
except PackageNotFoundError:
    # package is not installed
    pass
