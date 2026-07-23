"""
URL root của dự án webnoibo.
"""

from django.urls import path, include

urlpatterns = [
    # Auth: /, /login/, /logout/, /register/, /api/send-otp/, /auth/invite/
    path('', include('apps.authentication.urls')),
    # Dashboard: /dashboard/
    path('', include('apps.dashboard.urls')),
    # Projects: /projects/, /projects/<id>/, ...
    path('projects/', include('apps.projects.urls')),
    # Tasks: /tasks/, /tasks/<id>/, ...
    path('tasks/', include('apps.tasks.urls')),
    # Members: /members/, /members/<id>/
    path('members/', include('apps.members.urls')),
    # Reports: /reports/, /reports/export/tasks/
    path('reports/', include('apps.reports.urls')),
]
