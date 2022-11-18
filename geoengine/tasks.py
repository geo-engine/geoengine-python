'''
Module for encapsulating Geo Engine tasks API
'''

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, List
from uuid import UUID

import requests as req

from geoengine.auth import get_session
from geoengine.error import check_response_for_error, GeoEngineException


class TaskId:
    '''A wrapper for a task id'''

    __task_id: UUID

    def __init__(self, task_id: UUID) -> None:
        self.__task_id = task_id

    @classmethod
    def from_response(cls, response: Dict[str, str]) -> TaskId:
        '''Parse a http response to an `TaskId`'''
        if 'task_id' not in response:
            raise GeoEngineException(response)

        return TaskId(UUID(response['task_id']))

    def __str__(self) -> str:
        return str(self.__task_id)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        '''Checks if two dataset ids are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.__task_id == other.__task_id  # pylint: disable=protected-access


class TaskStatus(Enum):
    '''An enum of task status types'''

    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class TaskStatusInfo:  # pylint: disable=too-few-public-methods
    '''A wrapper for a task status type'''

    def __init__(self, status) -> None:
        self.status = status


class RunningTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a running task status with information about completion progress'''

    def __init__(self, status, pct_complete, time_estimate, info) -> None:
        super().__init__(status)
        self.pct_complete = pct_complete
        self.time_estimate = time_estimate
        self.info = info

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.pct_complete == other.pct_complete \
            and self.time_estimate == other.time_estimate and self.info == other.info

    def __str__(self):
        return f"status={self.status.value}, pct_complete={self.pct_complete}, " \
               f"time_estimate={self.time_estimate}, info={self.info}"


class CompletedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a completed task status with information about the completion'''

    def __init__(self, status, info, time_total) -> None:
        super().__init__(status)
        self.info = info
        self.time_total = time_total

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.info == other.info and self.time_total == other.time_total

    def __str__(self):
        return f"status={self.status.value}, info={self.info}, time_total={self.time_total}"


class AbortedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for an aborted task status with information about the termination'''

    def __init__(self, status, clean_up) -> None:
        super().__init__(status)
        self.clean_up = clean_up

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.clean_up == other.clean_up

    def __str__(self):
        return f"status={self.status.value}, clean_up={self.clean_up}"


class FailedTaskStatusInfo(TaskStatusInfo):
    '''A wrapper for a failed task status with information about the failure'''

    def __init__(self, status, error, clean_up) -> None:
        super().__init__(status)
        self.error = error
        self.clean_up = clean_up

    def __eq__(self, other):
        '''Check if two task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.status == other.status and self.error == other.error and self.clean_up == other.clean_up

    def __str__(self):
        return f"status={self.status.value}, error={self.error}, clean_up={self.clean_up}"


def __task_status_from_response(response: Dict[str, str]) -> TaskStatusInfo:
    '''
    Parse a http response to a `TaskStatusInfo`

    The task can be one of:
    RunningTaskStatusInfo, CompletedTaskStatusInfo, AbortedTaskStatusInfo or FailedTaskStatusInfo
    '''

    if 'status' not in response:
        raise GeoEngineException(response)

    status = TaskStatus(response['status'])

    if status == TaskStatus.RUNNING:
        if 'pct_complete' not in response or 'time_estimate' not in response or 'info' not in response:
            raise GeoEngineException(response)
        return RunningTaskStatusInfo(status, response['pct_complete'], response['time_estimate'], response['info'])
    if status == TaskStatus.COMPLETED:
        if 'info' not in response or 'timeTotal' not in response:
            raise GeoEngineException(response)
        return CompletedTaskStatusInfo(status, response['info'], response['timeTotal'])
    if status == TaskStatus.ABORTED:
        if 'cleanUp' not in response:
            raise GeoEngineException(response)
        return AbortedTaskStatusInfo(status, response['cleanUp'])
    if status == TaskStatus.FAILED:
        if 'error' not in response or 'cleanUp' not in response:
            raise GeoEngineException(response)
        return FailedTaskStatusInfo(status, response['error'], response['cleanUp'])
    raise GeoEngineException(response)


class TaskStatusWithId:
    '''A wrapper for a task id with a task status type'''

    def __init__(self, task_id, task_status_with_info) -> None:
        self.task_id = task_id
        self.task_status_with_info = task_status_with_info

    def __eq__(self, other):
        '''Check if two task ids and task statuses are equal'''
        if not isinstance(other, self.__class__):
            return False

        return self.task_id == other.task_id and self.task_status_with_info == other.task_status_with_info

    def __str__(self):
        return f"TaskId={self.task_id}, TaskInfo={{{self.task_status_with_info}}}"


def get_task_list(timeout: int = 3600) -> List[TaskStatusWithId]:
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
        if 'task_id' not in item:
            raise GeoEngineException(response_json)
        result.append(TaskStatusWithId(TaskId(UUID(item['task_id'])), __task_status_from_response(item)))

    return result


def get_task_status(task_id: TaskId, timeout: int = 3600) -> TaskStatusInfo:
    '''
    Returns the status of a task in a Geo Engine instance
    '''
    session = get_session()

    task_id_str = str(task_id)

    response = req.get(
        url=f'{session.server_url}/tasks/{task_id_str}/status',
        headers=session.auth_header,
        timeout=timeout
    )

    check_response_for_error(response)

    return __task_status_from_response(response.json())


def abort_task(task_id: TaskId, force: bool = False, timeout: int = 3600) -> None:
    '''
    Abort a running task in a Geo Engine instance
    '''
    session = get_session()

    task_id_str = str(task_id)

    force_str = str(force).lower()

    response = req.get(
        url=f'{session.server_url}/tasks/{task_id_str}/abort?force={force_str}',
        headers=session.auth_header,
        timeout=timeout
    )

    check_response_for_error(response)


def wait_for_task_to_finish_and_print_status(task_id: TaskId,
                                             check_interval_seconds: float = 5,
                                             request_timeout: int = 3600) -> TaskStatusInfo:
    '''
    Wait for the given task in a Geo Engine instance to finish (status either complete, aborted or failed).
    The status is printed after each check-in. Check-ins happen in intervals of check_interval_seconds seconds.
    '''
    current_status = get_task_status(task_id, request_timeout)

    while current_status.status == TaskStatus.RUNNING:
        current_status = get_task_status(task_id, request_timeout)
        print(current_status)
        if current_status.status == TaskStatus.RUNNING:
            time.sleep(check_interval_seconds)

    return current_status
