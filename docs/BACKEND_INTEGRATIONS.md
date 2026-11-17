# AgentPulse API integrations

Railway project: agentpulse-nairobi

A FastAPI application persists 30 synthetic outlets, a 36 month synthetic monthly series, transaction samples and balanced ledger entries in Railway PostgreSQL.

Public enrichment:

* WorldPop v3 catchment API: 2026 population estimates within 0.5 and 1 km of candidate sites, retrieved and cached in PostgreSQL. Attribution: WorldPop Global2 CC BY 4.0.
* Open-Meteo archive API: historical precipitation for Nairobi in October 2026, cached. Free public endpoint only for noncommercial use, attribution required.
* OpenStreetMap: current frontend tile basemap, attribution required. Not a measured traffic API. Production map tile hosting requires evaluating acceptable usage.

The app must distinguish synthetic financial transactions and proxy ranking factors from genuine open source population and weather observations. If a provider fetch fails, the data source endpoint returns an explicit unavailable status.

Endpoints: /health, /docs, /v1/overview, /v1/outlets, /v1/transactions, /v1/monthly, /v1/ledger/check, /v1/geo/candidates, /v1/geo/scores/preview, /v1/geo/weight-profiles, /v1/geo/public-context, /v1/data-sources.

This is a demonstration backend, not a secure real money service. No authentication, Airtel Money production credentials, automated transfers, or guaranteed live traffic feed.
