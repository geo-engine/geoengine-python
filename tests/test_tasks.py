'''Tests regarding task functionality'''

import unittest
from uuid import UUID

import datetime
import requests_mock

import geoengine as ge
from geoengine import GeoEngineException, DEFAULT_ISO_TIME_FORMAT
from geoengine.tasks import CompletedTaskStatusInfo, TaskStatus, RunningTaskStatusInfo, \
    AbortedTaskStatusInfo, FailedTaskStatusInfo, TaskId, Task


class TaskTests(unittest.TestCase):
    '''Test runner regarding task functionality'''

    def test_get_task_list_empty(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[])

            client = ge.create_client('http://mock-instance')

            expected_result = []

            task_list = client.task_list()

            self.assertEqual(len(task_list), 0)
            self.assertEqual(task_list, expected_result)

    def test_get_task_list_all_types(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[
                {
                    'taskId': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'taskType': 'dummy',
                    'description': 'No operation',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
                {
                    'taskId': 'a04d2e1b-db24-42cb-a620-1d7803df3abe',
                    'taskType': 'dummy',
                    'description': 'No operation',
                    'status': 'running',
                    'pctComplete': '0.00%',
                    'estimatedTimeRemaining': '? (± ?)',
                    'info': 'generic running info',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
                {
                    'taskId': '01d68e7b-c69f-4132-b758-538f2f05acf0',
                    'status': 'aborted',
                    'cleanUp': {'status': 'noCleanUp'},
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
                {
                    'taskId': '1ccba900-167d-4dcf-9001-5ce3c0b20844',
                    'status': 'failed',
                    'error': 'TileLimitExceeded',
                    'cleanUp': {'status': 'completed', 'info': None},
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
            ])

            client = ge.create_client('http://mock-instance')

            expected_start_time = datetime.datetime.strptime('2023-02-16T15:25:45.390Z', DEFAULT_ISO_TIME_FORMAT)
            expected_result = [
                (Task(session=client.get_session(), task_id=TaskId(UUID('e07aec1e-387a-4d24-8041-fbfba37eae2b'))),
                 CompletedTaskStatusInfo(TaskStatus.COMPLETED, expected_start_time, 'generic info', '00:00:05',
                                         'dummy', 'No operation')),
                (Task(session=client.get_session(), task_id=TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe'))),
                 RunningTaskStatusInfo(TaskStatus.RUNNING, expected_start_time,
                                       '0.00%', '? (± ?)', 'generic running info',
                                       'dummy', 'No operation')),
                (Task(session=client.get_session(), task_id=TaskId(UUID('01d68e7b-c69f-4132-b758-538f2f05acf0'))),
                 AbortedTaskStatusInfo(TaskStatus.ABORTED, expected_start_time, {'status': 'noCleanUp'})),
                (Task(session=client.get_session(), task_id=TaskId(UUID('1ccba900-167d-4dcf-9001-5ce3c0b20844'))),
                 FailedTaskStatusInfo(TaskStatus.FAILED, expected_start_time, 'TileLimitExceeded',
                                      {'status': 'completed', 'info': None})),
            ]

            task_list = client.task_list()

            self.assertEqual(len(task_list), 4)
            self.assertEqual(task_list, expected_result)

    def test_get_task_list_unknown_status(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[
                {
                    'taskId': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'taskType': 'dummy',
                    'description': 'No operation',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
                {
                    'taskId': 'ee4bc7ca-e637-4427-a617-2d2aa79d1406',
                    'status': 'clear',
                    'pctComplete': '0.00%',
                    'estimatedTimeRemaining': '? (± ?)',
                    'info': 'generic running info',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
            ])

            client = ge.create_client('http://mock-instance')

            self.assertRaises(ValueError, client.task_list, 0)

    def test_get_task_list_malformed(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[
                {
                    'taskId': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
                {
                    'taskId': 'ee4f1ed9-fd06-40be-90f5-d6289c154fcd',
                    'status': 'running',
                    # Missing pct_complete field
                    'estimatedTimeRemaing': '? (± ?)',
                    'info': 'generic running info',
                    'timeStarted': '2023-02-16T15:25:45.390Z'
                },
            ])

            client = ge.create_client('http://mock-instance')

            self.assertRaises(GeoEngineException, client.task_list, 0)

    def test_get_task_status(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            # Correct results
            m.get('http://mock-instance/tasks/e07aec1e-387a-4d24-8041-fbfba37eae2b/status',
                  json={
                      'status': 'completed',
                      'taskType': 'dummy',
                      'description': 'No operation',
                      'info': 'generic info',
                      'timeTotal': '00:00:05',
                      'timeStarted': '2023-02-16T15:25:45.390Z'})
            m.get('http://mock-instance/tasks/a04d2e1b-db24-42cb-a620-1d7803df3abe/status',
                  json={
                      'status': 'running',
                      'taskType': 'dummy',
                      'description': 'No operation',
                      'pctComplete': '0.00%',
                      'estimatedTimeRemaining': '? (± ?)',
                      'info': 'generic running info',
                      'timeStarted': '2023-02-16T15:25:45.390Z'})
            m.get('http://mock-instance/tasks/01d68e7b-c69f-4132-b758-538f2f05acf0/status',
                  json={'status': 'aborted',
                        'cleanUp': {'status': 'noCleanUp'}, })
            m.get('http://mock-instance/tasks/1ccba900-167d-4dcf-9001-5ce3c0b20844/status',
                  json={'status': 'failed',
                        'error': 'TileLimitExceeded',
                        'cleanUp': {'status': 'completed', 'info': None},
                        'timeStarted': '2023-02-16T15:25:45.390Z'})

            # Unknown status
            m.get('http://mock-instance/tasks/ee4bc7ca-e637-4427-a617-2d2aa79d1406/status',
                  json={
                      'status': 'clear',
                      'pctComplete': '0.00%',
                      'estimatedTimeRemaining': '? (± ?)',
                      'info': 'generic running info',
                      'timeStarted': '2023-02-16T15:25:45.390Z'})

            # Malformed info
            m.get('http://mock-instance/tasks/ee4f1ed9-fd06-40be-90f5-d6289c154fcd/status',
                  json={
                      'status': 'running',
                      'taskType': 'dummy',
                      'description': 'No operation',
                      # Missing pct_complete field
                      'estimatedTimeRemaining': '? (± ?)',
                      'info': 'generic running info',
                      'timeStarted': '2023-02-16T15:25:45.390Z'})

            client = ge.create_client('http://mock-instance')

            # Correct results
            expected_start_time = datetime.datetime.strptime('2023-02-16T15:25:45.390Z', DEFAULT_ISO_TIME_FORMAT)
            expected_results = [
                CompletedTaskStatusInfo(TaskStatus.COMPLETED, expected_start_time, 'generic info', '00:00:05',
                                        'dummy', 'No operation'),
                RunningTaskStatusInfo(TaskStatus.RUNNING, expected_start_time,
                                      '0.00%', '? (± ?)', 'generic running info',
                                      'dummy', 'No operation'),
                AbortedTaskStatusInfo(TaskStatus.ABORTED, expected_start_time, {'status': 'noCleanUp'}),
                FailedTaskStatusInfo(TaskStatus.FAILED, expected_start_time, 'TileLimitExceeded',
                                     {'status': 'completed', 'info': None}),
            ]

            completed_task = Task(client.get_session(), TaskId(UUID('e07aec1e-387a-4d24-8041-fbfba37eae2b')))
            running_task = Task(client.get_session(), TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe')))
            aborted_task = Task(client.get_session(), TaskId(UUID('01d68e7b-c69f-4132-b758-538f2f05acf0')))
            failed_task = Task(client.get_session(), TaskId(UUID('1ccba900-167d-4dcf-9001-5ce3c0b20844')))

            self.assertEqual(completed_task.get_status(), expected_results[0])
            self.assertEqual(running_task.get_status(), expected_results[1])
            self.assertEqual(aborted_task.get_status(), expected_results[2])
            self.assertEqual(failed_task.get_status(), expected_results[3])

            # Unknown status
            unknown_status_task = Task(client.get_session(), TaskId(UUID('ee4bc7ca-e637-4427-a617-2d2aa79d1406')))
            with self.assertRaises(ValueError):
                unknown_status_task.get_status()

            # Malformed
            malformed_status_task = Task(client.get_session(), TaskId(UUID('ee4f1ed9-fd06-40be-90f5-d6289c154fcd')))
            with self.assertRaises(GeoEngineException):
                malformed_status_task.get_status()

    def test_get_abort_task(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.delete('http://mock-instance/tasks/a04d2e1b-db24-42cb-a620-1d7803df3abe',
                     status_code=200, )
            m.delete('http://mock-instance/tasks/9f008e47-645b-48de-a513-748a1d0c2a3f',
                     status_code=400,
                     json={
                         'error': 'TaskError',
                         'message': 'TaskError: Task not found with id: 9f008e47-645b-48de-a513-748a1d0c2a3f'})

            client = ge.create_client('http://mock-instance')

            abort_success_task = Task(client.get_session(), TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe')))
            self.assertEqual(None, abort_success_task.abort())

            abort_failed_task = Task(client.get_session(), TaskId(UUID('9f008e47-645b-48de-a513-748a1d0c2a3f')))
            with self.assertRaises(GeoEngineException):
                abort_failed_task.abort()


if __name__ == '__main__':
    unittest.main()
