from django.conf import settings
from django.db import models


class BusinessMembership(models.Model):
    """
    Connects a Django user to a business.

    A user can belong to one or more businesses,
    and each membership defines the user's role.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        STAFF = "STAFF", "Staff"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_memberships",
    )

    business = models.ForeignKey(
        "tenants.Business",
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_user_business",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.business.name} - "
            f"{self.role}"
        )


class UserBusinessContext(models.Model):
    """
    Stores the business the user has explicitly selected
    as their current working business.

    The selected business must always be validated against
    the user's active BusinessMembership before it is used.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_context",
    )

    current_business = models.ForeignKey(
        "tenants.Business",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.current_business or 'No business selected'}"
        )

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.ImageField(
        upload_to="profiles/avatars/",
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile - {self.user.username}"

class UserSession(models.Model):
    """
    Tracks an authenticated Django session for security management.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tracked_sessions",
    )

    session_key = models.CharField(
        max_length=40,
        unique=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_active_at = models.DateTimeField(
        auto_now=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-last_active_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.session_key}"
        )

class SecurityEvent(models.Model):
    """
    Records security-sensitive actions performed on a user account.
    """

    class EventType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        SESSION_REVOKED = "SESSION_REVOKED", "Session cancelled"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password changed"
        PASSWORD_RESET = "PASSWORD_RESET", "Password reset"

        TWO_FACTOR_ENABLED = (
            "TWO_FACTOR_ENABLED",
            "Two-factor authentication enabled",
        )

        TWO_FACTOR_DISABLED = (
            "TWO_FACTOR_DISABLED",
            "Two-factor authentication disabled",
        )

        TWO_FACTOR_RECOVERY_CODES_REGENERATED = (
            "TWO_FACTOR_RECOVERY_CODES_REGENERATED",
            "Two-factor recovery codes regenerated",
        )

        TWO_FACTOR_AUTHENTICATOR_CHANGED = (
            "TWO_FACTOR_AUTHENTICATOR_CHANGED",
            "Authenticator app changed",
        )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_events",
    )

    event_type = models.CharField(
        max_length=64,
        choices=EventType.choices,
    )

    session = models.ForeignKey(
        UserSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="sec_event_user_created",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.event_type} - "
            f"{self.created_at}"
        )

class UserTwoFactorAuth(models.Model):
    """
    Stores the user's two-factor authentication configuration.

    The TOTP secret must always be stored encrypted.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_auth",
    )

    encrypted_secret = models.TextField()

    is_enabled = models.BooleanField(
        default=False,
    )

    setup_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    enabled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_used_time_step = models.BigIntegerField(
        null=True,
        blank=True,
    )

    failed_attempts = models.PositiveIntegerField(
        default=0,
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    pending_encrypted_secret = models.TextField(
        blank=True,
        null=True,
    )

    pending_setup_started_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    pending_last_used_time_step = models.BigIntegerField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"2FA - {self.user.username} - "
            f"{'Enabled' if self.is_enabled else 'Disabled'}"
        )


class TwoFactorRecoveryCode(models.Model):
    """
    Stores one-time recovery codes for two-factor authentication.

    Only password hashes are stored. Plaintext recovery codes
    are never persisted in the database.
    """

    two_factor_auth = models.ForeignKey(
        UserTwoFactorAuth,
        on_delete=models.CASCADE,
        related_name="recovery_codes",
    )

    code_hash = models.CharField(
        max_length=128,
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Recovery code - "
            f"{self.two_factor_auth.user.username} - "
            f"{'Used' if self.used_at else 'Unused'}"
        )