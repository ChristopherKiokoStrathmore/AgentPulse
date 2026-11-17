# AgentPulse MVP
An **independent Airtel Money inspired** owner intelligence demo for 30 *fictional* Nairobi outlet locations. Nothing in the app represents actual Airtel customer, employee, location, balance, transaction or commission data.

## What works
* Seven clickable views: Overview, Liquidity, Outlets, Transactions, GeoIntelligence, Decision Centre, Reports.
* Thirty simulated outlet profiles with searchable tables, status filters, balances and an interactive geographic display.
* Eight illustrative candidate sites on a Nairobi OpenStreetMap tile layer.
* Six configurable expansion factor weights; candidate scores and rankings recalculate immediately using normalized weights.
* Save a weight configuration to this browser's local storage; reset to defaults.
* Transaction explorer and CSV exports.
* A deterministic 36 month illustration covering November 2023 through October 2026.

## Run
Node 22+:
\`\`\`bash
cd apps/web
npm install
npm run dev
\`\`\`
This initial hosted frontend uses a deterministic, **client-side demo dataset**. It does not connect to real Airtel Money APIs or execute payments/transfers. It is intentionally self-contained for a presentation; the separately provided fuller source package also contains a FastAPI example.

## Scoring
\`score(site) = sum(weight[i] / sum(weights) * site_feature[i])\`.
All site features are hypothetical 0–100 values. The rankings do not represent real site predictions, and the illustrative coordinates do not identify actual agency premises.

## Presentation sequence
1. Overview: monitor simulated cash, electronic float, commissions and risks.
2. Liquidity: investigate critical outlet balances.
3. Outlets: compare 30 outlet profiles.
4. Transactions: filter and export a sample.
5. GeoIntelligence: alter sliders, watch the top candidate change, filter by rent and save.
6. Decision Centre: explain transparent liquidity and expansion scenarios.
7. Reports: acknowledge which data and conclusions are simulated.

## Roadmap
Introduce a Railway FastAPI API and PostgreSQL/PostGIS, consolidate frontend/backend fixtures, integrate licensed geographic datasets, implement secure owner accounts, and validate against authorized real business data before operational use.
