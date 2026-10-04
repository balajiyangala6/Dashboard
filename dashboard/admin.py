from django.contrib import admin
from .models import Profile, RoadmapTopic, Task, Project, StudySession, Activity, QuickLink, Quote


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'streak_days', 'focus_mode', 'daily_target_hours')


@admin.register(RoadmapTopic)
class RoadmapTopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'progress', 'order')
    ordering = ('order',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'scheduled_time', 'is_completed', 'priority')
    list_filter = ('date', 'is_completed', 'priority')
    ordering = ('-date', 'scheduled_time')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'progress', 'is_active', 'tech_stack')
    list_filter = ('is_active',)


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'hours')
    ordering = ('-date',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('description', 'timestamp', 'icon')
    ordering = ('-timestamp',)


@admin.register(QuickLink)
class QuickLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'order')
    ordering = ('order',)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'is_active')
    list_filter = ('is_active',)
