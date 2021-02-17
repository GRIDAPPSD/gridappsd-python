import os

import mock
import pytest

from gridappsd import utils


def test_error_when_environment_username_password_not_set():
    with mock.patch.dict(os.environ, dict(), clear=True):
        with pytest.raises(ValueError):
            utils.get_gridappsd_user()
        with pytest.raises(ValueError):
            utils.get_gridappsd_pass()

    with mock.patch.dict(os.environ, dict(GRIDAPPSD_USER="", GRIDAPPSD_PASSWORD="")):
        with pytest.raises(ValueError):
            utils.get_gridappsd_user()
        with pytest.raises(ValueError):
            utils.get_gridappsd_pass()


def test_can_get_username_password_from_environment():
    username = "user1"
    password = "password1"
    with mock.patch.dict(os.environ, dict(GRIDAPPSD_USER=username, GRIDAPPSD_PASSWORD=password)):
        assert username == utils.get_gridappsd_user()
        assert password == utils.get_gridappsd_pass()