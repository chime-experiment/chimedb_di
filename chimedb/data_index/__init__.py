"""alpenhorn (data index) table definitions"""
from . import orm, util

from .orm import (
    AcqType,
    ArchiveAcq,
    ArchiveFile,
    ArchiveFileCopy,
    ArchiveFileCopyRequest,
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


from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
