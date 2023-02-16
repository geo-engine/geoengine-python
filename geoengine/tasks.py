'''
Module for encapsulating Geo Engine tasks API
'''

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, List, Tuple
from uuid import UUID

import datetime
import requests as req

from geoengine.types import DEFAULT_ISO_TIME_FORMAT
from geoengine.auth import get_session
from geoengine.error import check_response_for_error, GeoEngineException


class TaskId:
    '''A wrapper for a task id'''

    def __init__(self, task_id: UUID) -> None:
        self.__task_id = task_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> TaskId:
        '''Parse a http response to an `TaskId`'''

        if 'task_id' not in response and 'taskId' not in response:
            raise GeoEngineException(response)

        task_id = response['task_id'] if 'task_id' in response else response['taskId']

        return TaskId(UUID(task_id))

    def __eq__(self, other) -> bool:
        '''Checks if two dataset ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__task_id == other.__task_id  # pylint: disable=protected-access

    def __str__(self) -> str:
        return str(self.__task_id)

    def __repr__(self) -> str:
        return repr(self.__task_id)


class TaskStatus(Enum):
    '''An enum of task status types'''

    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class TaskStatusInfo:  # pylint: disable=too-few-public-methods
    '''A wrapper for a task status type'''

    status: TaskStatus
    time_started: datetime.datetime

    def __init__(self, status, time_started) -> None:
        self.status = status
        self.time_started = time_started

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> TaskStatusInfo:
        '''
        Parse a http response to a `TaskStatusInfo`

        The task can be one of:
        RunningTaskStatusInfo, CompletedTaskStatusInfo, AbortedTaskStatusInfo or FailedTaskStatusInfo
        '''

        if 'status' not in response:
            raise GeoEngineException(response)

        status = TaskStatus(response['status'])
        time_started = None
        if 'timeStarted' in response:
            time_started = datetime.datetime.strptime(response['timeStarted'], DEFAULT_ISO_TIME_FORMAT)

        if status == TaskStatus.RUNNING:
            if 'pctComplete' not in response  \
                    or 'estimatedTimeRemaining' not in response \
                    or 'info' not in response:
                raise GeoEngineException(response)
            pct_complete = response['pctComplete']
            time_estimate = response['estimatedTimeRemaining']

            return RunningTaskStatusInfo(status, time_started, pct_complete, time_estimate, response['info'])
        if status == TaskStatus.COMPLETED:
            if 'info' not in response or 'timeTotal' not in response:
                raise GeoEngineException(response)
            return CompletedTaskStatusInfo(status, time_started, response['info'], response['timeTotal'])
        if status == TaskStatus.ABORTED:
            if 'cleanUp' not in response:
                raise GeoEngineException(response)
            return AbortedTaskStatusInfo(status, time_started, response['cleanUp'])
        if status == TaskStatus.FAILED:
            if 'error' not in response or 'cleanUp' not in response:
                raise GeoEngineException(response)
            return FailedTaskStatusInfo(status, time_started, response['error'], response['cleanUp'])
        raise GeoEngineException(response)


class RunningTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a running task status with information about completion progress'''

    def __init__(self, status, start_time, pct_complete, time_estimate, info) -> None:
        super().__init__(status, start_time)
        self.pct_complete = pct_complete
        self.time_estimate = time_estimate
        self.info = info

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.pct_complete == other.pct_complete \
            and self.time_estimate == other.time_estimate and self.info == other.info

    def __str__(self) -> str:
        return f"status={self.status.value}, time_started={self.time_started}, " \
            f"pct_complete={self.pct_complete}, " \
            f"time_estimate={self.time_estimate}, info={self.info}"

    def __repr__(self) -> str:
        return f"TaskStatusInfo(status={self.status.value!r}, pct_complete={self.pct_complete!r}, " \
               f"time_estimate={self.time_estimate!r}, info={self.info!r})"


class CompletedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a completed task status with information about the completion'''

    def __init__(self, status, time_started, info, time_total) -> None:
        super().__init__(status, time_started)
        self.info = info
        self.time_total = time_total

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.info == other.info and self.time_total == other.time_total

    def __str__(self) -> str:
        return f"status={self.status.value}, time_started={self.time_started}, info={self.info}, " \
            "time_total={self.time_total}"

    def __repr__(self) -> str:
        return f"TaskStatusInfo(status={self.status.value!r}, time_started={self.time_started!r}," \
            "info = {self.info!r}, time_total = {self.time_total!r})"


class AbortedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for an aborted task status with information about the termination'''

    def __init__(self, status, time_started, clean_up) -> None:
        super().__init__(status, time_started)
        self.clean_up = clean_up

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.clean_up == other.clean_up

    def __str__(self) -> str:
        return f"status={self.status.value}, time_started={self.time_started}, clean_up={self.clean_up}"

    def __repr__(self) -> str:
        return f"TaskStatusInfo(status={self.status.value!r}, time_started={self.time_started!r}," \
            " clean_up={self.clean_up!r})"


class FailedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a failed task status with information about the failure'''

    def __init__(self, status, time_started, error, clean_up) -> None:
        super().__init__(status, time_started)
        self.error = error
        self.clean_up = clean_up

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.error == other.error and self.clean_up == other.clean_up

    def __str__(self) -> str:
        return f"status={self.status.value}, time_started={self.time_started}, error={self.error}, " \
            " clean_up={self.clean_up}"

    def __repr__(self) -> str:
        return f"TaskStatusInfo(status={self.status.value!r}, time_started={self.time_started!r}, " \
            " error={self.error!r}, clean_up={self.clean_up!r})"


class Task:
    '''
    Holds a task id, allows querying and manipulating the task status
    '''

    def __init__(self, task_id: TaskId):
        self.__task_id = task_id

    def __eq__(self, other):
        '''Check if two task representations are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__task_id == other.__task_id  # pylint: disable=protected-access

    def get_status(self, timeout: int = 3600) -> TaskStatusInfo:
        '''
        Returns the status of a task in a Geo Engine instance
        '''
        session = get_session()

        task_id_str = str(self.__task_id)

        response = req.get(
            url=f'{session.server_url}/tasks/{task_id_str}/status',
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

        return TaskStatusInfo.from_response(response.json())

    def abort(self, force: bool = False, timeout: int = 3600) -> None:
        '''
        Abort a running task in a Geo Engine instance
        '''
        session = get_session()

        task_id_str = str(self.__task_id)

        force_str = str(force).lower()

        response = req.get(
            url=f'{session.server_url}/tasks/{task_id_str}/abort?force={force_str}',
            headers=session.auth_header,
            timeout=timeout
        )

        check_response_for_error(response)

    def wait_for_finish(
            self,
            check_interval_seconds: float = 5,
            request_timeout: int = 3600,
            print_status: bool = True) -> TaskStatusInfo:
        '''
        Wait for the given task in a Geo Engine instance to finish (status either complete, aborted or failed).
        The status is printed after each check-in. Check-ins happen in intervals of check_interval_seconds seconds.
        '''
        current_status = self.get_status(request_timeout)

        while current_status.status == TaskStatus.RUNNING:
            current_status = self.get_status(request_timeout)

            if print_status:
                print(current_status)
            if current_status.status == TaskStatus.RUNNING:
                time.sleep(check_interval_seconds)

        return current_status

    def __str__(self) -> str:
        return str(self.__task_id)

    def __repr__(self) -> str:
        return repr(self.__task_id)


def get_task_list(timeout: int = 3600) -> List[Tuple[Task, TaskStatusInfo]]:
    '''
    Returns the status of all tasks in a Geo Engine instance
    '''
    session = get_session()

    response = req.get(
        url=f'{session.server_url}/tasks/list',
        headers=session.auth_header,
        timeout=timeout
    )

    check_response_for_error(response)

    response_json = response.json()

    result = []
    for item in response_json:
        if 'task_id' not in item and 'taskId' not in item:
            raise GeoEngineException(response_json)

        task_id = item['task_id'] if 'task_id' in item else item['taskId']

        result.append((Task(TaskId(UUID(task_id))), TaskStatusInfo.from_response(item)))

    return result
