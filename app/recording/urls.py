"""
URL mappings for the recording app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from recording import views

router = DefaultRouter()
router.register('recordings', views.RecordingViewSet)

app_name = 'recording'

urlpatterns = [
    path('', include(router.urls)),
]
