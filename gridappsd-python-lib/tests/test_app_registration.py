"""Unit tests for gridappsd.app_registration status handling.

_set_application_status writes ApplicationStatusEnum values to the
GRIDAPPSD_APPLICATION_STATUS environment variable. These tests assert
the exact string value written for each status, and that Job.run()
drives the environment variable through the expected RUNNING then
STOPPED transition for a command that exits cleanly.
"""

import os

import pytest

from gridappsd.app_registration import (
    GRIDAPPSD_APPLICATION_STATUS,
    ApplicationStatusEnum,
    Job,
    _set_application_status,
)


@pytest.fixture(autouse=True)
def _clear_status_env(monkeypatch):
    monkeypatch.delenv(GRIDAPPSD_APPLICATION_STATUS, raising=False)


class TestSetApplicationStatus:
    @pytest.mark.parametrize(
        "status",
        [
            ApplicationStatusEnum.STARTING,
            ApplicationStatusEnum.STOPPING,
            ApplicationStatusEnum.RUNNING,
            ApplicationStatusEnum.STOPPED,
            ApplicationStatusEnum.ERROR,
        ],
    )
    def test_writes_exact_status_value_to_environment(self, status):
        _set_application_status(status)

        assert os.environ[GRIDAPPSD_APPLICATION_STATUS] == status.value

    def test_overwrites_previous_value(self):
        _set_application_status(ApplicationStatusEnum.STARTING)
        _set_application_status(ApplicationStatusEnum.RUNNING)

        assert os.environ[GRIDAPPSD_APPLICATION_STATUS] == "RUNNING"


class TestJobRunSetsApplicationStatus:
    def test_successful_job_ends_in_stopped_status(self):
        job = Job(args=["true"])

        job.run()

        assert os.environ[GRIDAPPSD_APPLICATION_STATUS] == ApplicationStatusEnum.STOPPED.value

    def test_failing_job_ends_in_error_status(self):
        job = Job(args=["/nonexistent-command-for-gadp-044-test"])

        job.run()

        assert os.environ[GRIDAPPSD_APPLICATION_STATUS] == ApplicationStatusEnum.ERROR.value
