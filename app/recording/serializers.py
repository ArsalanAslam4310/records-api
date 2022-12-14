"""
Serializers for the recording APIs
"""
from rest_framework import serializers

from core.models import Recording


class RecordingSerializer(serializers.ModelSerializer):
    """Serializer for recordings."""

    class Meta:
        model = Recording
        fields = ['id', 'title', 'duration_minutes', 'date_of_recording',
                  'category', 'current_status', 'recording_url', 'transcription_url']
        read_only_fields = ['id']


class RecordingDetailSerializer(RecordingSerializer):
    """Serializer for recording detail view."""

    class Meta(RecordingSerializer.Meta):
        fields = RecordingSerializer.Meta.fields
