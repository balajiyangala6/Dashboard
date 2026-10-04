from django.db import models
from django.utils import timezone


class Profile(models.Model):
    name = models.CharField(max_length=100, default="Balaji")
    tagline = models.CharField(max_length=200, default="Keep going!")
    streak_days = models.PositiveIntegerField(default=0)
    focus_mode = models.BooleanField(default=False)
    daily_target_hours = models.FloatField(default=8.0)

    def __str__(self):
        return self.name


class RoadmapTopic(models.Model):
    name = models.CharField(max_length=100)
    progress = models.PositiveIntegerField(default=0)  # 0-100
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.progress}%)"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    title = models.CharField(max_length=200)
    scheduled_time = models.TimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    date = models.DateField(default=timezone.now)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    color = models.CharField(max_length=20, default='#a78bfa')  # purple accent

    class Meta:
        ordering = ['scheduled_time', 'id']

    def __str__(self):
        return self.title


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='🚀')
    progress = models.PositiveIntegerField(default=0)  # 0-100
    tech_stack = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StudySession(models.Model):
    date = models.DateField(default=timezone.now)
    hours = models.FloatField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ['date']

    def __str__(self):
        return f"{self.date} — {self.hours}h"


class Activity(models.Model):
    description = models.CharField(max_length=300)
    timestamp = models.DateTimeField(default=timezone.now)
    icon = models.CharField(max_length=10, default='✅')
    color = models.CharField(max_length=20, default='#a78bfa')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.description


class QuickLink(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon = models.CharField(max_length=10, default='🔗')
    bg_color = models.CharField(max_length=20, default='#1e1e2e')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Quote(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:60]
