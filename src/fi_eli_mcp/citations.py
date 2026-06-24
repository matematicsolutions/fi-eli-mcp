"""Finnish Finlex (Akoma Ntoso) parsing + citation helpers.

Finlex serves legislation as Akoma Ntoso 3.0 XML. The ELI is exposed as
``<FRBRalias name="eli" value="http://data.finlex.fi/eli/sd/2018/1050/alkup"/>`` inside
``meta/identification/FRBRWork``. We parse it with the stdlib ElementTree - no third-party XML dep.

Citation contract:
- ``eli_uri``: the ``FRBRalias[name=eli]`` value.
- ``human_readable_citation``: ``docTitle`` + number/year (e.g. "Dataskyddslag (1050/2018)").
- ``source_url``: the open-data API URL of the act (the fetchable original).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
OPENDATA_BASE = "https://opendata.finlex.fi/finlex/avoindata/v1"


def _q(tag: str) -> str:
    return f"{{{AKN_NS}}}{tag}"


def _year_number_from_uri(frbr_uri: str | None) -> tuple[str | None, str | None]:
    if not frbr_uri:
        return None, None
    parts = [p for p in frbr_uri.split("/") if p]
    if len(parts) >= 2 and parts[-1].isdigit() and parts[-2].isdigit():
        return parts[-2], parts[-1]
    return None, None


def _parse_one(akn: ET.Element) -> dict[str, Any]:
    out: dict[str, Any] = {}
    work = akn.find(f".//{_q('identification')}/{_q('FRBRWork')}")
    if work is not None:
        for alias in work.findall(_q("FRBRalias")):
            if alias.get("name") == "eli" and alias.get("value"):
                out["eli_uri"] = alias.get("value")
        uri = work.find(_q("FRBRuri"))
        if uri is not None and uri.get("value"):
            out["frbr_uri"] = uri.get("value")
        num = work.find(_q("FRBRnumber"))
        if num is not None and num.get("value"):
            out["number"] = num.get("value")
        sub = work.find(_q("FRBRsubtype"))
        if sub is not None and sub.get("value"):
            out["subtype"] = sub.get("value")
        for d in work.findall(_q("FRBRdate")):
            name = d.get("name")
            if name == "dateIssued":
                out["date_issued"] = d.get("date")
            elif name == "datePublished":
                out["date_published"] = d.get("date")

    title_el = akn.find(f".//{_q('preface')}//{_q('docTitle')}")
    if title_el is not None:
        title = "".join(title_el.itertext()).strip()
        if title:
            out["title"] = title

    year, number = _year_number_from_uri(out.get("frbr_uri"))
    if year:
        out["year"] = year
    if number and "number" not in out:
        out["number"] = number

    # Citation: "Title (number/year)" - the Finnish convention cites number/year.
    title = out.get("title")
    if number and year:
        ref = f"{number}/{year}"
        out["human_readable_citation"] = f"{title} ({ref})" if title else ref
    elif title:
        out["human_readable_citation"] = title

    if out.get("frbr_uri"):
        out["source_url"] = f"{OPENDATA_BASE}{out['frbr_uri']}"
    elif out.get("eli_uri"):
        out["source_url"] = out["eli_uri"]
    return out


def parse_acts(xml_text: str) -> list[dict[str, Any]]:
    """Parse one or many acts from a Finlex AknXmlList response.

    Works for both a single act and a year listing (both wrap ``akomaNtoso`` elements).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    acts = root.findall(f".//{_q('akomaNtoso')}")
    return [_parse_one(a) for a in acts]
