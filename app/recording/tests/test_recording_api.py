"""
Tests for recording API.
"""
from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recording

from recording.serializers import (
    RecordingSerializer,
    RecordingDetailSerializer,
)

RECORDINGS_URL = reverse('recording:recording-list')


def detail_url(recording_id):
    """Create and return a recording detail URL."""
    return reverse('recording:recording-detail', args=[recording_id])


def create_recording(user, **params):
    """Create and return a sample recording."""
    defaults = {
        'title': 'Sample Recording name',
        'duration_minutes': Decimal(5),
        'date_of_recording': date.today(),
        'category': 'Art',
        'current_status': 'Not Transcribed',
        'recording_url': 'https://abcd.com/',
        'transcription_url': 'https://abcd.com',
    }

    defaults.update(params)

    recording = Recording.objects.create(user=user, **defaults)

    return recording


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecordingAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECORDINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecordingAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recordings(self):
        """Test retrieving a list of recordings."""
        create_recording(user=self.user)
        create_recording(user=self.user)

        res = self.client.get(RECORDINGS_URL)

        recordings = Recording.objects.all().order_by('-id')
        serializer = RecordingSerializer(recordings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recording_list_limited_to_user(self):
        """Test list of recording is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='password123'
        )
        create_recording(user=other_user)
        create_recording(user=self.user)

        res = self.client.get(RECORDINGS_URL)

        recordings = Recording.objects.filter(user=self.user)
        serializer = RecordingSerializer(recordings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recording_detail(self):
        """Test get recording detail."""
        recording = create_recording(user=self.user)

        url = detail_url(recording.id)
        res = self.client.get(url)

        serializer = RecordingDetailSerializer(recording)
        self.assertEqual(res.data, serializer.data)

    def test_create_recording(self):
        """Test creating a recording."""
        payload = {
            'title': 'Sample Recording name',
            'duration_minutes': Decimal(5),
            'date_of_recording': date.today(),
            'category': 'Art',
            'current_status': 'Not Transcribed',
            'recording_url': 'https://abcd.com/',
            'transcription_url': 'https://abcd.com',
        }
        res = self.client.post(RECORDINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recording = Recording.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recording, k), v)
        self.assertEqual(recording.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recording."""
        original_url = 'https://example.com/recording.mp3'
        recording = create_recording(
            user=self.user,
            title='Sample recording title',
            recording_url=original_url
        )
        payload = {'title': 'New Recording Title'}
        url = detail_url(recording.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recording.refresh_from_db()
        self.assertEqual(recording.title, payload['title'])
        self.assertEqual(recording.recording_url, original_url)
        self.assertEqual(recording.user, self.user)

    def test_full_update(self):
        """Test full update of recording."""
        recording = create_recording(
            user=self.user,
            title='Sample recording title',
            duration_minutes=Decimal(55),
            date_of_recording=date(2021, 12, 22),
            category='Philosophy',
            current_status='Transcribed',
            recording_url='https://abcdefg.com/',
            transcription_url='https://abcdefg.com/',
        )

        payload = {
            'title': 'Sample Recording name',
            'duration_minutes': Decimal(5),
            'date_of_recording': date.today(),
            'category': 'Art',
            'current_status': 'Not Transcribed',
            'recording_url': 'https://abcd.com/',
            'transcription_url': 'https://abcd.com',
        }
        url = detail_url(recording.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recording.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recording, k), v)
        self.assertEqual(recording.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recording user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recording = create_recording(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recording.id)
        self.client.patch(url, payload)

        recording.refresh_from_db()
        self.assertEqual(recording.user, self.user)

    def test_delete_recording(self):
        """Test deleting a recording is successful."""
        recording = create_recording(user=self.user)

        url = detail_url(recording.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recording.objects.filter(id=recording.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test trying to delete another user's recording gives an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recording = create_recording(user=new_user)

        url = detail_url(recording.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recording.objects.filter(id=recording.id).exists())
