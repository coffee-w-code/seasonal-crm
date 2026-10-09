from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from datetime import timedelta
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.accounts.models import UserSession


User = get_user_model()


class SessionManagementAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sessiontest",
            password="TestPassword123!",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def create_tracked_session(
        self,
        session_key,
        user=None,
        revoked_at=None,
    ):
        return UserSession.objects.create(
            user=user or self.user,
            session_key=session_key,
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            revoked_at=revoked_at,
        )

    def test_list_sessions_returns_active_sessions(self):
        session = self.create_tracked_session(
            session_key="test-session-key-1",
        )

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertEqual(
            len(response.data["sessions"]),
            1,
        )

        returned_session = response.data["sessions"][0]

        self.assertEqual(
            returned_session["id"],
            session.id,
        )

        self.assertEqual(
            returned_session["ip_address"],
            "127.0.0.1",
        )

        self.assertEqual(
            returned_session["user_agent"],
            "Test Browser",
        )

        self.assertIn(
            "created_at",
            returned_session,
        )

        self.assertIn(
            "last_active_at",
            returned_session,
        )

        self.assertIn(
            "is_current",
            returned_session,
        )

        # The real Django session key must never
        # be exposed through the API.
        self.assertNotIn(
            "session_key",
            returned_session,
        )

    def test_list_sessions_returns_active_and_signed_out_sessions(self):
        active_session = self.create_tracked_session(
            session_key="active-session-key",
        )

        signed_out_session = self.create_tracked_session(
            session_key="signed-out-session-key",
            revoked_at=timezone.now(),
        )

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertEqual(
            len(response.data["sessions"]),
            2,
        )

        returned_sessions = response.data["sessions"]

        returned_by_id = {
            session["id"]: session
            for session in returned_sessions
        }

        active_data = returned_by_id[active_session.id]
        signed_out_data = returned_by_id[signed_out_session.id]

        self.assertIsNone(
            active_data["sign_out_at"],
        )

        self.assertIsNotNone(
            signed_out_data["sign_out_at"],
        )

        self.assertNotIn(
            "session_key",
            active_data,
        )

        self.assertNotIn(
            "session_key",
            signed_out_data,
        )

    def test_revoke_other_sessions_revokes_all_other_sessions(self):
        current_session_key = (
            self.client.session.session_key
        )

        current_session = self.create_tracked_session(
            session_key=current_session_key,
        )

        other_session_1 = self.create_tracked_session(
            session_key="other-session-key-1",
        )

        other_session_2 = self.create_tracked_session(
            session_key="other-session-key-2",
        )

        response = self.client.post(
            "/api/auth/sessions/revoke-others/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertEqual(
            response.data["revoked_count"],
            2,
        )

        current_session.refresh_from_db()
        other_session_1.refresh_from_db()
        other_session_2.refresh_from_db()

        self.assertIsNone(
            current_session.revoked_at,
        )

        self.assertIsNotNone(
            other_session_1.revoked_at,
        )

        self.assertIsNotNone(
            other_session_2.revoked_at,
        )


    def test_revoke_other_sessions_deletes_other_django_sessions(self):
        current_session_key = (
            self.client.session.session_key
        )

        current_session = self.create_tracked_session(
            session_key=current_session_key,
        )

        django_session_1 = Session.objects.create(
            session_key="django-other-session-1",
            session_data="test-data",
            expire_date=timezone.now(),
        )

        django_session_2 = Session.objects.create(
            session_key="django-other-session-2",
            session_data="test-data",
            expire_date=timezone.now(),
        )

        other_session_1 = self.create_tracked_session(
            session_key=django_session_1.session_key,
        )

        other_session_2 = self.create_tracked_session(
            session_key=django_session_2.session_key,
        )

        response = self.client.post(
            "/api/auth/sessions/revoke-others/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Session.objects.filter(
                session_key=django_session_1.session_key,
            ).exists()
        )

        self.assertFalse(
            Session.objects.filter(
                session_key=django_session_2.session_key,
            ).exists()
        )

        current_session.refresh_from_db()

        self.assertIsNone(
            current_session.revoked_at,
        )

        other_session_1.refresh_from_db()
        other_session_2.refresh_from_db()

        self.assertIsNotNone(
            other_session_1.revoked_at,
        )

        self.assertIsNotNone(
            other_session_2.revoked_at,
        )


    def test_revoke_other_sessions_when_no_other_sessions_exist(self):
        current_session_key = (
            self.client.session.session_key
        )

        current_session = self.create_tracked_session(
            session_key=current_session_key,
        )

        response = self.client.post(
            "/api/auth/sessions/revoke-others/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["revoked_count"],
            0,
        )

        current_session.refresh_from_db()

        self.assertIsNone(
            current_session.revoked_at,
        )


    def test_unauthenticated_user_cannot_revoke_other_sessions(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/auth/sessions/revoke-others/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_revoke_session_revokes_other_session(self):
        session = self.create_tracked_session(
            session_key="other-session-key",
        )

        response = self.client.delete(
            f"/api/auth/sessions/{session.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        session.refresh_from_db()

        self.assertIsNotNone(
            session.revoked_at,
        )

    def test_revoke_session_deletes_django_session(self):
        django_session = Session.objects.create(
            session_key="django-session-key",
            session_data="test-data",
            expire_date=timezone.now(),
        )

        session = self.create_tracked_session(
            session_key=django_session.session_key,
        )

        response = self.client.delete(
            f"/api/auth/sessions/{session.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Session.objects.filter(
                session_key=django_session.session_key,
            ).exists()
        )

    def test_cannot_revoke_current_session(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
        )

        response = self.client.delete(
            f"/api/auth/sessions/{session.id}/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "CURRENT_SESSION",
        )

        session.refresh_from_db()

        self.assertIsNone(
            session.revoked_at,
        )

    def test_revoke_nonexistent_session_returns_not_found(self):
        response = self.client.delete(
            "/api/auth/sessions/999999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.data["code"],
            "SESSION_NOT_FOUND",
        )

    def test_user_cannot_revoke_another_users_session(self):
        other_user = User.objects.create_user(
            username="other_session_user",
            password="TestPassword123!",
        )

        other_session = self.create_tracked_session(
            session_key="other-users-session-key",
            user=other_user,
        )

        response = self.client.delete(
            f"/api/auth/sessions/{other_session.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.data["code"],
            "SESSION_NOT_FOUND",
        )

        other_session.refresh_from_db()

        self.assertIsNone(
            other_session.revoked_at,
        )

    def test_unauthenticated_user_cannot_list_sessions(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_unauthenticated_user_cannot_revoke_session(self):
        session = self.create_tracked_session(
            session_key="protected-session-key",
        )

        self.client.force_authenticate(
            user=None
        )

        response = self.client.delete(
            f"/api/auth/sessions/{session.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        session.refresh_from_db()

        self.assertIsNone(
            session.revoked_at,
        )

    def test_session_activity_updates_when_interval_has_passed(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
        )

        old_time = timezone.now() - timedelta(
            minutes=10,
        )

        UserSession.objects.filter(
            id=session.id,
        ).update(
            last_active_at=old_time,
        )

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session.refresh_from_db()

        self.assertGreater(
            session.last_active_at,
            old_time,
        )


    def test_session_activity_does_not_update_within_interval(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
        )

        recent_time = timezone.now() - timedelta(
            minutes=1,
        )

        UserSession.objects.filter(
            id=session.id,
        ).update(
            last_active_at=recent_time,
        )

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session.refresh_from_db()

        self.assertEqual(
            session.last_active_at,
            recent_time,
        )

    def test_session_activity_does_not_update_revoked_session(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
            revoked_at=timezone.now(),
        )

        old_time = session.last_active_at

        response = self.client.get(
            "/api/auth/sessions/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session.refresh_from_db()

        self.assertEqual(
            session.last_active_at,
            old_time,
        )

    def test_logout_revokes_current_tracked_session(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
        )

        response = self.client.post(
            "/api/auth/logout/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session.refresh_from_db()

        self.assertIsNotNone(
            session.revoked_at,
        )


    def test_logout_destroys_current_django_session(self):
        current_session_key = (
            self.client.session.session_key
        )

        session = self.create_tracked_session(
            session_key=current_session_key,
        )

        response = self.client.post(
            "/api/auth/logout/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Session.objects.filter(
                session_key=current_session_key,
            ).exists()
        )

        session.refresh_from_db()

        self.assertIsNotNone(
            session.revoked_at,
        )