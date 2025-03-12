"""alpenhorn (data index) table definitions"""

from . import orm as orm, util as util

from .orm import (
    AcqType as AcqType,
    ArchiveAcq as ArchiveAcq,
    ArchiveFile as ArchiveFile,
    ArchiveFileCopy as ArchiveFileCopy,
    ArchiveFileCopyRequest as ArchiveFileCopyRequest,
    ArchiveInst as ArchiveInst,
    CalibrationGainFileInfo as CalibrationGainFileInfo,
    CorrAcqInfo as CorrAcqInfo,
    CorrFileInfo as CorrFileInfo,
    DigitalGainFileInfo as DigitalGainFileInfo,
    FileType as FileType,
    FlagInputFileInfo as FlagInputFileInfo,
    HFBAcqInfo as HFBAcqInfo,
    HFBFileInfo as HFBFileInfo,
    HKAcqInfo as HKAcqInfo,
    HKFileInfo as HKFileInfo,
    HKPFileInfo as HKPFileInfo,
    MiscFileInfo as MiscFileInfo,
    RawadcAcqInfo as RawadcAcqInfo,
    RawadcFileInfo as RawadcFileInfo,
    StorageGroup as StorageGroup,
    StorageNode as StorageNode,
    WeatherFileInfo as WeatherFileInfo,
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("chimedb.data_index")
except PackageNotFoundError:
    # package is not installed
    pass
