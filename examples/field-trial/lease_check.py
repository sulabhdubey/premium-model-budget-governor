def lease_valid(now, expires_at):
    """Return whether the lease permits work at the given numeric timestamp."""
    return now <= expires_at
