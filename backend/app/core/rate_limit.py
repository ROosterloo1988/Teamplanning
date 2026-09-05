import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Eenvoudige in-memory sliding-window rate limiter per sleutel (meestal
    IP-adres). Geen Redis/externe afhankelijkheid nodig: de backend draait
    als één uvicorn-proces, dus in-memory state is hier voldoende — dit is
    geen distributed rate limiting voor meerdere workers/instanties."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        attempts = self._attempts[key]
        while attempts and now - attempts[0] > self.window_seconds:
            attempts.popleft()
        if len(attempts) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Te veel pogingen, probeer het over een paar minuten opnieuw",
            )
        attempts.append(now)


def client_ip(request: Request) -> str:
    """Neemt het eerste adres uit X-Forwarded-For (gezet door een reverse
    proxy of, hier, door Next.js' rewrite-proxy), anders het directe
    verbindingsadres. Bij meerdere gebruikers achter dezelfde proxy zonder
    doorgegeven header vallen ze samen onder één sleutel — een acceptabele
    tegenprestatie: erger is duizenden ongelimiteerde gokpogingen op het
    gedeelde teamwachtwoord."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
