"""
Kept in its own module to avoid a circular import between main.py and
the route handlers that need to reference the same limiter instance.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
