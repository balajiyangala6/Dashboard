"""Replace MongoDB collections with the sample dashboard data."""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.mongodb import replace_records


class Command(BaseCommand):
    help = 'Replace MongoDB dashboard collections with sample data'

    def handle(self, *args, **options):
        today = timezone.localdate()
        now = timezone.now()

        replace_records('profiles', [{
            '_id': 'main',
            'name': 'Balaji',
            'tagline': 'Keep going!',
            'streak_days': 12,
            'focus_mode': False,
            'daily_target_hours': 8.0,
        }])
        replace_records('roadmap_topics', [
            {'name': name, 'progress': progress, 'order': order}
            for name, progress, order in [
                ('Python Basics', 100, 1),
                ('Data Structures', 85, 2),
                ('SQL', 70, 3),
                ('ReactJS', 45, 4),
                ('System Design', 30, 5),
                ('Projects', 60, 6),
            ]
        ])

        task_data = [
            ('Python – Functions', '09:00', True, '#22c55e'),
            ('SQL – Joins', '10:30', True, '#60a5fa'),
            ('Solve 5 Problems', '12:00', False, '#a78bfa'),
            ('Build API – User Module', '14:00', False, '#fb923c'),
            ('Read Book – Clean Code', '16:00', False, '#f472b6'),
        ]
        replace_records('tasks', [
            {
                'title': title,
                'scheduled_time': scheduled_time,
                'is_completed': completed,
                'date': today.isoformat(),
                'priority': 'medium',
                'color': color,
            }
            for title, scheduled_time, completed, color in task_data
        ])
        replace_records('projects', [
            {
                'name': 'Rental Marketplace',
                'description': 'Connecting farmers and machinery owners. Build. Test. Grow.',
                'icon': '🏗️',
                'progress': 45,
                'tech_stack': 'Django · React · MongoDB',
                'is_active': True,
            },
            {
                'name': 'Portfolio Website',
                'description': 'Personal portfolio to showcase projects and blog posts.',
                'icon': '🌐',
                'progress': 70,
                'tech_stack': 'Next.js · Tailwind CSS',
                'is_active': False,
            },
        ])

        week_hours = [3.0, 5.5, 4.0, 6.0, 7.0, 4.5, 4.583]
        week_start = today - datetime.timedelta(days=today.weekday())
        replace_records('study_sessions', [
            {
                'date': (week_start + datetime.timedelta(days=day)).isoformat(),
                'hours': hours,
            }
            for day, hours in enumerate(week_hours)
            if week_start + datetime.timedelta(days=day) <= today
        ])

        activity_data = [
            ('Completed Python – Functions', 0, '✅', '#22c55e'),
            ('Solved 5 problems on LeetCode', 60, '💻', '#60a5fa'),
            ('Updated project: User API', 240, '🔧', '#a78bfa'),
            ('Read 20 pages of Clean Code', 1440, '📚', '#fb923c'),
        ]
        replace_records('activities', [
            {
                'description': description,
                'timestamp': now - datetime.timedelta(minutes=minutes_ago),
                'icon': icon,
                'color': color,
            }
            for description, minutes_ago, icon, color in activity_data
        ])

        link_data = [
            ('GitHub', 'https://github.com', '🐙', '#24292e'),
            ('LeetCode', 'https://leetcode.com', '🟠', '#1a1a1a'),
            ('HackerRank', 'https://hackerrank.com', '🟢', '#1a1a1a'),
            ('Notion', 'https://notion.so', '📝', '#191919'),
            ('YouTube', 'https://youtube.com', '▶️', '#ff0000'),
            ('Documentation', 'https://docs.djangoproject.com', '📖', '#0c3547'),
            ('Resume', 'https://resume.io', '📄', '#1e3a5f'),
            ('Portfolio', 'https://github.com', '🌐', '#0f3460'),
        ]
        replace_records('quick_links', [
            {
                'name': name,
                'url': url,
                'icon': icon,
                'bg_color': background,
                'order': order,
            }
            for order, (name, url, icon, background) in enumerate(link_data, 1)
        ])

        quote_data = [
            ('The harder you work for something, the greater you’ll feel when you achieve it.', ''),
            ('Code is like humor. When you have to explain it, it’s bad.', 'Cory House'),
            ('First, solve the problem. Then, write the code.', 'John Johnson'),
            ('Discipline today, Success tomorrow.', 'Your Future Self'),
            ('It always seems impossible until it is done.', 'Nelson Mandela'),
        ]
        replace_records('quotes', [
            {'text': text, 'author': author, 'is_active': True}
            for text, author in quote_data
        ])

        self.stdout.write(self.style.SUCCESS('MongoDB dashboard data seeded.'))
