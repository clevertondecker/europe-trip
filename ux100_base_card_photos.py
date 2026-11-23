"""Verified photo strip for city-base cards.

Uses existing validated local WebP assets or the human-reviewed Commons
catalog. No generic image search or external API on reruns.
"""
from __future__ import annotations

from html import escape
import streamlit as st
from destination_photo_assets import local_destination_photo
from ux501_destination_photo_service import curated_destination_photo


def _safe(value) -> str:
    return escape(str(value), quote=True)


def base_card_photo_record(base_id: str) -> dict | None:
    """Return verified metadata, or None. Never substitute a nearby city."""
    return local_destination_photo(base_id) or curated_destination_photo(base_id)


def render_base_card_photo(base_id: str, name: str) -> None:
    """Render one real photo with a stable fallback and explicit provenance."""
    photo = base_card_photo_record(base_id)
    with st.container(key="ux100_photo_" + base_id):
        if photo and photo.get("local_path"):
            st.image(photo["local_path"], width="stretch")
        elif photo and photo.get("url"):
            url = _safe(photo["url"])
            st.markdown(
                '<div class="ux100-photo-fallback" role="img" aria-label="Foto de '+_safe(name)+'">'
                '<span>Foto indisponível no momento</span>'
                '<div class="ux100-photo-external" aria-hidden="true" '
                'style="background-image:url(&quot;'+url+'&quot;)"></div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ux100-photo-fallback" role="img" '
                'aria-label="Fotografia de '+_safe(name)+' ainda não disponível">'
                '<span>Foto de '+_safe(name)+' ainda não disponível</span></div>',
                unsafe_allow_html=True,
            )
        if photo:
            source = _safe(photo["source_page"])
            license_url = _safe(photo["license_url"])
            st.markdown(
                '<div class="ux100-photo-credit">Foto: '+_safe(photo["author"])
                +' · <a href="'+license_url+'" target="_blank" rel="noopener noreferrer">'
                +_safe(photo["license"])+'</a> · '
                '<a href="'+source+'" target="_blank" rel="noopener noreferrer">Fonte</a></div>',
                unsafe_allow_html=True,
            )
