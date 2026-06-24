# fi-eli-mcp

An MCP server for the Finnish **Finlex** open-data API (`opendata.finlex.fi`). It fetches
consolidated Finnish statutes as Akoma Ntoso 3.0 XML, with verifiable ELI identifiers and
Finnish citations.

Part of the MateMatic `eu-legal-mcp` production line - after PL, DE, AT and ES. Same citation
contract, Finlex source.

> **Scope.** This MVP covers Finnish statutes (saadokset). Discovery is by year (`fi_list_acts`)
> or by year + number; the open-data API is path-based, not keyword search. Finland is bilingual,
> so titles may be Finnish or Swedish. Every response carries a `dataset_note`.
>
> **Licence.** Finnish legislation in Finlex is official public information published as open
> data (keyless). This connector relays it with attribution and a `source_url`.

## The tools

| Tool | What it does |
|---|---|
| `fi_list_acts` | List the statutes of a year (discovery). |
| `fi_get_act` | Metadata for a statute by year + number. |
| `fi_get_text` | Full Akoma Ntoso text of a statute by year + number. |

Every response carries the contract: `eli_uri` (a full ELI URL, e.g.
`http://data.finlex.fi/eli/sd/2018/1050/alkup`), `human_readable_citation`
(e.g. `Tietosuojalaki (1050/2018)`), and `source_url`.

## Install

```bash
cd fi-eli-mcp
pip install -e .
```

## Configure (Claude Code / any MCP client)

```json
{
  "mcpServers": {
    "fi-eli-mcp": { "command": "fi-eli-mcp" }
  }
}
```

Environment:

- `FI_ELI_BASE_URL` - default `https://opendata.finlex.fi/finlex/avoindata/v1`
- `FI_ELI_CACHE_DIR` - default `~/.matematic/cache/fi-eli`
- `FI_ELI_AUDIT_DIR` - default `~/.matematic/audit`

No API key. Finlex open data is keyless.

## Governance

- **Public data only** - read-only against Finlex; no client data leaves the machine.
- **Audit log** - every tool call appends one JSON line to `~/.matematic/audit/fi-eli-mcp.jsonl`.
- **Vendor-neutral** - talks only to `opendata.finlex.fi`; no LLM provider, no telemetry.
- **Verifiable citations** - every response is independently checkable via `source_url`.

See `CONSTITUTION.md` and `DISCOVERY.md`.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/test_instructions_drift.py -v   # offline
pytest tests/test_smoke.py -v                # hits live Finlex
```

## Licence

Apache-2.0. © Matematic Solutions / Wieslaw Mazur.
