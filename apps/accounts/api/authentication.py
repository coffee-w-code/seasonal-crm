import json

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from django.utils import timezone

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.accounts.models import (
    SecurityEvent,
    UserProfile,
    UserSession,
    UserTwoFactorAuth,
    TwoFactorRecoveryCode,
)
from apps.accounts.security.recovery_codes import (
    generate_recovery_codes,
    get_recovery_code_status,
    store_recovery_codes,
)
from apps.accounts.security.totp import (
    generate_provisioning_uri,
    generate_totp_secret,
)
from apps.accounts.security.two_factor import (
    encrypt_totp_secret,
)
from apps.accounts.security.verification import (
    verify_totp_for_user,
    verify_recovery_code_for_user,
    verify_totp_setup_for_user,
    verify_totp_authenticator_change_for_user,
)
from PIL import Image


PENDING_2FA_USER_SESSION_KEY = "pending_2fa_user_id"
PENDING_2FA_STARTED_SESSION_KEY = "pending_2fa_started_at"

PENDING_2FA_EXPIRATION_SECONDS = 300

def _clear_pending_2fa(request):
    request.session.pop(PENDING_2FA_USER_SESSION_KEY, None)
    request.session.pop(PENDING_2FA_STARTED_SESSION_KEY, None)
    request.session.modified = True


def _get_pending_2fa_auth(request):
    pending_user_id = request.session.get(
        PENDING_2FA_USER_SESSION_KEY
    )
    pending_started_at = request.session.get(
        PENDING_2FA_STARTED_SESSION_KEY
    )

    if not pending_user_id or pending_started_at is None:
        return None, "TWO_FACTOR_LOGIN_REQUIRED"

    try:
        pending_started_at = float(pending_started_at)
    except (TypeError, ValueError):
        _clear_pending_2fa(request)
        return None, "TWO_FACTOR_LOGIN_EXPIRED"

    elapsed_seconds = (
        timezone.now().timestamp() - pending_started_at
    )

    if elapsed_seconds < 0 or elapsed_seconds > PENDING_2FA_EXPIRATION_SECONDS:
        _clear_pending_2fa(request)
        return None, "TWO_FACTOR_LOGIN_EXPIRED"

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .select_related("user")
        .filter(
            user_id=pending_user_id,
            is_enabled=True,
        )
        .first()
    )

    if two_factor_auth is None:
        _clear_pending_2fa(request)
        return None, "TWO_FACTOR_LOGIN_EXPIRED"

    return two_factor_auth, None


def _user_data(user):
    """
    Return the authenticated user's basic profile information.
    """

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }

def _profile_data(user):
    """
    Return the authenticated user's complete profile information,
    including avatar information.
    """

    profile, _ = UserProfile.objects.get_or_create(
        user=user
    )

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": profile.phone_number,
        "avatar": (
            profile.avatar.url
            if profile.avatar
            else None
        ),
        "default_landing_page": profile.default_landing_page,
    }

def _get_client_ip(request):
    """
    Return the client's IP address.

    For now, use the direct remote address. We will handle
    trusted proxy configuration separately when deploying.
    """
    return request.META.get("REMOTE_ADDR")


def _session_data(session, current_session_key):
    return {
        "id": session.id,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
        "created_at": session.created_at,
        "last_active_at": session.last_active_at,
        "sign_out_at": session.revoked_at,
        "is_current": session.session_key == current_session_key,
    }

def _record_security_event(
    request,
    user,
    event_type,
    session=None,
):
    """
    Record a security-sensitive account event.
    """

    SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        session=session,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            "",
        ),
    )

@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_view(request):
    """
    Ensure the browser receives a CSRF cookie.
    """

    return JsonResponse(
        {
            "status": "success",
            "message": "CSRF cookie set.",
        }
    )


@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_JSON",
                "message": "Invalid JSON request body.",
            },
            status=400,
        )

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_CREDENTIALS",
                "message": "Username and password are required.",
            },
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid username or password.",
            },
            status=401,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=user,
            is_enabled=True,
        )
        .first()
    )

    # --------------------------------------------------
    # 2FA REQUIRED
    # --------------------------------------------------

    if two_factor_auth:
        request.session[
            PENDING_2FA_USER_SESSION_KEY
        ] = user.id

        request.session[
            PENDING_2FA_STARTED_SESSION_KEY
        ] = timezone.now().timestamp()

        request.session.modified = True

        return JsonResponse(
            {
                "status": "2fa_required",
                "code": "TWO_FACTOR_REQUIRED",
                "message": "Two-factor authentication is required.",
            },
            status=200,
        )

    # --------------------------------------------------
    # NORMAL LOGIN — 2FA NOT ENABLED
    # --------------------------------------------------

    login(request, user)

    session_key = request.session.session_key

    tracked_session, _ = UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            "user": user,
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
            "revoked_at": None,
        },
    )

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.LOGIN,
        tracked_session,
    )

    return JsonResponse(
        {
            "status": "success",
            "message": "Login successful.",
            "user": _user_data(user),
        }
    )


@require_http_methods(["POST"])
def two_factor_login_verify_view(request):
    two_factor_auth, error_code = _get_pending_2fa_auth(request)

    if error_code:
        if error_code == "TWO_FACTOR_LOGIN_REQUIRED":
            message = "Two-factor login verification is required."
        else:
            message = "The two-factor login session has expired."

        return JsonResponse(
            {
                "status": "error",
                "code": error_code,
                "message": message,
            },
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_JSON",
                "message": "Invalid JSON request body.",
            },
            status=400,
        )

    method = data.get("method")
    code = data.get("code")

    if method not in {"TOTP", "RECOVERY_CODE"}:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_2FA_METHOD",
                "message": "A valid two-factor verification method is required.",
            },
            status=400,
        )

    if not isinstance(code, str) or not code.strip():
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_2FA_CODE",
                "message": "A two-factor verification code is required.",
            },
            status=400,
        )

    if method == "TOTP":
        verification_result = verify_totp_for_user(
            two_factor_auth,
            code,
        )
    else:
        verification_result = verify_recovery_code_for_user(
            two_factor_auth,
            code,
        )

    if not verification_result["success"]:
        reason = verification_result["reason"]

        error_messages = {
            "INVALID_CODE": "The authenticator code is invalid.",
            "CODE_ALREADY_USED": "This authenticator code has already been used.",
            "INVALID_RECOVERY_CODE": "The recovery code is invalid.",
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. Please try again later."
            ),
            "CONFIGURATION_ERROR": (
                "Two-factor authentication is temporarily unavailable."
            ),
        }

        return JsonResponse(
            {
                "status": "error",
                "code": reason,
                "message": error_messages.get(
                    reason,
                    "Two-factor verification failed.",
                ),
            },
            status=400,
        )

    user = two_factor_auth.user

    # Remove the temporary 2FA challenge before
    # creating the authenticated session.
    _clear_pending_2fa(request)

    login(request, user)

    session_key = request.session.session_key

    tracked_session, _ = UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            "user": user,
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
            "revoked_at": None,
        },
    )

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.LOGIN,
        tracked_session,
    )

    return JsonResponse(
        {
            "status": "success",
            "message": "Login successful.",
            "user": _user_data(user),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Log out the current user and revoke the tracked session.
    """

    current_session_key = request.session.session_key

    tracked_session = None

    if current_session_key:
        tracked_session = UserSession.objects.filter(
            user=request.user,
            session_key=current_session_key,
            revoked_at__isnull=True,
        ).first()

        if tracked_session:
            tracked_session.revoked_at = timezone.now()
            tracked_session.save(
                update_fields=["revoked_at"],
            )

            _record_security_event(
                request,
                request.user,
                SecurityEvent.EventType.LOGOUT,
                tracked_session,
            )

    logout(request)

    return Response(
        {
            "status": "success",
            "message": "Logged out successfully.",
        },
        status=status.HTTP_200_OK,
    )


@require_http_methods(["GET"])
def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "code": "NOT_AUTHENTICATED",
                "message": "User is not authenticated.",
            },
            status=401,
        )

    return JsonResponse(
        {
            "status": "success",
            "user": _user_data(request.user),
        }
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sessions_view(request):
    """
    Return the user's session history, including
    active and signed-out sessions.
    """

    current_session_key = request.session.session_key

    sessions = (
        UserSession.objects
        .filter(
            user=request.user,
        )
        .order_by("-created_at")
    )

    return Response(
        {
            "status": "success",
            "sessions": [
                _session_data(
                    session,
                    current_session_key,
                )
                for session in sessions
            ],
        },
        status=status.HTTP_200_OK,
    )

def _security_event_data(event):
    return {
        "id": event.id,
        "event_type": event.event_type,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "created_at": event.created_at,
        "session_id": event.session_id,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def security_events_view(request):
    """
    Return the authenticated user's security activity.
    """

    events = (
        SecurityEvent.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return Response(
        {
            "status": "success",
            "events": [
                _security_event_data(event)
                for event in events
            ],
        },
        status=status.HTTP_200_OK,
    )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_session_view(request, session_id):
    """
    Revoke one tracked session belonging to the authenticated user.
    """

    current_session_key = request.session.session_key

    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user,
            revoked_at__isnull=True,
        )
    except UserSession.DoesNotExist:
        return Response(
            {
                "status": "error",
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if session.session_key == current_session_key:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_SESSION",
                "message": "You cannot revoke your current session here.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.revoked_at = timezone.now()
    session.save(
        update_fields=["revoked_at"],
    )

    _record_security_event(
        request,
        request.user,
        SecurityEvent.EventType.SESSION_REVOKED,
        session,
    )

    # Invalidate the actual Django session.

    from django.contrib.sessions.models import Session

    Session.objects.filter(
        session_key=session.session_key,
    ).delete()

    return Response(
        {
            "status": "success",
            "message": "Session revoked successfully.",
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_other_sessions_view(request):
    """
    Revoke all tracked sessions except the current session.
    """

    current_session_key = request.session.session_key

    sessions = (
        UserSession.objects
        .filter(
            user=request.user,
            revoked_at__isnull=True,
        )
        .exclude(
            session_key=current_session_key,
        )
    )

    sessions_to_revoke = list(sessions)

    session_keys = [
        session.session_key
        for session in sessions_to_revoke
    ]

    revoked_count = len(sessions_to_revoke)

    revoked_at = timezone.now()

    sessions.update(
        revoked_at=revoked_at,
    )

    for session in sessions_to_revoke:
        _record_security_event(
            request,
            request.user,
            SecurityEvent.EventType.SESSION_REVOKED,
            session,
        )

    from django.contrib.sessions.models import Session

    Session.objects.filter(
        session_key__in=session_keys,
    ).delete()

    return Response(
        {
            "status": "success",
            "message": "All other sessions have been revoked.",
            "revoked_count": revoked_count,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Read or update the authenticated user's personal profile.

    Username is intentionally not editable here.
    """

    user = request.user

    # -----------------------------------------
    # GET PROFILE
    # -----------------------------------------
    if request.method == "GET":
        return Response(
            {
                "status": "success",
                "user": _profile_data(user),
            },
            status=status.HTTP_200_OK,
        )

    # -----------------------------------------
    # UPDATE PROFILE
    # -----------------------------------------
    data = request.data

    # Only allow profile fields.
    first_name = data.get(
        "first_name",
        user.first_name,
    )

    last_name = data.get(
        "last_name",
        user.last_name,
    )

    email = data.get(
        "email",
        user.email,
    )

    phone_number = data.get(
        "phone_number",
        UserProfile.objects.get_or_create(
            user=user
        )[0].phone_number,
    )

    if not isinstance(first_name, str):
        return Response(
            {
                "status": "error",
                "code": "INVALID_FIRST_NAME",
                "message": "First name must be text.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(last_name, str):
        return Response(
            {
                "status": "error",
                "code": "INVALID_LAST_NAME",
                "message": "Last name must be text.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(email, str):
        return Response(
            {
                "status": "error",
                "code": "INVALID_EMAIL",
                "message": "Email must be text.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip()

    # -----------------------------------------
    # Validate email
    # -----------------------------------------
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_EMAIL",
                    "message": "Enter a valid email address.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # -----------------------------------------
    # Validate phone number
    # -----------------------------------------
    if not isinstance(phone_number, str):
        return Response(
            {
                "status": "error",
                "code": "INVALID_PHONE_NUMBER",
                "message": "Phone number must be text.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    phone_number = phone_number.strip()

    if len(phone_number) > 15:
        return Response(
            {
                "status": "error",
                "code": "INVALID_PHONE_NUMBER",
                "message": "Phone number must be 15 characters or fewer.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Validate default landing page
    # -----------------------------------------
    landing_page = None

    if "default_landing_page" in request.data:
        landing_page = request.data["default_landing_page"]

        allowed_pages = {
            "/",
            "/inventory",
            "/orders",
            "/customers",
        }

        if landing_page not in allowed_pages:
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_LANDING_PAGE",
                    "message": "Invalid Default Landing Page.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # -----------------------------------------
    # Update
    # -----------------------------------------
    user.first_name = first_name
    user.last_name = last_name
    user.email = email

    user.save(
        update_fields=[
            "first_name",
            "last_name",
            "email",
        ]
    )

    profile, _ = UserProfile.objects.get_or_create(
        user=user
    )

    profile.phone_number = phone_number

    update_fields = [
        "phone_number",
        "updated_at",
    ]

    if "default_landing_page" in request.data:
        profile.default_landing_page = landing_page
        update_fields.append("default_landing_page")

    profile.save(update_fields=update_fields)
    return Response(
        {
            "status": "success",
            "message": "Profile updated successfully.",
            "user": _profile_data(user),
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change the authenticated user's password.

    The current password must be verified before the new password
    is accepted. Django's configured password validators are used
    for the new password.
    """

    user = request.user

    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    # -----------------------------------------
    # Required fields
    # -----------------------------------------

    if not current_password:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_PASSWORD_REQUIRED",
                "message": "Current password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not new_password:
        return Response(
            {
                "status": "error",
                "code": "NEW_PASSWORD_REQUIRED",
                "message": "New password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not confirm_password:
        return Response(
            {
                "status": "error",
                "code": "CONFIRM_PASSWORD_REQUIRED",
                "message": "Please confirm your new password.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Verify current password
    # -----------------------------------------

    if not user.check_password(current_password):
        return Response(
            {
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Your current password is incorrect.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Confirm new password
    # -----------------------------------------

    if new_password != confirm_password:
        return Response(
            {
                "status": "error",
                "code": "PASSWORD_MISMATCH",
                "message": "New passwords do not match.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Prevent reusing current password
    # -----------------------------------------

    if user.check_password(new_password):
        return Response(
            {
                "status": "error",
                "code": "PASSWORD_UNCHANGED",
                "message": "Your new password must be different from your current password.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Django password validation
    # -----------------------------------------

    try:
        validate_password(
            new_password,
            user=user,
        )
    except ValidationError as error:
        return Response(
            {
                "status": "error",
                "code": "INVALID_NEW_PASSWORD",
                "message": error.messages[0],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------
    # Save new password
    # -----------------------------------------

    user.set_password(new_password)

    user.save(
        update_fields=["password"],
    )

    # Keep the current browser session authenticated.
    update_session_auth_hash(
        request,
        user,
    )

    tracked_session = UserSession.objects.filter(
        user=user,
        session_key=request.session.session_key,
    ).first()

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.PASSWORD_CHANGED,
        tracked_session,
    )

    return Response(
        {
            "status": "success",
            "message": "Password changed successfully.",
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def avatar_view(request):
    """
    Upload, replace, or remove the authenticated user's avatar.
    """

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "DELETE":
        if profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save(update_fields=["avatar", "updated_at"])

        return Response(
            {
                "status": "success",
                "message": "Avatar removed successfully.",
                "user": _profile_data(request.user),
            },
            status=status.HTTP_200_OK,
        )

    avatar = request.FILES.get("avatar")

    if not avatar:
        return Response(
            {
                "status": "error",
                "code": "AVATAR_REQUIRED",
                "message": "Please select an image.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    max_size = 10 * 1024 * 1024

    if avatar.size > max_size:
        return Response(
            {
                "status": "error",
                "code": "AVATAR_TOO_LARGE",
                "message": "Avatar image must be 10 MB or smaller.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        image = Image.open(avatar)

        image_format = image.format

        image.verify()

        avatar.seek(0)

    except Exception:
        return Response(
            {
                "status": "error",
                "code": "INVALID_AVATAR",
                "message": "The uploaded file is not a valid image.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    allowed_formats = {"JPEG", "PNG", "GIF", "WEBP"}

    if image_format not in allowed_formats:
        return Response(
            {
                "status": "error",
                "code": "UNSUPPORTED_AVATAR_FORMAT",
                "message": "Use a JPG, PNG, GIF, or WEBP image.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_avatar = profile.avatar

    profile.avatar = avatar
    profile.save()

    if old_avatar:
        old_avatar.delete(save=False)

    return Response(
        {
            "status": "success",
            "message": "Avatar uploaded successfully.",
            "user": _profile_data(request.user),
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def two_factor_status_view(request):
    """
    Return the current user's two-factor authentication status.

    Sensitive TOTP information is never returned.
    """

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(user=request.user)
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "success",
                "enabled": False,
                "setup_in_progress": False,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "status": "success",
            "enabled": two_factor_auth.is_enabled,
            "setup_in_progress": (
                not two_factor_auth.is_enabled
                and two_factor_auth.setup_started_at is not None
            ),
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def two_factor_recovery_code_status_view(request):
    """
    Return the current recovery-code usage status.

    Plaintext recovery codes are never returned.
    """

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=request.user,
            is_enabled=True,
        )
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_NOT_ENABLED",
                "message": (
                    "Two-factor authentication is not enabled."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    recovery_code_status = get_recovery_code_status(
        two_factor_auth
    )

    return Response(
        {
            "status": "success",
            "total": recovery_code_status["total"],
            "unused": recovery_code_status["unused"],
            "used": recovery_code_status["used"],
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def regenerate_two_factor_recovery_codes_view(request):
    """
    Generate a completely new set of recovery codes.

    Requires:
    - current account password
    - either a valid authenticator code or a valid recovery code

    Existing recovery codes are immediately invalidated.
    Plaintext codes are returned only once.
    """

    user = request.user

    current_password = request.data.get(
        "current_password"
    )

    method = request.data.get("method")
    code = request.data.get("code")

    if not current_password:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_PASSWORD_REQUIRED",
                "message": "Current password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(current_password):
        return Response(
            {
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Your current password is incorrect.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method not in {"TOTP", "RECOVERY_CODE"}:
        return Response(
            {
                "status": "error",
                "code": "INVALID_2FA_METHOD",
                "message": (
                    "A valid two-factor verification method "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(code, str) or not code.strip():
        return Response(
            {
                "status": "error",
                "code": "MISSING_2FA_CODE",
                "message": (
                    "A two-factor verification code "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=user,
            is_enabled=True,
        )
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_NOT_ENABLED",
                "message": (
                    "Two-factor authentication is not enabled."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method == "TOTP":
        verification_result = verify_totp_for_user(
            two_factor_auth,
            code,
        )
    else:
        verification_result = verify_recovery_code_for_user(
            two_factor_auth,
            code,
        )

    if not verification_result["success"]:
        reason = verification_result["reason"]

        error_messages = {
            "INVALID_CODE": (
                "The authenticator code is invalid."
            ),
            "CODE_ALREADY_USED": (
                "This authenticator code has already been used."
            ),
            "INVALID_RECOVERY_CODE": (
                "The recovery code is invalid."
            ),
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. "
                "Please try again later."
            ),
            "TWO_FACTOR_DISABLED": (
                "Two-factor authentication is not enabled."
            ),
            "CONFIGURATION_ERROR": (
                "Two-factor authentication is temporarily "
                "unavailable."
            ),
        }

        return Response(
            {
                "status": "error",
                "code": reason,
                "message": error_messages.get(
                    reason,
                    "Two-factor verification failed.",
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    recovery_codes = generate_recovery_codes()

    store_recovery_codes(
        two_factor_auth,
        recovery_codes,
    )

    tracked_session = UserSession.objects.filter(
        user=user,
        session_key=request.session.session_key,
    ).first()

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.TWO_FACTOR_RECOVERY_CODES_REGENERATED,
        tracked_session,
    )

    return Response(
        {
            "status": "success",
            "message": (
                "New recovery codes generated successfully. "
                "Your previous recovery codes are no longer valid."
            ),
            "recovery_codes": recovery_codes,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def disable_two_factor_view(request):
    """
    Disable two-factor authentication.

    Requires:
    - current account password
    - either a valid authenticator code or a valid recovery code

    All recovery codes are invalidated when 2FA is disabled.
    """

    user = request.user

    current_password = request.data.get(
        "current_password"
    )

    method = request.data.get("method")
    code = request.data.get("code")

    if not current_password:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_PASSWORD_REQUIRED",
                "message": "Current password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(current_password):
        return Response(
            {
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Your current password is incorrect.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method not in {"TOTP", "RECOVERY_CODE"}:
        return Response(
            {
                "status": "error",
                "code": "INVALID_2FA_METHOD",
                "message": (
                    "A valid two-factor verification method "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(code, str) or not code.strip():
        return Response(
            {
                "status": "error",
                "code": "MISSING_2FA_CODE",
                "message": (
                    "A two-factor verification code "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=user,
            is_enabled=True,
        )
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_NOT_ENABLED",
                "message": (
                    "Two-factor authentication is not enabled."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method == "TOTP":
        verification_result = verify_totp_for_user(
            two_factor_auth,
            code,
        )
    else:
        verification_result = verify_recovery_code_for_user(
            two_factor_auth,
            code,
        )

    if not verification_result["success"]:
        reason = verification_result["reason"]

        error_messages = {
            "INVALID_CODE": (
                "The authenticator code is invalid."
            ),
            "CODE_ALREADY_USED": (
                "This authenticator code has already been used."
            ),
            "INVALID_RECOVERY_CODE": (
                "The recovery code is invalid."
            ),
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. "
                "Please try again later."
            ),
            "TWO_FACTOR_DISABLED": (
                "Two-factor authentication is not enabled."
            ),
            "CONFIGURATION_ERROR": (
                "Two-factor authentication is temporarily "
                "unavailable."
            ),
        }

        return Response(
            {
                "status": "error",
                "code": reason,
                "message": error_messages.get(
                    reason,
                    "Two-factor verification failed.",
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth.is_enabled = False
    two_factor_auth.encrypted_secret = ""
    two_factor_auth.setup_started_at = None
    two_factor_auth.enabled_at = None
    two_factor_auth.last_verified_at = None
    two_factor_auth.last_used_time_step = None
    two_factor_auth.failed_attempts = 0
    two_factor_auth.locked_until = None
    two_factor_auth.pending_encrypted_secret = None
    two_factor_auth.pending_setup_started_at = None
    two_factor_auth.pending_last_used_time_step = None

    two_factor_auth.save(
        update_fields=[
            "is_enabled",
            "encrypted_secret",
            "setup_started_at",
            "enabled_at",
            "last_verified_at",
            "last_used_time_step",
            "failed_attempts",
            "locked_until",
            "pending_encrypted_secret",
            "pending_setup_started_at",
            "pending_last_used_time_step",
            "updated_at",
        ]
    )

    TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
    ).delete()

    tracked_session = UserSession.objects.filter(
        user=user,
        session_key=request.session.session_key,
    ).first()

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.TWO_FACTOR_DISABLED,
        tracked_session,
    )

    return Response(
        {
            "status": "success",
            "message": (
                "Two-factor authentication disabled successfully."
            ),
            "enabled": False,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_setup_view(request):
    """
    Begin 2FA setup after verifying the user's current password.

    The newly generated TOTP secret is encrypted before storage.
    The plaintext secret is returned only as part of the setup
    response so the user can configure an authenticator app.
    """

    user = request.user

    current_password = request.data.get(
        "current_password"
    )

    if not current_password:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_PASSWORD_REQUIRED",
                "message": "Current password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(current_password):
        return Response(
            {
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Your current password is incorrect.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = (
        UserTwoFactorAuth.objects
        .filter(user=user)
        .first()
    )

    if existing and existing.is_enabled:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_ALREADY_ENABLED",
                "message": "Two-factor authentication is already enabled.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    secret = generate_totp_secret()

    encrypted_secret = encrypt_totp_secret(
        secret
    )

    two_factor_auth, _ = (
        UserTwoFactorAuth.objects.update_or_create(
            user=user,
            defaults={
                "encrypted_secret": encrypted_secret,
                "is_enabled": False,
                "setup_started_at": timezone.now(),
                "enabled_at": None,
                "last_verified_at": None,
                "last_used_time_step": None,
                "failed_attempts": 0,
                "locked_until": None,
            },
        )
    )

    provisioning_uri = generate_provisioning_uri(
        secret,
        user.username,
    )

    return Response(
        {
            "status": "success",
            "message": "Two-factor authentication setup started.",
            "enabled": False,
            "secret": secret,
            "provisioning_uri": provisioning_uri,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_verify_setup_view(request):
    """
    Verify the authenticator code and permanently enable 2FA.

    Recovery codes are generated only after successful TOTP
    verification.
    """

    user = request.user

    code = request.data.get("code")

    if not code:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_CODE_REQUIRED",
                "message": "Authenticator code is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(user=user)
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_SETUP_NOT_STARTED",
                "message": "Two-factor authentication setup has not been started.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if two_factor_auth.is_enabled:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_ALREADY_ENABLED",
                "message": "Two-factor authentication is already enabled.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = verify_totp_setup_for_user(
        two_factor_auth,
        code,
    )

    if not result["success"]:
        error_messages = {
            "INVALID_CODE": "The authenticator code is invalid.",
            "CODE_ALREADY_USED": "This authenticator code has already been used.",
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. Please try again later."
            ),
            "TWO_FACTOR_SETUP_EXPIRED": (
                "Your two-factor authentication setup has expired. "
                "Please start the setup again."
            ),
            "TWO_FACTOR_SETUP_NOT_STARTED": (
                "Two-factor authentication setup has not been started."
            ),
            "TWO_FACTOR_ALREADY_ENABLED": (
                "Two-factor authentication is already enabled."
            ),
            "CONFIGURATION_ERROR": (
                "Two-factor authentication could not be verified."
            ),
        }

        return Response(
            {
                "status": "error",
                "code": result["reason"],
                "message": error_messages.get(
                    result["reason"],
                    "The authenticator code could not be verified.",
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth.is_enabled = True
    two_factor_auth.enabled_at = timezone.now()

    two_factor_auth.save(
        update_fields=[
            "is_enabled",
            "enabled_at",
            "updated_at",
        ]
    )

    recovery_codes = generate_recovery_codes()

    store_recovery_codes(
        two_factor_auth,
        recovery_codes,
    )

    SecurityEvent.objects.create(
        user=user,
        event_type=SecurityEvent.EventType.TWO_FACTOR_ENABLED,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    return Response(
        {
            "status": "success",
            "message": "Two-factor authentication enabled successfully.",
            "enabled": True,
            "recovery_codes": recovery_codes,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def two_factor_authenticator_change_view(request):
    """
    Begin changing the user's authenticator app.

    The current password and currently active 2FA method must
    be verified before a new authenticator is created.

    The existing authenticator remains active until the new
    authenticator is successfully verified.
    """

    user = request.user

    current_password = request.data.get(
        "current_password"
    )

    method = request.data.get("method")
    code = request.data.get("code")

    if not current_password:
        return Response(
            {
                "status": "error",
                "code": "CURRENT_PASSWORD_REQUIRED",
                "message": "Current password is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(current_password):
        return Response(
            {
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "Your current password is incorrect.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=user,
            is_enabled=True,
        )
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_NOT_ENABLED",
                "message": (
                    "Two-factor authentication is not enabled."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method not in {"TOTP", "RECOVERY_CODE"}:
        return Response(
            {
                "status": "error",
                "code": "INVALID_2FA_METHOD",
                "message": (
                    "A valid two-factor verification method "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(code, str) or not code.strip():
        return Response(
            {
                "status": "error",
                "code": "MISSING_2FA_CODE",
                "message": (
                    "A two-factor verification code "
                    "is required."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method == "TOTP":
        verification_result = verify_totp_for_user(
            two_factor_auth,
            code,
        )
    else:
        verification_result = verify_recovery_code_for_user(
            two_factor_auth,
            code,
        )

    if not verification_result["success"]:
        reason = verification_result["reason"]

        error_messages = {
            "INVALID_CODE": (
                "The authenticator code is invalid."
            ),
            "CODE_ALREADY_USED": (
                "This authenticator code has already been used."
            ),
            "INVALID_RECOVERY_CODE": (
                "The recovery code is invalid."
            ),
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. "
                "Please try again later."
            ),
            "TWO_FACTOR_DISABLED": (
                "Two-factor authentication is not enabled."
            ),
            "CONFIGURATION_ERROR": (
                "Two-factor authentication is temporarily "
                "unavailable."
            ),
        }

        return Response(
            {
                "status": "error",
                "code": reason,
                "message": error_messages.get(
                    reason,
                    "Two-factor verification failed.",
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    secret = generate_totp_secret()

    encrypted_secret = encrypt_totp_secret(
        secret
    )

    two_factor_auth.pending_encrypted_secret = (
        encrypted_secret
    )
    two_factor_auth.pending_setup_started_at = (
        timezone.now()
    )
    two_factor_auth.pending_last_used_time_step = None

    two_factor_auth.save(
        update_fields=[
            "pending_encrypted_secret",
            "pending_setup_started_at",
            "pending_last_used_time_step",
            "updated_at",
        ]
    )

    provisioning_uri = generate_provisioning_uri(
        secret,
        user.username,
    )

    return Response(
        {
            "status": "success",
            "message": (
                "New authenticator setup started. "
                "Your current authenticator remains active "
                "until the new one is verified."
            ),
            "secret": secret,
            "provisioning_uri": provisioning_uri,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def two_factor_authenticator_change_verify_view(request):
    """
    Verify the new authenticator and make it the active
    authenticator.

    The old authenticator remains active until this
    verification succeeds.
    """

    user = request.user

    code = request.data.get("code")

    if not isinstance(code, str) or not code.strip():
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_CODE_REQUIRED",
                "message": "Authenticator code is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth = (
        UserTwoFactorAuth.objects
        .filter(
            user=user,
            is_enabled=True,
        )
        .first()
    )

    if not two_factor_auth:
        return Response(
            {
                "status": "error",
                "code": "TWO_FACTOR_NOT_ENABLED",
                "message": (
                    "Two-factor authentication is not enabled."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = verify_totp_authenticator_change_for_user(
        two_factor_auth,
        code,
    )

    if not result["success"]:
        error_messages = {
            "TWO_FACTOR_DISABLED": (
                "Two-factor authentication is not enabled."
            ),
            "TWO_FACTOR_CHANGE_NOT_STARTED": (
                "A new authenticator setup has not been started."
            ),
            "TWO_FACTOR_CHANGE_EXPIRED": (
                "The new authenticator setup has expired. "
                "Please start again."
            ),
            "INVALID_CODE": (
                "The authenticator code is invalid."
            ),
            "CODE_ALREADY_USED": (
                "This authenticator code has already been used."
            ),
            "TOO_MANY_ATTEMPTS": (
                "Too many verification attempts. "
                "Please try again later."
            ),
            "CONFIGURATION_ERROR": (
                "The new authenticator could not be verified."
            ),
        }

        return Response(
            {
                "status": "error",
                "code": result["reason"],
                "message": error_messages.get(
                    result["reason"],
                    "The new authenticator could not be verified.",
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    two_factor_auth.encrypted_secret = (
        two_factor_auth.pending_encrypted_secret
    )

    two_factor_auth.last_used_time_step = (
        two_factor_auth.pending_last_used_time_step
    )

    two_factor_auth.pending_encrypted_secret = None
    two_factor_auth.pending_setup_started_at = None
    two_factor_auth.pending_last_used_time_step = None

    two_factor_auth.save(
        update_fields=[
            "encrypted_secret",
            "last_used_time_step",
            "pending_encrypted_secret",
            "pending_setup_started_at",
            "pending_last_used_time_step",
            "updated_at",
        ]
    )

    tracked_session = UserSession.objects.filter(
        user=user,
        session_key=request.session.session_key,
    ).first()

    _record_security_event(
        request,
        user,
        SecurityEvent.EventType.TWO_FACTOR_AUTHENTICATOR_CHANGED,
        tracked_session,
    )

    return Response(
        {
            "status": "success",
            "message": (
                "Authenticator app changed successfully."
            ),
        },
        status=status.HTTP_200_OK,
    )
