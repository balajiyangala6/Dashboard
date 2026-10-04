"""
Management command: python manage.py seed_data
Populates the database with realistic sample data matching the screenshot.
"""
import datetime
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import (
    Profile, RoadmapTopic, Task, Project,
    StudySession, Activity, QuickLink, Quote
)


class Command(BaseCommand):
    help = 'Seed the database with sample dashboard data'

    def handle(self, *args, **options):
        self.stdout.write('🌱  Seeding database...')

        # ── Profile ───────────────────────────────────
        Profile.objects.all().delete()
        Profile.objects.create(
            name='Balaji',
            tagline='Keep going!',
            streak_days=12,
            focus_mode=False,
            daily_target_hours=8.0,
        )
        self.stdout.write('  ✔  Profile')

        # ── Roadmap topics ────────────────────────────
        RoadmapTopic.objects.all().delete()
        topics = [
            ('Python Basics',    100, 1),
            ('Data Structures',   85, 2),
            ('SQL',               70, 3),
            ('ReactJS',           45, 4),
            ('System Design',     30, 5),
            ('Projects',          60, 6),
        ]
        for name, pct, order in topics:
            RoadmapTopic.objects.create(name=name, progress=pct, order=order)
        self.stdout.write('  ✔  Roadmap topics')

        # ── Tasks (today) ─────────────────────────────
        Task.objects.all().delete()
        today = timezone.localdate()
        tasks = [
            ('Python – Functions',       '09:00', True,  '#22c55e'),
            ('SQL – Joins',              '10:30', True,  '#60a5fa'),
            ('Solve 5 Problems',         '12:00', False, '#a78bfa'),
            ('Build API – User Module',  '14:00', False, '#fb923c'),
            ('Read Book – Clean Code',   '16:00', False, '#f472b6'),
        ]
        for title, t, done, color in tasks:
            h, m = map(int, t.split(':'))
            Task.objects.create(
                title=title,
                scheduled_time=datetime.time(h, m),
                is_completed=done,
                date=today,
                color=color,
            )
        self.stdout.write('  ✔  Tasks')

        # ── Project ───────────────────────────────────
        Project.objects.all().delete()
        Project.objects.create(
            name='Rental Marketplace',
            description='Connecting farmers and machinery owners. Build. Test. Grow.',
            icon='🏗️',
            progress=45,
            tech_stack='Django · React · PostgreSQL',
            is_active=True,
        )
        Project.objects.create(
            name='Portfolio Website',
            description='Personal portfolio to showcase projects and blog posts.',
            icon='🌐',
            progress=70,
            tech_stack='Next.js · Tailwind CSS',
            is_active=False,
        )
        self.stdout.write('  ✔  Projects')

        # ── Study sessions (last 7 days) ──────────────
        StudySession.objects.all().delete()
        week_hours = [3.0, 5.5, 4.0, 6.0, 7.0, 4.5, 4.583]  # Mon→Sun
        for i, h in enumerate(week_hours):
            d = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=i)
            if d <= today:
                StudySession.objects.create(date=d, hours=h)
        self.stdout.write('  ✔  Study sessions')

        # ── Recent activity ───────────────────────────
        Activity.objects.all().delete()
        now = timezone.now()
        activities = [
            ('Completed Python – Functions',      0,    '✅', '#22c55e'),
            ('Solved 5 problems on LeetCode',    60,    '💻', '#60a5fa'),
            ('Updated project: User API',       240,    '🔧', '#a78bfa'),
            ('Read 20 pages of Clean Code',    1440,    '📚', '#fb923c'),
        ]
        for desc, mins_ago, icon, color in activities:
            Activity.objects.create(
                description=desc,
                timestamp=now - datetime.timedelta(minutes=mins_ago),
                icon=icon,
                color=color,
            )
        self.stdout.write('  ✔  Activities')

        # ── Quick links ───────────────────────────────
        QuickLink.objects.all().delete()
        links = [
            ('GitHub',        'https://github.com',          '🐙', '#24292e', 1),
            ('LeetCode',      'https://leetcode.com',        '🟠', '#1a1a1a', 2),
            ('HackerRank',    'https://hackerrank.com',      '🟢', '#1a1a1a', 3),
            ('Notion',        'https://notion.so',           '📝', '#191919', 4),
            ('YouTube',       'https://youtube.com',         '▶️', '#ff0000', 5),
            ('Documentation', 'https://docs.djangoproject.com', '📖', '#0c3547', 6),
            ('Resume',        'https://resume.io',           '📄', '#1e3a5f', 7),
            ('Portfolio',     'https://github.com',          '🌐', '#0f3460', 8),
        ]
        for name, url, icon, bg, order in links:
            QuickLink.objects.create(name=name, url=url, icon=icon, bg_color=bg, order=order)
        self.stdout.write('  ✔  Quick links')

        # ── Quotes ────────────────────────────────────
        Quote.objects.all().delete()
        quotes = [
            ('The harder you work for something, the greater you\'ll feel when you achieve it.', ''),
            ('Code is like humor. When you have to explain it, it\'s bad.', 'Cory House'),
            ('First, solve the problem. Then, write the code.', 'John Johnson'),
            ('Discipline today, Success tomorrow.', 'Your Future Self'),
            ('It always seems impossible until it is done.', 'Nelson Mandela'),
        ]
        for text, author in quotes:
            Quote.objects.create(text=text, author=author, is_active=True)
        self.stdout.write('  ✔  Quotes')

        self.stdout.write(self.style.SUCCESS('\n✅  Seed complete! Visit http://127.0.0.1:8000/'))
