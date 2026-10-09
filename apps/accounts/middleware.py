from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import UserSession


class UserSessionActivityMiddleware:
    """
    Update the last activity time of the authenticated user's
    tracked session.

    To avoid a database write on every request, the timestamp is
    only updated when the previous activity was more than 5 minutes ago.
    """

    ACTIVITY_UPDATE_INTERVAL = timedelta(minutes=5)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.user.is_authenticated
            and request.session.session_key
        ):
            self._update_session_activity(request)

        return response

    def _update_session_activity(self, request):
        try:
            session = UserSession.objects.get(
                user=request.user,
                session_key=request.session.session_key,
                revoked_at__isnull=True,
            )
        except UserSession.DoesNotExist:
            return

        now = timezone.now()

        if (
            now - session.last_active_at
            >= self.ACTIVITY_UPDATE_INTERVAL
        ):
            session.last_active_at = now

            session.save(
                update_fields=["last_active_at"],
            )