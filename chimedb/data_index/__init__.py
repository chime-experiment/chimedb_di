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


def __getattr__(name: str):
    """Custom handling for __version__ global variable."""
    if name == "__version__":
        # No need to re-get __version__ if it already exists
        v = globals().get(name, None)
        if not v:
            from ._version import get_versions

            v = get_versions()["version"]
            globals()[name] = v
        return v

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    