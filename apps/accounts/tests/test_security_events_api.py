from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import SecurityEvent, UserSession


User = get_user_model()


class SecurityEventsAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="security_test_user",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other_security_user",
            password="TestPassword123!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def get_events(self, response):
        """
        Return the event list from the API response.
        """

        self.assertEqual(
            response.status_code,
            200,
        )

        if isinstance(response.data, list):
            return response.data

        return response.data["events"]

    def test_security_events_endpoint_returns_events(self):
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.LOGIN,
            ip_address="127.0.0.1",
            user_agent="Test Browser",
        )

        response = self.client.get(
            "/api/auth/security-events/",
        )

        events = self.get_events(response)

        self.assertEqual(
            len(events),
            1,
        )

        self.assertEqual(
            events[0]["event_type"],
            "LOGIN",
        )

    def test_security_events_only_return_current_users_events(self):
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.LOGIN,
        )

        SecurityEvent.objects.create(
            user=self.other_user,
            event_type=SecurityEvent.EventType.LOGIN,
        )

        response = self.client.get(
            "/api/auth/security-events/",
        )

        events = self.get_events(response)

        self.assertEqual(
            len(events),
            1,
        )

        self.assertEqual(
            events[0]["event_type"],
            "LOGIN",
        )

    def test_security_events_are_newest_first(self):
        older_event = SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.LOGIN,
        )

        newer_event = SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.PASSWORD_CHANGED,
        )

        SecurityEvent.objects.filter(
            id=older_event.id,
        ).update(
            created_at=timezone.now() - timezone.timedelta(
                minutes=10,
            ),
        )

        SecurityEvent.objects.filter(
            id=newer_event.id,
        ).update(
            created_at=timezone.now(),
        )

        response = self.client.get(
            "/api/auth/security-events/",
        )

        events = self.get_events(response)

        self.assertEqual(
            events[0]["id"],
            newer_event.id,
        )

        self.assertEqual(
            events[1]["id"],
            older_event.id,
        )

    def test_security_event_does_not_expose_session_key(self):
        django_session = self.client.session
        session_key = django_session.session_key

        tracked_session = UserSession.objects.create(
            user=self.user,
            session_key=session_key,
        )

        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.LOGIN,
            session=tracked_session,
        )

        response = self.client.get(
            "/api/auth/security-events/",
        )

        events = self.get_events(response)

        event_data = events[0]

        self.assertIn(
            "session_id",
            event_data,
        )

        self.assertNotIn(
            "session_key",
            event_data,
        )

        self.assertNotIn(
            session_key,
            str(event_data),
        )

    def test_unauthenticated_user_cannot_access_security_events(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            "/api/auth/security-events/",
        )

        self.assertIn(
            response.status_code,
            [401, 403],
        )