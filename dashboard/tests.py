import io
from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bson import ObjectId
from django.core import signing
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase
from pymongo import ReturnDocument

from dashboard.management.commands.create_admin import Command as CreateAdminCommand
from dashboard.middleware import SESSION_COOKIE, SESSION_SALT, account_for_request
from dashboard.mongodb import _record, populate_task_completion, toggle_task


class AuthenticatedClientMixin:
    account_role = 'user'

    def setUp(self):
        super().setUp()
        self.account = SimpleNamespace(
            id=str(ObjectId()),
            username='test-user',
            display_name='Test User',
            role=self.account_role,
        )
        active_patches = (
            patch('dashboard.middleware.account_for_request', return_value=self.account),
            patch('dashboard.middleware.record_activity'),
        )
        for active_patch in active_patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)


class MongoRecordTests(SimpleTestCase):
    def test_mongo_document_is_converted_for_templates(self):
        object_id = ObjectId()
        record = _record({
            '_id': object_id,
            'date': '2026-10-07',
            'scheduled_time': '09:30',
        })

        self.assertEqual(record.id, str(object_id))
        self.assertEqual(record.date, date(2026, 10, 7))
        self.assertEqual(record.scheduled_time, time(9, 30))


class CreateAdminCommandTests(SimpleTestCase):
    @patch('dashboard.management.commands.create_admin.create_account')
    @patch('dashboard.management.commands.create_admin.make_password', return_value='hashed')
    @patch('dashboard.management.commands.create_admin.getpass.getpass')
    @patch('dashboard.management.commands.create_admin.sys.stdin')
    @patch('dashboard.management.commands.create_admin.get_collection')
    def test_creates_admin_from_interactive_terminal(
        self, get_collection, stdin, getpass_prompt, make_password, create_account
    ):
        get_collection.return_value.count_documents.return_value = 0
        stdin.isatty.return_value = True
        getpass_prompt.side_effect = ['correct-horse-battery', 'correct-horse-battery']

        command = CreateAdminCommand(stdout=io.StringIO())
        command.handle(username='ybalaji', email='')

        make_password.assert_called_once_with('correct-horse-battery')
        create_account.assert_called_once_with(
            'ybalaji', '', 'ybalaji', 'admin', 'hashed'
        )

    @patch('dashboard.management.commands.create_admin.sys.stdin')
    @patch('dashboard.management.commands.create_admin.get_collection')
    def test_reports_noninteractive_terminal(self, get_collection, stdin):
        get_collection.return_value.count_documents.return_value = 0
        stdin.isatty.return_value = False

        command = CreateAdminCommand()
        with self.assertRaisesMessage(
            CommandError, 'Run this command in an interactive terminal'
        ):
            command.handle(username='ybalaji', email='')

    @patch('dashboard.mongodb.get_collection')
    def test_task_toggle_uses_atomic_mongodb_update(self, get_collection):
        object_id = ObjectId()
        tasks_collection = MagicMock()
        tasks_collection.find_one.return_value = {'_id': object_id}
        completion_collection = MagicMock()
        completion_collection.find_one_and_update.return_value = {
            'is_completed': True
        }
        get_collection.side_effect = [tasks_collection, completion_collection]

        self.assertTrue(toggle_task(str(object_id), 'user-1'))

        update = completion_collection.find_one_and_update.call_args
        self.assertEqual(
            update.args[0], {'task_id': str(object_id), 'account_id': 'user-1'}
        )
        self.assertTrue(update.kwargs['upsert'])
        self.assertIs(update.kwargs['return_document'], ReturnDocument.AFTER)

    @patch('dashboard.mongodb.get_collection')
    def test_task_completion_is_scoped_to_one_account(self, get_collection):
        task = SimpleNamespace(id='task-1')
        collection = get_collection.return_value
        collection.find.return_value = [
            {'task_id': 'task-1', 'is_completed': True}
        ]

        populate_task_completion([task], 'user-1')

        self.assertTrue(task.is_completed)
        query = collection.find.call_args.args[0]
        self.assertEqual(query['account_id'], 'user-1')
        self.assertEqual(query['task_id'], {'$in': ['task-1']})

    @patch('dashboard.mongodb.get_collection')
    def test_new_account_starts_with_tasks_incomplete(self, get_collection):
        task = SimpleNamespace(id='task-1')
        get_collection.return_value.find.return_value = []

        populate_task_completion([task], 'user-2')

        self.assertFalse(task.is_completed)

    @patch('dashboard.mongodb.get_collection')
    def test_invalid_task_id_is_not_sent_to_mongodb(self, get_collection):
        self.assertIsNone(toggle_task('not-an-object-id', 'user-1'))
        get_collection.assert_not_called()


class AuthenticationViewTests(SimpleTestCase):
    @patch('dashboard.middleware.find_account_by_id')
    def test_signed_cookie_resolves_its_account(self, find_account):
        account = SimpleNamespace(id=str(ObjectId()), role='user')
        find_account.return_value = account
        request = RequestFactory().get('/')
        request.COOKIES[SESSION_COOKIE] = signing.dumps(
            {'account_id': account.id}, salt=SESSION_SALT
        )

        self.assertIs(account_for_request(request), account)
        find_account.assert_called_once_with(account.id)

    @patch('dashboard.middleware.find_account_by_id')
    def test_tampered_cookie_is_rejected(self, find_account):
        request = RequestFactory().get('/')
        request.COOKIES[SESSION_COOKIE] = 'invalid-session-token'

        self.assertIsNone(account_for_request(request))
        find_account.assert_not_called()

    def test_unauthenticated_page_redirects_to_login(self):
        response = self.client.get('/tasks/')

        self.assertRedirects(
            response, '/login/?next=%2Ftasks%2F', fetch_redirect_response=False
        )

    def test_unauthenticated_api_request_is_rejected(self):
        response = self.client.post('/api/toggle-task/not-an-id/')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Authentication required.')

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.check_password', return_value=True)
    @patch('dashboard.views.find_account_by_username')
    def test_login_sets_http_only_signed_cookie(
        self, find_account, _check_password, _record_activity
    ):
        find_account.return_value = SimpleNamespace(
            id=str(ObjectId()), password_hash='hashed'
        )

        response = self.client.post(
            '/login/', {'username': 'member', 'password': 'correct-password'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertTrue(response.cookies['dashboard_session']['httponly'])
        self.assertEqual(response.cookies['dashboard_session']['samesite'], 'Lax')


class DashboardViewTests(AuthenticatedClientMixin, SimpleTestCase):
    @patch('dashboard.views.find_records', return_value=[])
    @patch('dashboard.views.find_one_record')
    def test_dashboard_renders_using_mongodb_records(self, find_one, find_many):
        find_one.side_effect = [
            SimpleNamespace(name='Balaji', streak_days=1, focus_mode=False),
            None,
            None,
        ]

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Daily Progress')
        self.assertEqual(find_one.call_count, 3)
        self.assertGreater(find_many.call_count, 0)


class TaskViewTests(AuthenticatedClientMixin, SimpleTestCase):
    @patch('dashboard.views.find_records')
    def test_tasks_page_includes_study_progress_and_removes_old_sidebar_items(self, find_many):
        find_many.side_effect = [
            [],
            [],
            [SimpleNamespace(date=date(2026, 10, 7), hours=2.5)],
        ]

        response = self.client.get('/tasks/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Study Progress')
        self.assertContains(response, '2.5h')
        self.assertNotContains(response, 'Practice')
        self.assertNotContains(response, 'Notes')
        self.assertNotContains(response, 'nav-label">Progress')
        self.assertNotContains(response, 'RESOURCES')
        self.assertNotContains(response, 'Books')
        self.assertNotContains(response, 'Courses')

    def test_old_progress_url_redirects_to_tasks(self):
        response = self.client.get('/progress/')

        self.assertRedirects(response, '/tasks/')

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.find_one_record')
    @patch('dashboard.views.toggle_task_record', return_value=True)
    def test_task_completion_is_written_to_activity_log(
        self, _toggle_task, _find_one, record_activity
    ):
        task_id = str(ObjectId())

        response = self.client.post(f'/api/toggle-task/{task_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['completed'])
        self.assertEqual(
            record_activity.call_args.kwargs['action'], 'Task updated'
        )
        self.assertIn(
            'marked complete',
            record_activity.call_args.kwargs['details'],
        )


class CalendarViewTests(AuthenticatedClientMixin, SimpleTestCase):
    @patch('dashboard.views.populate_task_completion')
    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records')
    def test_calendar_shows_selected_day_tasks(
        self, find_many, _find_one, _populate_completion
    ):
        find_many.return_value = [
            SimpleNamespace(
                id=str(ObjectId()),
                date=date(2026, 2, 5),
                scheduled_time=time(9, 30),
                is_completed=False,
                color='#60a5fa',
                title='Review project plan',
            ),
            SimpleNamespace(
                id=str(ObjectId()),
                date=date(2026, 2, 6),
                scheduled_time=None,
                is_completed=False,
                color='#a78bfa',
                title='Prepare presentation',
            ),
        ]

        response = self.client.get(
            '/calendar/?month=2026-02&day=2026-02-05'
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'February, 2026')
        self.assertContains(response, 'Review project plan')
        self.assertContains(response, '9:30')
        self.assertNotContains(response, 'Prepare presentation')
        self.assertContains(response, 'Has tasks')

        query = find_many.call_args.args[1]['date']
        self.assertEqual(query['$gte'], '2026-02-01')
        self.assertEqual(query['$lt'], '2026-03-01')

    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    def test_calendar_defaults_to_current_month_and_empty_day(self, _find_many, _find_one):
        response = self.client.get('/calendar/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tasks scheduled for this day.')

    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    def test_calendar_ignores_invalid_month_and_day(self, _find_many, _find_one):
        response = self.client.get(
            '/calendar/?month=not-a-month&day=not-a-day'
        )

        self.assertEqual(response.status_code, 200)


class AdminViewTests(AuthenticatedClientMixin, SimpleTestCase):
    account_role = 'admin'

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    @patch('dashboard.views.find_accounts', return_value=[])
    @patch('dashboard.views.get_collection')
    def test_admin_can_add_roadmap_topic(
        self, get_collection, _find_accounts, _find_records,
        _find_one, _record_activity
    ):
        response = self.client.post('/admin/', {
            'action': 'add_roadmap',
            'name': 'Python',
            'progress': '25',
            'order': '1',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Roadmap topic added.')
        inserted = get_collection.return_value.insert_one.call_args.args[0]
        self.assertEqual(inserted, {'name': 'Python', 'progress': 25, 'order': 1})

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    @patch('dashboard.views.find_accounts', return_value=[])
    @patch('dashboard.views.get_collection')
    def test_admin_can_add_task(
        self, get_collection, _find_accounts, _find_records,
        _find_one, _record_activity
    ):
        response = self.client.post('/admin/', {
            'action': 'add_task',
            'title': 'Review Python',
            'date': '2026-10-08',
            'scheduled_time': '09:30',
            'priority': 'high',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task added.')
        inserted = get_collection.return_value.insert_one.call_args.args[0]
        self.assertEqual(inserted['date'], '2026-10-08')
        self.assertEqual(inserted['scheduled_time'], '09:30:00')
        self.assertEqual(inserted['priority'], 'high')
        self.assertFalse(inserted['is_completed'])

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    @patch('dashboard.views.find_accounts', return_value=[])
    @patch('dashboard.views.get_collection')
    def test_admin_can_add_project(
        self, get_collection, _find_accounts, _find_records,
        _find_one, _record_activity
    ):
        response = self.client.post('/admin/', {
            'action': 'add_project',
            'name': 'Dashboard',
            'description': 'Learning project',
            'tech_stack': 'Django, MongoDB',
            'progress': '40',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Project added.')
        inserted = get_collection.return_value.insert_one.call_args.args[0]
        self.assertEqual(inserted['name'], 'Dashboard')
        self.assertEqual(inserted['progress'], 40)
        self.assertFalse(inserted['is_active'])

    @patch('dashboard.views.record_activity')
    @patch('dashboard.views.make_password', return_value='encoded-password')
    @patch('dashboard.views.create_account')
    @patch('dashboard.views.find_one_record', return_value=None)
    @patch('dashboard.views.find_records', return_value=[])
    @patch('dashboard.views.find_accounts', return_value=[])
    def test_admin_can_create_a_user_account(
        self, _find_accounts, _find_records, _find_one,
        create_user, make_password, _record_activity
    ):
        response = self.client.post('/admin/', {
            'action': 'add_account',
            'username': 'learner-1',
            'display_name': 'Learner One',
            'email': 'learner@example.com',
            'role': 'user',
            'password': 'a-secure-password',
            'password_confirmation': 'a-secure-password',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account created.')
        make_password.assert_called_once_with('a-secure-password')
        create_user.assert_called_once_with(
            'learner-1', 'learner@example.com', 'Learner One',
            'user', 'encoded-password'
        )

    def test_user_cannot_open_admin_console(self):
        user_account = SimpleNamespace(
            id=str(ObjectId()),
            username='member',
            display_name='Member',
            role='user',
        )
        with patch(
            'dashboard.middleware.account_for_request',
            return_value=user_account,
        ):
            response = self.client.get('/admin/')

        self.assertEqual(response.status_code, 403)
