from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('admin/', views.admin_console, name='admin'),
    path('', views.dashboard, name='dashboard'),
    path('roadmap/', views.roadmap, name='roadmap'),
    path('tasks/', views.tasks, name='tasks'),
    path('projects/', views.projects, name='projects'),
    path('progress/', views.progress, name='progress'),
    path('calendar/', views.calendar, name='calendar'),
    path('api/toggle-task/<str:task_id>/', views.toggle_task, name='toggle_task'),
    path('api/toggle-focus/', views.toggle_focus_mode, name='toggle_focus'),
]
