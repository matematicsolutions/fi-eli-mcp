"""FastMCP entry point - Finnish Finlex statute tools.

Run:

    python -m fi_eli_mcp.server

Configuration via env:

- ``FI_ELI_CACHE_DIR`` (default ``~/.matematic/cache/fi-eli``)
- ``FI_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``FI_ELI_BASE_URL`` (default ``https://opendata.finlex.fi/finlex/avoindata/v1``)
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, hash_input, timer
from .citations import parse_acts
from .client import DEFAULT_BASE_URL, FinlexClient
from .models import Act, ActListResult, LawText

INSTRUCTIONS = """\
This MCP server exposes the Finnish Finlex open-data API (opendata.finlex.fi). It serves consolidated Finnish statutes (saadokset) as Akoma Ntoso 3.0 XML. Every response carries a stable `eli_uri`, a `human_readable_citation` and a `source_url` (the citation contract). Finland is bilingual; titles may be Finnish or Swedish.

## Call order

1. `fi_list_acts` - list the statutes of a given `year` (e.g. 2018). Use this to discover the `number` of an act. Each item carries `eli_uri`, `human_readable_citation`, `source_url`.
2. `fi_get_act` - metadata for a statute by `year` and `number` (e.g. 2018 / 1050): `eli_uri` (e.g. `http://data.finlex.fi/eli/sd/2018/1050/alkup`), title, dates.
3. `fi_get_text` - the full Akoma Ntoso XML of a statute by `year` and `number`.

## Hard constraints

- **No free-text search** - the open-data API is addressed by year and number, not keywords. Discover via `fi_list_acts` (by year). Relay the `dataset_note`.
- **ELI is the key to citability** - Finlex returns a full ELI URL in `eli_uri`; do not invent it.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user.
- **No modification of official text** - returned verbatim (Akoma Ntoso) from Finlex.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/fi-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing or out of range (e.g. a non-numeric or implausible year).
- `not_found` - no statute exists for that year / number.
- `upstream_error` - a Finlex API error (HTTP, timeout, malformed XML). Retry once before surfacing.

## Response style

- Cite acts as `human_readable_citation` with the ELI URL: "Tietosuojalaki (1050/2018), http://data.finlex.fi/eli/sd/2018/1050/alkup".
- NEVER invent an ELI, a number or a year - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for fi-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="fi-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("FI_ELI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        return ToolError("not_found", "No statute found in Finlex for that year/number.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"Finlex API error: {type(exc).__name__}: {exc}")
    return exc


def _check_year(year: int) -> None:
    if not 1700 <= year <= 2100:
        raise ToolError("invalid_arg", f"year={year} is out of range (1700..2100).")


# ---------------------------------------------------------------------------
# fi_list_acts
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def fi_list_acts(year: int) -> ActListResult:
    """List Finnish statutes published in a given year.

    Args:
        year: e.g. ``2018``.

    Returns:
        ``ActListResult`` with ``items: list[Act]``, each carrying the citation contract.
    """
    audit = _audit()
    _check_year(year)
    input_hash = hash_input({"year": year})

    with timer() as t:
        try:
            async with FinlexClient(base_url=_base_url()) as client:
                xml = await client.list_year(year)
        except Exception as exc:
            audit.log(tool="fi_list_acts", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    items = [Act.model_validate(a) for a in parse_acts(xml)]
    result = ActListResult(year=year, total=len(items), items=items)
    audit.log(tool="fi_list_acts", input_hash=input_hash, output_count_or_size=len(items),
              duration_ms=t.duration_ms, status="ok")
    return result


# ---------------------------------------------------------------------------
# fi_get_act
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def fi_get_act(year: int, number: int) -> Act:
    """Fetch statute metadata by year and number.

    Args:
        year: e.g. ``2018``.
        number: e.g. ``1050``.

    Returns:
        ``Act`` with ``eli_uri``, ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    _check_year(year)
    if number <= 0:
        raise ToolError("invalid_arg", f"number={number} must be positive.")
    input_hash = hash_input({"year": year, "number": number})

    with timer() as t:
        try:
            async with FinlexClient(base_url=_base_url()) as client:
                xml = await client.get_act(year, number)
        except Exception as exc:
            audit.log(tool="fi_get_act", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    acts = parse_acts(xml)
    if not acts:
        raise ToolError("not_found", f"No statute {number}/{year} in Finlex.")
    act = Act.model_validate(acts[0])
    audit.log(tool="fi_get_act", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return act


# ---------------------------------------------------------------------------
# fi_get_text
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def fi_get_text(year: int, number: int) -> LawText:
    """Fetch the full Akoma Ntoso text of a statute by year and number.

    Args:
        year: e.g. ``2018``.
        number: e.g. ``1050``.

    Returns:
        ``LawText`` with ``eli_uri``, ``human_readable_citation``, ``source_url`` and ``content`` (Akoma Ntoso XML).
    """
    audit = _audit()
    _check_year(year)
    if number <= 0:
        raise ToolError("invalid_arg", f"number={number} must be positive.")
    input_hash = hash_input({"year": year, "number": number})

    with timer() as t:
        try:
            async with FinlexClient(base_url=_base_url()) as client:
                xml = await client.get_act(year, number)
        except Exception as exc:
            audit.log(tool="fi_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    acts = parse_acts(xml)
    if not acts:
        raise ToolError("not_found", f"No statute {number}/{year} in Finlex.")
    meta = acts[0]
    result = LawText(
        year=year,
        number=number,
        eli_uri=meta.get("eli_uri"),
        human_readable_citation=meta.get("human_readable_citation"),
        source_url=meta.get("source_url"),
        content=xml,
        byte_size=len(xml.encode("utf-8")),
    )
    audit.log(tool="fi_get_text", input_hash=input_hash, output_count_or_size=result.byte_size or 0,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
