import logging
from django.utils import timezone
from django.db import models
from website.models import BlockedIP
from website.utils.ip import is_valid_ip

logger = logging.getLogger(__name__)


def is_ip_blocked(ip_address):
    """
    Checks whether the provided IP address is currently blocked.
    
    1. Validates the IP format (returns False if invalid or None).
    2. Queries the BlockedIP table for active records matching the IP.
    3. Handles expiration: if expires_at is set and past, the block has expired
       and will not be enforced (is_active is lazily updated).
    4. If actively blocked, increments blocked_attempts_count and updates last_attempt_at.
    5. Returns True if blocked, False otherwise.
    """
    if not ip_address or not is_valid_ip(ip_address):
        return False

    ip_clean = ip_address.strip()
    now = timezone.now()

    blocked_entry = BlockedIP.objects.filter(ip_address=ip_clean, is_active=True).first()
    if not blocked_entry:
        return False

    # Check for temporary block expiration
    if blocked_entry.expires_at and blocked_entry.expires_at <= now:
        # Block has expired; lazily deactivate
        blocked_entry.is_active = False
        blocked_entry.save(update_fields=['is_active'])
        logger.info(f"Block on IP {ip_clean} expired at {blocked_entry.expires_at} and was deactivated.")
        return False

    # Actively blocked - record the attempt atomically
    BlockedIP.objects.filter(pk=blocked_entry.pk).update(
        blocked_attempts_count=models.F('blocked_attempts_count') + 1,
        last_attempt_at=now
    )
    logger.warning(f"Blocked form submission attempt intercepted from IP: {ip_clean} (Block ID #{blocked_entry.pk})")
    return True
