"""Security boundary for GitHub writes: verified Google OIDC identity only.

This is intentionally independent of Streamlit so it can be tested. Streamlit
validates the OIDC identity token when the user returns from st.login("google").
"""
from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime, timezone
from hmac import compare_digest

GOOGLE_ISSUERS=frozenset({"https://accounts.google.com","accounts.google.com"})

def is_verified_owner(identity:Mapping|None,owner_email:str,now:int|None=None)->bool:
    """Fail closed if no provider, Google verification, expiration or email."""
    if not identity or not owner_email or "@" not in owner_email:
        return False
    if identity.get("is_logged_in") is not True:
        return False
    if identity.get("iss") not in GOOGLE_ISSUERS:
        return False
    if identity.get("email_verified") not in (True,"true","True"):
        return False
    address=identity.get("email")
    if not isinstance(address,str):
        return False
    if not compare_digest(address.casefold().strip(),owner_email.casefold().strip()):
        return False
    expiry=identity.get("exp")
    try:
        exp=int(expiry)
    except (TypeError,ValueError):
        return False
    current=int(datetime.now(timezone.utc).timestamp()) if now is None else now
    return exp>current+30
