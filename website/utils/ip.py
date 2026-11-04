import ipaddress

def is_valid_ip(ip_str):
    """
    Validates whether a string is a valid IPv4 or IPv6 address.
    """
    if not ip_str or not isinstance(ip_str, str):
        return False
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except (ValueError, AttributeError):
        return False


def get_client_ip(request):
    """
    Extracts and safely validates the visitor's IP address from the request.
    Handles IPv4, IPv6, proxies (Cloudflare, reverse proxies), and direct connections.
    Never crashes and returns None if no valid IP address can be determined.
    """
    if not request or not hasattr(request, 'META'):
        return None

    # 1. Cloudflare connecting IP header
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip and is_valid_ip(cf_ip.strip()):
        return cf_ip.strip()

    # 2. X-Forwarded-For header (reverse proxy / load balancer chain)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(',') if p.strip()]
        for candidate in parts:
            if is_valid_ip(candidate):
                return candidate

    # 3. Standard REMOTE_ADDR (standard WSGI / Passenger direct socket connection)
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr and is_valid_ip(remote_addr.strip()):
        return remote_addr.strip()

    return None
