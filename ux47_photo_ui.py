"""Photo presentation for UX 4.7 destination cards.

A CSS background layer sits above a neutral placeholder. Browser failures
expose the fallback without broken <img> glyphs or per-rerun HTTP probes.
Only HTTPS Wikimedia-hosted catalog assets are displayed. Scoped inline styles
are local to each photo, not global application CSS.
"""
from __future__ import annotations
from html import escape
from urllib.parse import urlsplit,quote

PHOTO_HOSTS=frozenset({"commons.wikimedia.org","upload.wikimedia.org",
                       "thumb.wikimedia.org"})

def permitted_photo_url(value:object)->str|None:
    if not isinstance(value,str) or not value.strip():
        return None
    try:
        parsed=urlsplit(value.strip())
        if parsed.scheme!="https" or parsed.hostname not in PHOTO_HOSTS or (
            parsed.username is not None or parsed.password is not None
        ) or parsed.port not in (None,443):
            return None
        # Keep valid URL characters and %-encoded Commons filenames, but
        # encode quote, parentheses, backslashes and control characters.
        path=quote(parsed.path,safe="/%:@!$&+,;=-._~")
        query=quote(parsed.query,safe="/%=&?+,:;-._~")
        return "https://"+parsed.hostname+path+("?"+query if query else "")
    except (ValueError,TypeError):
        return None

def photo_markup(photo:dict|None,name:str)->str:
    """Build a local, responsive 4:5 visual with a neutral failure fallback."""
    url=permitted_photo_url((photo or {}).get("url"))
    name_html=escape(str(name),quote=True)
    # Background images do not display the browser's broken image icon.
    # Transparent layer when load fails leaves the neutral placeholder visible.
    image_layer=(
        '<div aria-hidden="true" style="position:absolute;inset:0;'
        'border-radius:inherit;background-position:center center;'
        'background-size:cover;background-repeat:no-repeat;'
        "background-image:url(&quot;"+escape(url,quote=True)+"&quot;)"></div>"
        if url else "")
    return (
        '<div role="img" aria-label="Fotografia de '+name_html+
        ' (quando disponível)" style="position:relative;'
        'width:100%;max-width:310px;aspect-ratio:4/5;max-height:365px;'
        'border-radius:14px;overflow:hidden;background:#EDF1F4;'
        'display:flex;align-items:center;justify-content:center;">'
        '<span style="color:#647480;font-size:0.85rem;text-align:center;'
        'padding:16px;">Imagem indisponível</span>'
        +image_layer+"</div>"
    )

def photo_credit(photo:dict|None)->str|None:
    """Metadata credit is retained even if the browser cannot load its URL."""
    if not permitted_photo_url((photo or {}).get("url")):
        return None
    author=escape(str(photo.get("author") or "Autor não informado"))
    license_name=escape(str(photo.get("license") or "Licença não informada"))
    source=permitted_photo_url(photo.get("source_page"))
    license_link=photo.get("license_url")
    from urllib.parse import urlsplit
    if isinstance(license_link,str):
        p=urlsplit(license_link)
        if p.scheme!="https" or p.hostname not in ("creativecommons.org",):
            license_link=None
    if source:
        author="["+author+"]("+source+")"
    if license_link:
        license_name="["+license_name+"]("+license_link+")"
    # Attribution names the registered source rather than pretending the
    # remote image necessarily loaded successfully.
    return "Crédito da foto cadastrada: "+author+" · "+license_name
