"""Test util."""

from chimedb.data_index import util
from chimedb.data_index.orm import (
    AcqType,
    FileType,
    AcqFileTypes,
    StorageHost,
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
    for host in ["drao", "fir", "scinet"]:
        StorageHost.get(name=host)

    for group in [
        "scinet_staging",
        "scinet_hpss",
        "drao_storage",
        "fir_online",
        "fir_staging",
        "fir_nearline",
    ]:
        StorageGroup.get(name=group)

    for node in [
        "gong",
        "fir_staging",
        "fir_smallfile",
        "fir_nearline",
        "fir_online",
        "scinet_staging",
        "scinet_hpss",
    ]:
        node = StorageNode.get(name=node)
        assert node.host is not None

    edges = [
        ("gong", "fir_staging", True, False),
        ("fir_staging", "fir_nearline", True, True),
        ("fir_nearline", "scinet_staging", True, False),
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
