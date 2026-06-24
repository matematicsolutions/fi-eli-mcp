"""Pydantic v2 models for the Finnish Finlex API + fi-eli-mcp."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

DATASET_NOTE = (
    "Finlex serves Finnish consolidated statutes as Akoma Ntoso. Discover by year "
    "(fi_list_acts) or fetch by year+number. This MVP covers statutes (saadokset); "
    "case law is not yet covered. Finland is bilingual - titles may be Finnish or Swedish."
)


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Act(_Tolerant):
    """A Finnish statute (parsed from Akoma Ntoso metadata)."""

    year: str | None = None
    number: str | None = None
    title: str | None = None
    subtype: str | None = None
    frbr_uri: str | None = None
    date_issued: str | None = None
    date_published: str | None = None

    # Citation contract (Art. 4 CONSTITUTION).
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None


class ActListResult(_Tolerant):
    """Result of ``fi_list_acts``."""

    year: int
    total: int
    items: list[Act] = Field(default_factory=list)
    dataset_note: str = DATASET_NOTE


class LawText(_Tolerant):
    """Result of ``fi_get_text`` (full Akoma Ntoso XML)."""

    year: int
    number: int
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    format: str = "akoma-ntoso-xml"
    content: str | None = None
    byte_size: int | None = None
    dataset_note: str = DATASET_NOTE
