"""Common fixtures."""

import pytest
import chimedb.core as db

from chimedb.data_index.orm import (
    AcqFileTypes,
    AcqType,
    ArchiveInst,
    FileType,
    StorageNode,
    StorageGroup,
    StorageTransferAction,
)


@pytest.fixture
def proxy():
    """Open a connection to the database.

    Returns the database proxy.
    """
    db.test_enable()
    db.connect(read_write=True)
    yield db.proxy

    db.close()


@pytest.fixture
def tables(proxy):
    """Ensure all the tables are created."""

    proxy.create_tables(
        [
            AcqFileTypes,
            AcqType,
            ArchiveInst,
            FileType,
            StorageNode,
            StorageGroup,
            StorageTransferAction,
        ]
    )
