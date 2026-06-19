import pytest
from ocrsys.locking import SingleInstanceLock, AlreadyRunning


def test_second_acquire_fails(tmp_path):
    lock_path = tmp_path / ".ocr.lock"
    with SingleInstanceLock(lock_path):
        with pytest.raises(AlreadyRunning):
            with SingleInstanceLock(lock_path):
                pass


def test_releases_after_exit(tmp_path):
    lock_path = tmp_path / ".ocr.lock"
    with SingleInstanceLock(lock_path):
        pass
    # rilasciato -> si puo' riacquisire
    with SingleInstanceLock(lock_path):
        pass
