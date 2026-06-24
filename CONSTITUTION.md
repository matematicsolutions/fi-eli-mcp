# Constitution of fi-eli-mcp

Version: 0.1.0
Date: 2026-06-24
Licence: Apache-2.0

`fi-eli-mcp` is an MCP server for the Finnish Finlex open-data API
(`opendata.finlex.fi`). It fetches consolidated Finnish statutes as Akoma Ntoso 3.0 XML with
verifiable ELI citations. The MVP covers statutes (saadokset); case law is a later feature.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV).

---

## Art. 1. Public data only

The Finlex open-data API is the official, public source of Finnish legislation, published as Open
Government Data (keyless). The server is read-only against Finlex and sends nothing beyond the
requested year / number.

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/fi-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to write =
the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server talks
only to `opendata.finlex.fi` and the local filesystem. Authentication: none; own backoff + cache.

## Art. 4. ELI citations and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: the canonical ELI from `FRBRalias[name=eli]` (e.g. `http://data.finlex.fi/eli/sd/2018/1050/alkup`).
- `human_readable_citation`: title + number/year (e.g. "Tietosuojalaki (1050/2018)").
- `source_url`: the open-data API URL of the act (the fetchable original).

---

## Open points

1. **Keyword search** - the open-data API is path-based (by year/number); discovery is by year. Not a search API.
2. **Case law** and **bilingual title selection** (fi vs sv) - later refinements.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-06-24. Author: Wieslaw Mazur / MateMatic.
