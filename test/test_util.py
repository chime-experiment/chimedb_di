"""Test util."""

from chimedb.data_index import util
from chimedb.data_index.orm import (
    AcqType,
    FileType,
    AcqFileTypes,
    StorageGroup,
    StorageNode,
    StorageTransferAction,
)


def test_update_types(tables):
    """Test update_types()."""

    # Create the type data
    util.update_types()

    # Check
    type_data = {
        "corr": {"acq_class": "CorrAcqInfo", "file_class": "CorrFileInfo"},
        "hfb": {"acq_class": "HFBAcqInfo", "file_class": "HFBFileInfo"},
        "weather": {"acq_class": None, "file_class": "WeatherFileInfo"},
        "rawadc": {"acq_class": "RawadcAcqInfo", "file_class": "RawadcFileInfo"},
    }

    for name, data in type_data.items():
        at = AcqType.get(name=name)
        assert at.info_class == data["acq_class"]

        ft = FileType.get(name=name)
        assert ft.info_class == data["file_class"]

        fts = list(AcqFileTypes.select().where(AcqFileTypes.acq_type == at))
        assert len(fts) == 1
        assert fts[0].file_type == ft

    # The calibration types are different
    ft = FileType.get(name="calibration")
    assert ft.info_class == "cal_info_class"

    for name in ["digitalgain", "gain", "flaginput"]:
        at = AcqType.get(name=name)
        assert at.info_class is None

        fts = list(AcqFileTypes.select().where(AcqFileTypes.acq_type == at))
        assert len(fts) == 1
        assert fts[0].file_type == ft


def test_update_storage(tables):
    """Test update_storage()."""

    # Create the storage data
    util.update_storage()

    # Check
    for group in [
        "scinet_staging",
        "scinet_hpss",
        "drao_storage",
        "cedar_offload",
        "cedar_online",
        "cedar_staging",
        "cedar_nearline",
    ]:
        StorageGroup.get(name=group)

    for node in [
        "gong",
        "cedar_offload",
        "cedar_staging",
        "cedar_smallfile",
        "cedar_nearline",
        "cedar_online",
        "scinet_staging",
        "scinet_hpss",
    ]:
        StorageNode.get(name=node)

    edges = [
        ("gong", "cedar_staging", True, False),
        ("cedar_staging", "cedar_offload", True, False),
        ("cedar_staging", "scinet_staging", True, False),
        ("cedar_staging", "scinet_hpss", False, True),
        ("cedar_offload", "cedar_nearline", True, True),
        ("scinet_staging", "scinet_hpss", True, True),
    ]

    for edge in edges:
        sta = (
            StorageTransferAction.select()
            .join(StorageGroup)
            .switch(StorageTransferAction)
            .join(StorageNode)
            .select()
            .where(StorageNode.name == edge[0], StorageGroup.name == edge[1])
            .get()
        )

        assert sta.autosync == edge[2]
        assert sta.autoclean == edge[3]
