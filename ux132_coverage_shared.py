"""Small pure presentation helpers shared by documentary coverage domains."""
from unicodedata import normalize, combining


def search_key(value):
    return "".join(c for c in normalize("NFKD", value.casefold())
                   if not combining(c)).strip()
