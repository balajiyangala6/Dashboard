import datetime
import random
import re
import calendar as month_calendar

from bson import ObjectId
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .mongodb import (
    DESCENDING,
    create_account,
    delete_record,
    find_accounts,
    find_account_by_username,
    find_one_record,
    find_records,
    get_collection,
    populate_task_completion,
    record_activity,
    toggle_focus_mode as toggle_focus_mode_record,
    toggle_task as toggle_task_record,
)
from .middleware import SESSION_COOKIE, admin_required, set_account_cookie
from pymongo.errors import DuplicateKeyError


def dashboard(request):
    today = timezone.localdate()
    profile = find_one_record('profiles', {'_id': 'main'})

    today_tasks = find_records(
        'tasks',
        {'date': today.isoformat()},
        sort=[('scheduled_time', 1), ('_id', 1)],
    )
    populate_task_completion(today_tasks, request.account.id)
    completed_tasks = sum(task.is_completed for task in today_tasks)
    total_tasks = len(today_tasks)

    today_session = find_one_record('study_sessions', {'date': today.isoformat()})
    study_seconds = int((today_session.hours if today_session else 0) * 3600)
    study_h = study_seconds // 3600
    study_m = (study_seconds % 3600) // 60

    week_start = today - datetime.timedelta(days=today.weekday())
    week_sessions = find_records(
        'study_sessions',
        {'date': {'$gte': week_start.isoformat(), '$lte': today.isoformat()}},
    )
    week_map = {s.date: s.hours for s in week_sessions}
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    week_chart = []
    for i, day_name in enumerate(days_of_week):
        d = week_start + datetime.timedelta(days=i)
        week_chart.append({
            'day': day_name,
            'hours': week_map.get(d, 0),
            'is_today': d == today,
        })

    max_week_hours = max((d['hours'] for d in week_chart), default=1) or 1

    daily_progress = int((completed_tasks / total_tasks * 100) if total_tasks else 0)

    roadmap_topics = find_records('roadmap_topics', sort=[('order', 1)])
    current_project = find_one_record('projects', {'is_active': True})
    recent_activities = find_records(
        'activities', sort=[('timestamp', DESCENDING)], limit=5
    )
    quick_links = find_records('quick_links', sort=[('order', 1)])
    quotes = find_records('quotes', {'is_active': True})
    quote = random.choice(quotes) if quotes else None

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Good Morning"
        greeting_emoji = "☀️"
    elif hour < 17:
        greeting = "Good Afternoon"
        greeting_emoji = "👋"
    else:
        greeting = "Good Evening"
        greeting_emoji = "🌙"

    context = {
        'profile': profile,
        'today_tasks': today_tasks,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'daily_progress': daily_progress,
        'study_h': study_h,
        'study_m': study_m,
        'week_chart': week_chart,
        'max_week_hours': max_week_hours,
        'roadmap_topics': roadmap_topics,
        'current_project': current_project,
        'recent_activities': recent_activities,
        'quick_links': quick_links,
        'quote': quote,
        'greeting': greeting,
        'greeting_emoji': greeting_emoji,
        'today': today,
        'active_page': 'dashboard',
    }
    return render(request, 'dashboard/dashboard.html', context)


def roadmap(request):
    topics = find_records('roadmap_topics', sort=[('order', 1)])
    context = {'topics': topics, 'active_page': 'roadmap'}
    return render(request, 'dashboard/roadmap.html', context)

def tasks(request):
    today = timezone.localdate()
    all_tasks = find_records(
        'tasks', sort=[('date', DESCENDING), ('scheduled_time', 1)]
    )
    today_tasks = find_records(
        'tasks',
        {'date': today.isoformat()},
        sort=[('scheduled_time', 1), ('_id', 1)],
    )
    sessions = find_records(
        'study_sessions', sort=[('date', DESCENDING)], limit=30
    )
    populate_task_completion(all_tasks, request.account.id)
    populate_task_completion(today_tasks, request.account.id)
    context = {
        'all_tasks': all_tasks,
        'today_tasks': today_tasks,
        'sessions': sessions,
        'active_page': 'tasks',
        'today': today,
    }
    return render(request, 'dashboard/tasks.html', context)


def projects(request):
    all_projects = find_records('projects')
    context = {'projects': all_projects, 'active_page': 'projects'}
    return render(request, 'dashboard/projects.html', context)


def progress(request):
    return redirect('dashboard:tasks')


def login(request):
    if request.account is not None:
        return redirect('dashboard:dashboard')

    next_url = request.POST.get('next') or request.GET.get('next', '')
    error = None
    if request.method == 'POST':
        account = find_account_by_username(request.POST.get('username', ''))
        password = request.POST.get('password', '')
        if account and check_password(password, account.password_hash):
            destination = next_url
            if not url_has_allowed_host_and_scheme(
                destination, allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                destination = '/'
            record_activity(
                account, action='Signed in', method=request.method,
                path=request.path, status=302,
            )
            response = redirect(destination)
            return set_account_cookie(response, account.id, request.is_secure())
        error = 'Incorrect username or password.'

    return render(request, 'dashboard/login.html', {
        'error': error,
        'next': next_url,
        'profile': None,
    })


@require_POST
def logout(request):
    response = redirect('dashboard:login')
    response.delete_cookie(
        SESSION_COOKIE, path='/', samesite='Lax',
        secure=request.is_secure(),
    )
    return response


@admin_required
def admin_console(request):
    error = None
    notice = None
    try:
        activity_page = max(1, int(request.GET.get('activity_page', '1')))
    except ValueError:
        activity_page = 1
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add_roadmap':
                name = request.POST.get('name', '').strip()
                progress_value = int(request.POST.get('progress', ''))
                order = int(request.POST.get('order', ''))
                if not name or not 0 <= progress_value <= 100 or order < 0:
                    raise ValueError('Enter a topic, a progress from 0 to 100, and a non-negative order.')
                get_collection('roadmap_topics').insert_one({
                    'name': name,
                    'progress': progress_value,
                    'order': order,
                })
                notice = 'Roadmap topic added.'
            elif action == 'add_task':
                title = request.POST.get('title', '').strip()
                date_value = datetime.date.fromisoformat(request.POST.get('date', ''))
                time_value = request.POST.get('scheduled_time', '').strip()
                priority = request.POST.get('priority', 'medium')
                if not title or priority not in {'low', 'medium', 'high'}:
                    raise ValueError('Enter a task title and choose a valid priority.')
                scheduled_time = (
                    datetime.time.fromisoformat(time_value).isoformat()
                    if time_value else None
                )
                get_collection('tasks').insert_one({
                    'title': title,
                    'date': date_value.isoformat(),
                    'scheduled_time': scheduled_time,
                    'priority': priority,
                    'color': '#a78bfa',
                    'is_completed': False,
                })
                notice = 'Task added.'
            elif action == 'add_project':
                name = request.POST.get('name', '').strip()
                progress_value = int(request.POST.get('progress', ''))
                if not name or not 0 <= progress_value <= 100:
                    raise ValueError('Enter a project name and progress from 0 to 100.')
                get_collection('projects').insert_one({
                    'name': name,
                    'description': request.POST.get('description', '').strip(),
                    'tech_stack': request.POST.get('tech_stack', '').strip(),
                    'icon': '📁',
                    'progress': progress_value,
                    'is_active': False,
                })
                notice = 'Project added.'
            elif action == 'add_account':
                username = request.POST.get('username', '').strip()
                display_name = request.POST.get('display_name', '').strip()
                email = request.POST.get('email', '').strip()
                role = request.POST.get('role', '')
                password = request.POST.get('password', '')
                password_confirmation = request.POST.get('password_confirmation', '')
                if not re.fullmatch(r'[A-Za-z0-9_.-]{3,80}', username):
                    raise ValueError('Username must be 3-80 characters using letters, numbers, dots, underscores, or hyphens.')
                if not display_name or role not in {'admin', 'user'}:
                    raise ValueError('Enter a display name and a valid account role.')
                if email:
                    validate_email(email)
                if len(password) < 12:
                    raise ValueError('Password must be at least 12 characters.')
                if password != password_confirmation:
                    raise ValueError('The passwords do not match.')
                create_account(
                    username, email, display_name, role, make_password(password)
                )
                notice = 'Account created.'
            elif action == 'delete_record':
                collection = request.POST.get('collection', '')
                if collection not in {'roadmap_topics', 'tasks', 'projects'}:
                    raise ValueError('Choose a valid content type.')
                if not delete_record(collection, request.POST.get('record_id', '')):
                    raise ValueError('That record no longer exists.')
                notice = 'Record deleted.'
            else:
                raise ValueError('Choose a valid action.')
        except ValueError as exc:
            error = str(exc) or 'Enter valid values in all required fields.'
        except ValidationError:
            error = 'Enter a valid email address.'
        except DuplicateKeyError:
            error = 'That username is already in use.'

        if notice:
            record_activity(
                request.account, action='Admin content change',
                method=request.method, path=request.path, status=200,
                details=notice,
            )

    topics = find_records('roadmap_topics', sort=[('order', 1)])
    activity_records = find_records(
        'activity_logs',
        sort=[('timestamp', DESCENDING)],
        limit=101,
        skip=(activity_page - 1) * 100,
    )
    context = {
        'profile': find_one_record('profiles', {'_id': 'main'}),
        'topics': topics,
        'tasks': find_records(
            'tasks', sort=[('date', DESCENDING), ('scheduled_time', 1)]
        ),
        'projects': find_records('projects', sort=[('name', 1)]),
        'accounts': find_accounts(),
        'activity': activity_records[:100],
        'activity_page': activity_page,
        'activity_has_previous': activity_page > 1,
        'activity_has_next': len(activity_records) > 100,
        'next_roadmap_order': len(topics) + 1,
        'error': error,
        'notice': notice,
        'active_page': 'admin',
    }
    populate_task_completion(context['tasks'], request.account.id)
    return render(request, 'dashboard/admin.html', context)


def calendar(request):
    today = timezone.localdate()
    selected_date = today
    requested_day = request.GET.get('day')
    if requested_day:
        try:
            selected_date = datetime.date.fromisoformat(requested_day)
        except ValueError:
            selected_date = today

    requested_month = request.GET.get('month')
    if requested_month:
        try:
            displayed_month = datetime.datetime.strptime(
                requested_month, '%Y-%m'
            ).date().replace(day=1)
        except ValueError:
            displayed_month = selected_date.replace(day=1)
    else:
        displayed_month = selected_date.replace(day=1)

    if selected_date.year != displayed_month.year or selected_date.month != displayed_month.month:
        selected_date = (
            today if today.year == displayed_month.year and today.month == displayed_month.month
            else displayed_month
        )

    next_month = (
        displayed_month.replace(year=displayed_month.year + 1, month=1)
        if displayed_month.month == 12
        else displayed_month.replace(month=displayed_month.month + 1)
    )
    previous_month = (
        displayed_month.replace(year=displayed_month.year - 1, month=12)
        if displayed_month.month == 1
        else displayed_month.replace(month=displayed_month.month - 1)
    )
    month_tasks = find_records(
        'tasks',
        {
            'date': {
                '$gte': displayed_month.isoformat(),
                '$lt': next_month.isoformat(),
            },
        },
        sort=[('date', 1), ('scheduled_time', 1)],
    )
    task_counts = {}
    for task in month_tasks:
        task_counts[task.date] = task_counts.get(task.date, 0) + 1
    selected_day_tasks = [
        task for task in month_tasks if task.date == selected_date
    ]
    populate_task_completion(selected_day_tasks, request.account.id)

    weeks = []
    for week in month_calendar.Calendar(firstweekday=6).monthdatescalendar(
        displayed_month.year, displayed_month.month
    ):
        weeks.append([
            {
                'date': day,
                'day': day.day,
                'in_month': day.month == displayed_month.month,
                'is_selected': day == selected_date,
                'is_today': day == today,
                'task_count': task_counts.get(day, 0),
            }
            for day in week
        ])

    context = {
        'profile': find_one_record('profiles', {'_id': 'main'}),
        'weeks': weeks,
        'month_tasks': selected_day_tasks,
        'selected_date': selected_date,
        'displayed_month': displayed_month,
        'previous_month': previous_month,
        'next_month': next_month,
        'active_page': 'calendar',
    }
    return render(request, 'dashboard/calendar.html', context)


@require_POST
def toggle_task(request, task_id):
    completed = toggle_task_record(task_id, request.account.id)
    if completed is None:
        raise Http404('Task not found.')
    task = find_one_record('tasks', {'_id': ObjectId(task_id)})
    task_title = task.title if task else task_id
    record_activity(
        request.account, action='Task updated', method=request.method,
        path=request.path, status=200,
        details=f'Task "{task_title}" marked {"complete" if completed else "incomplete"}.',
    )
    return JsonResponse({'completed': completed})


@require_POST
def toggle_focus_mode(request):
    focus_mode = toggle_focus_mode_record()
    if focus_mode is None:
        return JsonResponse({'error': 'No profile'}, status=404)
    return JsonResponse({'focus_mode': focus_mode})
