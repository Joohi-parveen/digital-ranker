from django.db import models
from django.contrib.auth.models import User


class BlockedIP(models.Model):
    """
    Model to store blocked IP addresses and prevent spam / malicious form submissions.
    Supports both IPv4 and IPv6 addresses, permanent or temporary blocks,
    and tracks blocked submission attempts.
    """
    ip_address = models.GenericIPAddressField(
        unique=True,
        unpack_ipv4=False,
        db_index=True,
        verbose_name="IP Address",
        help_text="Valid IPv4 or IPv6 address to block."
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Reason",
        help_text="Reason for blocking this IP (e.g. repeated spam submissions)."
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Is Active",
        help_text="Whether this IP block is currently enforced."
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expires At",
        help_text="Optional expiration date/time. Leave blank for permanent block."
    )
    blocked_attempts_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Blocked Attempts",
        help_text="Count of form submissions blocked from this IP."
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Blocked Attempt"
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_blocked_ips",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blocked IP"
        verbose_name_plural = "Blocked IPs"

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.ip_address} ({status})"
