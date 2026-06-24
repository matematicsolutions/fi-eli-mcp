"""Smoke tests - require internet, hit the live Finlex API.

Run manually:

    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import pytest

from fi_eli_mcp.server import fi_get_act, fi_get_text, fi_list_acts

# Tietosuojalaki / Dataskyddslag - Finnish Data Protection Act, 1050/2018.
YEAR, NUMBER = 2018, 1050


@pytest.mark.asyncio
async def test_smoke_get_act() -> None:
    act = await fi_get_act(YEAR, NUMBER)
    assert act.eli_uri is not None, "missing eli_uri"
    assert "data.finlex.fi/eli" in act.eli_uri, f"bad eli: {act.eli_uri!r}"
    assert act.number == str(NUMBER)
    assert act.human_readable_citation is not None and "1050/2018" in act.human_readable_citation
    assert act.source_url is not None and act.source_url.startswith("https://")


@pytest.mark.asyncio
async def test_smoke_get_text() -> None:
    text = await fi_get_text(YEAR, NUMBER)
    assert text.content is not None and "akomaNtoso" in text.content
    assert text.eli_uri is not None and "data.finlex.fi/eli" in text.eli_uri
    assert text.byte_size and text.byte_size > 0


@pytest.mark.asyncio
async def test_smoke_list_acts() -> None:
    result = await fi_list_acts(YEAR)
    assert result.total > 0, "expected statutes for 2018"
    for item in result.items[:10]:
        assert item.eli_uri is not None and "data.finlex.fi/eli" in item.eli_uri
        assert item.source_url is not None
