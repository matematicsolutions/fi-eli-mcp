# Discovery: Finlex open-data API (opendata.finlex.fi) - Finland

Date: 2026-06-24. **Status: CLOSED** for a statutes MVP (confirmed by live probing).

Finnish Finlex open-data API. Keyless, modern, serves **Akoma Ntoso 3.0 XML** with FRBR + ELI.
The fastest clean connector after DE/AT/ES (chosen on WM's "pick the fastest" directive).

## Base API properties (CONFIRMED)

- **Base URL:** `https://opendata.finlex.fi/finlex/avoindata/v1`
- **Authentication:** none (open data).
- **Format:** Akoma Ntoso 3.0 XML (`application/xml`), wrapped in `<AknXmlList><Results><akomaNtoso>...`.
- **ELI:** YES - `<FRBRalias name="eli" value="http://data.finlex.fi/eli/sd/2018/1050/alkup"/>` in `meta/identification/FRBRWork`.

## Endpoints (CONFIRMED)

| Endpoint | Notes |
|---|---|
| `/akn/fi/act/statute/{year}/{number}` | a single statute, full Akoma Ntoso (meta + body) |
| `/akn/fi/act/statute/{year}` | all statutes of a year (list of akomaNtoso) |
| `/akn/fi/act/statute-consolidated` | all consolidated statutes (large) |

## FRBRWork fields (for the citation contract)

- `FRBRalias[name=eli]` -> `eli_uri` (e.g. `http://data.finlex.fi/eli/sd/2018/1050/alkup`).
- `FRBRuri` -> `/akn/fi/act/statute/2018/1050` (year + number).
- `FRBRnumber` -> "1050"; `FRBRsubtype` -> "statute".
- `FRBRdate[name=dateIssued|datePublished]`.
- `preface//docTitle` -> the title (Finnish or Swedish - Finland is bilingual; e.g. "Dataskyddslag").

## Citation contract (Article IV) - CLOSED for FI

- `eli_uri` = `FRBRalias[name=eli]` value.
- `human_readable_citation` = `docTitle` + number/year (e.g. "Tietosuojalaki (1050/2018)").
- `source_url` = the open-data API act URL (`{base}{FRBRuri}`) - the fetchable original.

## Tool mapping - statutes MVP

| Tool | Endpoint |
|---|---|
| `fi_list_acts` | `/akn/fi/act/statute/{year}` |
| `fi_get_act` | `/akn/fi/act/statute/{year}/{number}` (parse meta) |
| `fi_get_text` | `/akn/fi/act/statute/{year}/{number}` (full Akoma Ntoso) |

**Deferred:** keyword search (the API is path-based, discover by year), case law.

## Differences vs DE/AT/ES/PL

- Pure Akoma Ntoso 3.0 - parsed with stdlib ElementTree (no XML dep).
- Discovery is by year (path-based), not keyword search.
- Bilingual titles (fi/sv).

## Decision: BUILD (fastest)

ELI present, keyless, modern Akoma Ntoso, clean path-based access. Reuse: audit + cache verbatim,
server pattern. New: tiny AKN parser (citations) + Finlex client. The cleanest mapping of the line so far.
