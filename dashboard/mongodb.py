from datetime import date, datetime, time, timezone
from threading import Lock
from types import SimpleNamespace

from bson import ObjectId
from bson.errors import InvalidId
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError


_client = None
_client_lock = Lock()


def get_collection(name):
    global _client

    if not settings.MONGODB_URI:
        raise ImproperlyConfigured(
            'Set MONGODB_URI to a reachable MongoDB connection URL.'
        )

    if _client is None:
        with _client_lock:
            if _client is None:
                _client = MongoClient(
                    settings.MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    tz_aware=True,
                )

    return _client[settings.MONGODB_DATABASE][name]


def _record(document):
    values = dict(document)
    values['id'] = str(values.pop('_id'))

    if isinstance(values.get('date'), datetime):
        values['date'] = values['date'].date()
    elif isinstance(values.get('date'), str):
        values['date'] = date.fromisoformat(values['date'])

    if 'scheduled_time' in values and isinstance(values['scheduled_time'], str):
        values['scheduled_time'] = time.fromisoformat(values['scheduled_time'])

    timestamp = values.get('timestamp')
    if isinstance(timestamp, datetime) and timestamp.tzinfo is None:
        values['timestamp'] = timestamp.replace(tzinfo=timezone.utc)

    return SimpleNamespace(**values)


def find_records(name, query=None, sort=None, limit=None, skip=0):
    cursor = get_collection(name).find(query or {})
    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit is not None:
        cursor = cursor.limit(limit)
    return [_record(document) for document in cursor]


def find_one_record(name, query=None):
    document = get_collection(name).find_one(query or {})
    return _record(document) if document else None


def find_account_by_username(username):
    document = get_collection('accounts').find_one({
        'username': username.strip().lower(),
        'is_active': True,
    })
    return _account_record(document, include_password=True) if document else None


def find_account_by_id(account_id):
    try:
        object_id = ObjectId(account_id)
    except (InvalidId, TypeError):
        return None

    document = get_collection('accounts').find_one({
        '_id': object_id,
        'is_active': True,
    })
    return _account_record(document) if document else None


def find_accounts():
    return [
        _account_record(document)
        for document in get_collection('accounts').find(
            {}, {'password_hash': 0}
        ).sort('created_at', DESCENDING)
    ]


def _account_record(document, include_password=False):
    values = dict(document)
    values['id'] = str(values.pop('_id'))
    if not include_password:
        values.pop('password_hash', None)
    return SimpleNamespace(**values)


def create_account(username, email, display_name, role, password_hash):
    collection = get_collection('accounts')
    collection.create_index('username', unique=True)
    return collection.insert_one({
        'username': username.strip().lower(),
        'email': email.strip().lower(),
        'display_name': display_name.strip(),
        'role': role,
        'password_hash': password_hash,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
    }).inserted_id


def record_activity(account, action, method, path, status, details=None):
    get_collection('activity_logs').insert_one({
        'account_id': account.id,
        'username': account.username,
        'role': account.role,
        'action': action,
        'method': method,
        'path': path,
        'status': status,
        'details': details or '',
        'timestamp': datetime.now(timezone.utc),
    })


def populate_task_completion(tasks, account_id):
    if not tasks:
        return tasks

    task_ids = [task.id for task in tasks]
    completion_by_task = {
        completion['task_id']: completion['is_completed']
        for completion in get_collection('task_completions').find(
            {
                'account_id': str(account_id),
                'task_id': {'$in': task_ids},
            },
            {'task_id': 1, 'is_completed': 1},
        )
    }
    for task in tasks:
        task.is_completed = completion_by_task.get(task.id, False)
    return tasks


def delete_record(name, record_id):
    try:
        object_id = ObjectId(record_id)
    except (InvalidId, TypeError):
        return False
    deleted = get_collection(name).delete_one({'_id': object_id}).deleted_count == 1
    if deleted and name == 'tasks':
        get_collection('task_completions').delete_many({
            'task_id': str(object_id),
        })
    return deleted


def toggle_task(task_id, account_id):
    try:
        object_id = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None

    if not get_collection('tasks').find_one(
        {'_id': object_id}, {'_id': 1}
    ):
        return None

    completions = get_collection('task_completions')
    completions.create_index(
        [('task_id', ASCENDING), ('account_id', ASCENDING)],
        unique=True,
    )
    query = {'task_id': str(object_id), 'account_id': str(account_id)}
    update = [{
        '$set': {
            'is_completed': {
                '$not': [{'$ifNull': ['$is_completed', False]}],
            },
            'updated_at': datetime.now(timezone.utc),
        },
    }]
    try:
        document = completions.find_one_and_update(
            query,
            update,
            projection={'is_completed': 1},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        document = completions.find_one_and_update(
            query,
            update,
            projection={'is_completed': 1},
            return_document=ReturnDocument.AFTER,
        )
    return document['is_completed'] if document else None


def toggle_focus_mode():
    document = get_collection('profiles').find_one_and_update(
        {'_id': 'main'},
        [{
            '$set': {
                'focus_mode': {
                    '$not': [{'$ifNull': ['$focus_mode', False]}],
                },
            },
        }],
        projection={'focus_mode': 1},
        return_document=ReturnDocument.AFTER,
    )
    return document['focus_mode'] if document else None


def replace_records(name, records):
    collection = get_collection(name)
    collection.delete_many({})
    if records:
        collection.insert_many(records)


__all__ = [
    'ASCENDING',
    'DESCENDING',
    'create_account',
    'delete_record',
    'find_account_by_id',
    'find_account_by_username',
    'find_accounts',
    'find_one_record',
    'find_records',
    'populate_task_completion',
    'record_activity',
    'replace_records',
    'toggle_focus_mode',
    'toggle_task',
]
