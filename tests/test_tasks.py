'''Tests regarding task functionality'''

import unittest
from uuid import UUID

import requests_mock

import geoengine as ge
from geoengine import GeoEngineException
from geoengine.tasks import CompletedTaskStatusInfo, TaskStatus, RunningTaskStatusInfo, \
    AbortedTaskStatusInfo, FailedTaskStatusInfo, TaskId, Task


class TaskTests(unittest.TestCase):
    '''Test runner regarding task functionality'''

    def setUp(self) -> None:
        ge.reset(False)

    def test_get_task_list_empty(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[])

            ge.initialize('http://mock-instance')

            expected_result = []

            task_list = ge.tasks.get_task_list()

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
                    'task_id': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                },
                {
                    'task_id': 'a04d2e1b-db24-42cb-a620-1d7803df3abe',
                    'status': 'running',
                    'pct_complete': '0.00%',
                    'time_estimate': '? (± ?)',
                    'info': 'generic running info',
                },
                {
                    'task_id': '01d68e7b-c69f-4132-b758-538f2f05acf0',
                    'status': 'aborted',
                    'cleanUp': {'status': 'noCleanUp'}
                },
                {
                    'task_id': '1ccba900-167d-4dcf-9001-5ce3c0b20844',
                    'status': 'failed',
                    'error': 'TileLimitExceeded',
                    'cleanUp': {'status': 'completed', 'info': None}
                },
            ])

            ge.initialize('http://mock-instance')

            expected_result = [
                (Task(TaskId(UUID('e07aec1e-387a-4d24-8041-fbfba37eae2b'))),
                 CompletedTaskStatusInfo(TaskStatus.COMPLETED, 'generic info', '00:00:05')),
                (Task(TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe'))),
                 RunningTaskStatusInfo(TaskStatus.RUNNING, '0.00%', '? (± ?)', 'generic running info')),
                (Task(TaskId(UUID('01d68e7b-c69f-4132-b758-538f2f05acf0'))),
                 AbortedTaskStatusInfo(TaskStatus.ABORTED, {'status': 'noCleanUp'})),
                (Task(TaskId(UUID('1ccba900-167d-4dcf-9001-5ce3c0b20844'))),
                 FailedTaskStatusInfo(TaskStatus.FAILED, 'TileLimitExceeded', {'status': 'completed', 'info': None})),
            ]

            task_list = ge.tasks.get_task_list()

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
                    'task_id': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                },
                {
                    'task_id': 'ee4bc7ca-e637-4427-a617-2d2aa79d1406',
                    'status': 'clear',
                    'pct_complete': '0.00%',
                    'time_estimate': '? (± ?)',
                    'info': 'generic running info',
                },
            ])

            ge.initialize('http://mock-instance')

            self.assertRaises(ValueError, ge.tasks.get_task_list, 0)

    def test_get_task_list_malformed(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/list', json=[
                {
                    'task_id': 'e07aec1e-387a-4d24-8041-fbfba37eae2b',
                    'status': 'completed',
                    'info': 'generic info',
                    'timeTotal': '00:00:05',
                },
                {
                    'task_id': 'ee4f1ed9-fd06-40be-90f5-d6289c154fcd',
                    'status': 'running',
                    # Missing pct_complete field
                    'time_estimate': '? (± ?)',
                    'info': 'generic running info',
                },
            ])

            ge.initialize('http://mock-instance')

            self.assertRaises(GeoEngineException, ge.tasks.get_task_list, 0)

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
                      'info': 'generic info',
                      'timeTotal': '00:00:05', })
            m.get('http://mock-instance/tasks/a04d2e1b-db24-42cb-a620-1d7803df3abe/status',
                  json={
                      'status': 'running',
                      'pct_complete': '0.00%',
                      'time_estimate': '? (± ?)',
                      'info': 'generic running info', })
            m.get('http://mock-instance/tasks/01d68e7b-c69f-4132-b758-538f2f05acf0/status',
                  json={'status': 'aborted',
                        'cleanUp': {'status': 'noCleanUp'}, })
            m.get('http://mock-instance/tasks/1ccba900-167d-4dcf-9001-5ce3c0b20844/status',
                  json={'status': 'failed',
                        'error': 'TileLimitExceeded',
                        'cleanUp': {'status': 'completed', 'info': None}})

            # Unknown status
            m.get('http://mock-instance/tasks/ee4bc7ca-e637-4427-a617-2d2aa79d1406/status',
                  json={
                      'status': 'clear',
                      'pct_complete': '0.00%',
                      'time_estimate': '? (± ?)',
                      'info': 'generic running info', })

            # Malformed info
            m.get('http://mock-instance/tasks/ee4f1ed9-fd06-40be-90f5-d6289c154fcd/status',
                  json={
                      'status': 'running',
                      # Missing pct_complete field
                      'time_estimate': '? (± ?)',
                      'info': 'generic running info', })

            ge.initialize('http://mock-instance')

            # Correct results
            expected_results = [
                CompletedTaskStatusInfo(TaskStatus.COMPLETED, 'generic info', '00:00:05'),
                RunningTaskStatusInfo(TaskStatus.RUNNING, '0.00%', '? (± ?)', 'generic running info'),
                AbortedTaskStatusInfo(TaskStatus.ABORTED, {'status': 'noCleanUp'}),
                FailedTaskStatusInfo(TaskStatus.FAILED, 'TileLimitExceeded',
                                     {'status': 'completed', 'info': None}),
            ]

            completed_task = Task(TaskId(UUID('e07aec1e-387a-4d24-8041-fbfba37eae2b')))
            running_task = Task(TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe')))
            aborted_task = Task(TaskId(UUID('01d68e7b-c69f-4132-b758-538f2f05acf0')))
            failed_task = Task(TaskId(UUID('1ccba900-167d-4dcf-9001-5ce3c0b20844')))

            self.assertEqual(completed_task.get_status(), expected_results[0])
            self.assertEqual(running_task.get_status(), expected_results[1])
            self.assertEqual(aborted_task.get_status(), expected_results[2])
            self.assertEqual(failed_task.get_status(), expected_results[3])

            # Unknown status
            unknown_status_task = Task(TaskId(UUID('ee4bc7ca-e637-4427-a617-2d2aa79d1406')))
            with self.assertRaises(ValueError):
                unknown_status_task.get_status()

            # Malformed
            malformed_status_task = Task(TaskId(UUID('ee4f1ed9-fd06-40be-90f5-d6289c154fcd')))
            with self.assertRaises(GeoEngineException):
                malformed_status_task.get_status()

    def test_get_abort_task(self):
        with requests_mock.Mocker() as m:
            m.post('http://mock-instance/anonymous', json={
                "id": "26a4c585-8aa5-4de8-9ede-293d3cd3544a",
                "project": None,
                "view": None
            })

            m.get('http://mock-instance/tasks/a04d2e1b-db24-42cb-a620-1d7803df3abe/abort',
                  status_code=200, )
            m.get('http://mock-instance/tasks/9f008e47-645b-48de-a513-748a1d0c2a3f/abort',
                  status_code=400,
                  json={
                      'error': 'TaskError',
                      'message': 'TaskError: Task not found with id: 9f008e47-645b-48de-a513-748a1d0c2a3f'})

            ge.initialize('http://mock-instance')

            abort_success_task = Task(TaskId(UUID('a04d2e1b-db24-42cb-a620-1d7803df3abe')))
            self.assertEqual(None, abort_success_task.abort())

            abort_failed_task = Task(TaskId(UUID('9f008e47-645b-48de-a513-748a1d0c2a3f')))
            with self.assertRaises(GeoEngineException):
                abort_failed_task.abort()


if __name__ == '__main__':
    unittest.main()
