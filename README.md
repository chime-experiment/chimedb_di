# chimedb.data_index - CHIME data index table definitions

This package, built on top of [chimedb.core](https://github.com/chime-experiment/chimedb), defines the
data index tables used by `alpenhorn` to track raw data files.

The table classes defined `orm` module include:
* AcqType
* ArchiveAcq
* ArchiveFile
* ArchiveFileCopy
* ArchiveFileCopyRequest
* ArchiveInst
* CalibrationGainFileInfo
* CorrAcqInfo
* CorrFileInfo
* DigitalGainFileInfo
* FileType
* FlagInputFileInfo
* HKAcqInfo
* HKFileInfo
* HKPFileInfo
* RawadcAcqInfo
* RawadcFileInfo
* StorageGroup
* StorageNode
* WeatherFileInfo

The `util` module defines a few utility functions:
* detect_file_type
* md5sum_file
* parse_acq_name
* parse_corrfile_name
* parse_hkfile_name
* parse_weatherfile_name
* populate_types
