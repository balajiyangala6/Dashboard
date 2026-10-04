from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
import json
import datetime

from .models import (
    Profile, RoadmapTopic, Task, Project,
    StudySession, Activity, QuickLink, Quote
)


def dashboard(request):
    today = timezone.localdate()
    profile = Profile.objects.first()

    # Tasks
    today_tasks = Task.objects.filter(date=today)
    completed_tasks = today_tasks.filter(is_completed=True).count()
    total_tasks = today_tasks.count()

    # Study hours today
    today_session = StudySession.objects.filter(date=today).first()
    study_seconds = int((today_session.hours if today_session else 0) * 3600)
    study_h = study_seconds // 3600
    study_m = (study_seconds % 3600) // 60

    # Study hours this week (Mon–Sun)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_sessions = StudySession.objects.filter(date__gte=week_start, date__lte=today)
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

    # Daily progress (% of tasks done today)
    daily_progress = int((completed_tasks / total_tasks * 100) if total_tasks else 0)

    # Roadmap
    roadmap_topics = RoadmapTopic.objects.all()

    # Current project
    current_project = Project.objects.filter(is_active=True).first()

    # Recent activity
    recent_activities = Activity.objects.all()[:5]

    # Quick links
    quick_links = QuickLink.objects.all()

    # Daily quote
    quote = Quote.objects.filter(is_active=True).order_by('?').first()

    # Greeting
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
    topics = RoadmapTopic.objects.all()
    context = {'topics': topics, 'active_page': 'roadmap'}
    return render(request, 'dashboard/roadmap.html', context)


def tasks(request):
    today = timezone.localdate()
    all_tasks = Task.objects.all().order_by('-date', 'scheduled_time')
    today_tasks = Task.objects.filter(date=today)
    context = {
        'all_tasks': all_tasks,
        'today_tasks': today_tasks,
        'active_page': 'tasks',
        'today': today,
    }
    return render(request, 'dashboard/tasks.html', context)


def projects(request):
    all_projects = Project.objects.all()
    context = {'projects': all_projects, 'active_page': 'projects'}
    return render(request, 'dashboard/projects.html', context)


def progress(request):
    sessions = StudySession.objects.all()[:30]
    context = {'sessions': sessions, 'active_page': 'progress'}
    return render(request, 'dashboard/progress.html', context)


@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_completed = not task.is_completed
    task.save()
    return JsonResponse({'completed': task.is_completed})


@require_POST
def toggle_focus_mode(request):
    profile = Profile.objects.first()
    if profile:
        profile.focus_mode = not profile.focus_mode
        profile.save()
        return JsonResponse({'focus_mode': profile.focus_mode})
    return JsonResponse({'error': 'No profile'}, status=404)
