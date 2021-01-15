# chimedb.data_index - CHIME data index table definitions

This package, built on top of [chimedb.core](https://github.com/chime-experiment/chimedb), defines the
data index tables used by `alpenhorn` to track raw data files.

## Installing

Install directly from GitHub:
```
pip install git+https://github.com/chime-experiment/chimedb_di.git
```

If, instead, you're installing from a local clone, read the installation instructions in the
[chimedb.core README.md](https://github.com/chime-experiment/chimedb/) for an important caveat.

## Contents

The table classes provided in `chimedb.data_index` are:
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

The `chimedb.data_index.orm` module also defines:
* file_info_table

The `chimedb.data_index.util` module defines a few utility functions:
* detect_file_type
* md5sum_file
* parse_acq_name
* parse_corrfile_name
* parse_hkfile_name
* parse_weatherfile_name
* populate_types
