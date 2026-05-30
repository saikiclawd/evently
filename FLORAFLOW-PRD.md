# FloraFlow — Product Requirements Document

**Version:** 2.0
**Client:** Luxel Decor & Flowers
**Prepared by:** Product Team
**Last Updated:** 2026-05-20
**Status:** Active

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Problem](#2-business-problem)
3. [Target Users](#3-target-users)
4. [Success Metrics](#4-success-metrics)
5. [Key Features](#5-key-features)
6. [Functional Requirements](#6-functional-requirements)
   - 6.1 Flower Catalog
   - 6.2 Event & Arrangement Builder
   - 6.3 Recipe Studio
   - 6.4 Order Engine
   - 6.5 Inventory Management
   - 6.6 Reporting & Analytics
   - 6.7 Recipe Similarity Detection *(New)*
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Integrations](#8-integrations)
9. [Workflow Diagrams](#9-workflow-diagrams)
10. [Permission & Role Structure](#10-permission--role-structure)
11. [Technical Architecture](#11-technical-architecture)
12. [API Design](#12-api-design)
13. [Database Design](#13-database-design)
14. [Proposal System](#14-proposal-system)
15. [AI Feature Roadmap](#15-ai-feature-roadmap)
16. [Mobile Experience](#16-mobile-experience)
17. [Testing Strategy](#17-testing-strategy)
18. [Deployment & Infrastructure](#18-deployment--infrastructure)
19. [Open Questions](#19-open-questions)
20. [MVP vs Phase 2 vs Phase 3](#20-mvp-vs-phase-2-vs-phase-3) *(Updated)*
21. [Competitive Differentiation](#21-competitive-differentiation) *(New)*
22. [SaaS Pricing Model](#22-saas-pricing-model) *(New)*
23. [Onboarding & Data Import](#23-onboarding--data-import) *(New)*
- [Appendix A: Glossary](#appendix-a-glossary)
- [Appendix B: Sample Data Structures](#appendix-b-sample-data-structures)
- [Appendix C: Quick Wins — Immediate Phase 1 Additions](#appendix-c-quick-wins--immediate-phase-1-additions) *(New)*

---

## 1. Executive Summary

FloraFlow is a floral stem calculation and ordering automation platform purpose-built for Luxel Decor & Flowers. It replaces a fragile, error-prone spreadsheet workflow with a structured, version-controlled, collaborative system that connects recipe creation, event planning, purchase order generation, and inventory reconciliation in a single end-to-end workflow.

### Problem in One Line

Luxel's designers spend 3–5 hours per large event manually calculating stem counts, building vendor orders, and reconciling inventory — a process rife with errors, version conflicts, and invisible margin bleed.

### Solution in One Line

FloraFlow automates the stem calculation pipeline: a designer builds or selects a recipe, assigns it to an event, and the system generates scaled POs per vendor with real-time margin visibility.

### Strategic Objectives

1. Reduce stem calculation time per event by 80%.
2. Eliminate duplicate-order errors caused by multi-version spreadsheets.
3. Provide real-time cost-vs.-quoted margin visibility per event.
4. Enable post-event inventory reconciliation and wastage analysis.
5. Build toward AI-powered buffer optimization and demand forecasting in Phase 2.
6. Establish a clear competitive differentiation from Floranext, Details Flowers, and existing wholesale ordering portals by being the only platform that combines recipe versioning + automated PO generation + real-time margin visibility in a single end-to-end workflow. *(Updated)*

---

## 2. Business Problem

Luxel Decor & Flowers is a high-volume wedding and event floristry studio operating with a manual, spreadsheet-based workflow for stem calculation and vendor ordering. This creates compounding operational risk as event volume grows.

### Core Pain Points

| Pain Point | Impact |
|---|---|
| Manual stem calculation per event | 3–5 hours per large wedding |
| No recipe versioning | Designers work from different spreadsheet versions |
| No automated PO generation | Ordering errors and missed items |
| No real-time margin tracking | Profitability only visible post-event |
| Inventory discrepancies | Over-ordering, wastage not tracked |
| Vendor communication via email | No single source of truth for PO status |

### Business Risk

As Luxel scales from ~30 to 60+ events per month, the spreadsheet workflow does not scale. A single miscalculation on a 500-person wedding can result in $800–$2,000 in emergency sourcing costs or under-delivered arrangements.

---

## 3. Target Users

| Role | Primary Workflows |
|---|---|
| Owner / Principal Designer | Financial oversight, proposal review, pricing approval |
| Head Designer | Recipe authoring, event build sign-off, vendor selection |
| Designer | Arrangement building, event assignment |
| Operations Manager | PO review, vendor coordination, delivery scheduling |
| Warehouse Staff | Inventory receiving, count entry, wastage logging |
| Bookkeeper | Read-only access to financials, PO log, payment records |

---

## 4. Success Metrics

| Metric | Phase 1 Target | Phase 2 Target |
|---|---|---|
| Stem calculation time per event | < 30 minutes | < 10 minutes |
| PO generation errors | < 2% | < 0.5% |
| Inventory waste rate | Baseline established | 10% reduction |
| Designer adoption | 100% of Luxel team | N/A (internal) |
| Margin visibility | Real-time per event | Predictive per event type |

---

## 5. Key Features

### Milestone 1 (M1) — Recipe & Calculation Engine

- Flower catalog with variety, cost, bunch size, seasonality
- Recipe Studio: build arrangements with named stem line items
- Automatic stem scaling (per guest count, per table, per unit)
- Category-aware buffer matrix (arches 15%, centerpieces 10%, boutonnières 5%)
- Recipe versioning with change history

### Milestone 2 (M2) — Event Planner & Order Engine *(Updated)*

- Event creation with date, venue, guest count, package tier
- Assign recipes to rooms/areas within an event
- Aggregate stem totals across all arrangements
- PO generation split by vendor preference
- PO PDF export and email send
- Payment and deposit tracking per event
- Event day / production checklist per room and arrangement

### Milestone 3 (M3) — Inventory & Reconciliation

- Inventory ledger: opening counts, received, adjusted
- Receiving workflow: scan/confirm against PO line items
- Pre-order inventory netting (reduce PO by in-stock quantity)
- Post-event wastage capture with reason codes
- Inventory alerts: low stock, overstock

### Milestone 4 (M4) — Reporting & AI

- Margin report: quoted vs. actual cost per event
- Vendor fill rate performance
- Stem demand forecasting by season
- AI-powered buffer recommendations
- Analytics dashboard (home screen)

---

## 6. Functional Requirements

### 6.1 Flower Catalog

The flower catalog is the master data layer for all stem calculations.

**6.1.1 Flower Record Fields**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | Multi-tenant isolation |
| common_name | VARCHAR(100) | e.g. "Garden Rose" |
| variety | VARCHAR(100) | e.g. "White Ohara" |
| color | VARCHAR(50) | |
| cost_per_stem | DECIMAL(8,4) | At current pricing |
| bunch_size | INTEGER | Default bunch size |
| season_start | MONTH | Optional |
| season_end | MONTH | Optional |
| buffer_pct | DECIMAL(5,2) | Override global default |
| photo_url | TEXT | |
| is_active | BOOLEAN | |

**6.1.2 Catalog Actions**

- CRUD for flowers (Owner, Head Designer)
- Bulk import via CSV
- Price update propagation: when cost_per_stem changes, affected recipes are flagged for review
- Seasonal availability warnings on event builds

### 6.2 Event & Arrangement Builder

#### 6.2.1 Event Record Fields

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| organization_id | UUID | |
| name | VARCHAR(255) | e.g. "Chen-Williams Wedding" |
| event_date | DATE | |
| venue | VARCHAR(255) | |
| guest_count | INTEGER | |
| package_tier | ENUM | essential / signature / luxe |
| quoted_total | DECIMAL(10,2) | |
| status | ENUM | draft / confirmed / in_production / complete / cancelled |
| lead_designer_id | UUID FK | |
| notes | TEXT | |

#### 6.2.2 Event Build *(Updated)*

An event build is the set of arrangements assigned to an event, organized by location/room.

**EventArrangement Fields**

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| event_id | UUID FK | |
| recipe_id | UUID FK | Pinned to specific recipe version |
| location | VARCHAR(100) | e.g. "Ceremony Arch", "Table 12" |
| quantity | INTEGER | How many of this arrangement |
| scaled_total_cost | DECIMAL(10,2) | Computed |

**EventStemOverride** *(New)*

When a designer manually overrides a stem count for an arrangement, the override is saved separately and flagged as custom so it does not get overwritten if the recipe updates.

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| event_arrangement_id | UUID FK | |
| flower_id | UUID FK | |
| override_quantity | INTEGER | Replaces calculated quantity |
| reason | TEXT | Why this was overridden |

**Event Payments** *(New)*

Events track client payment milestones — deposit (typically 50%), balance payment (30 days before event), and refund.

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| event_id | UUID FK | |
| amount | DECIMAL(10,2) | |
| payment_type | ENUM | deposit / balance / refund |
| payment_date | DATE | |
| method | VARCHAR(50) | e.g. 'bank transfer', 'check', 'card' |
| notes | TEXT | |

**Event Day / Production Checklist** *(New)*

Each event has a checklist of arrangements organized by setup location. Designers can print this or view on mobile. Each checklist item contains:

- Arrangement name
- Quantity
- Location
- Assigned staff
- Status: `staged` / `delivered` / `complete`

### 6.3 Recipe Studio

**6.3.1 Recipe Fields**

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| organization_id | UUID | |
| name | VARCHAR(255) | e.g. "White Ohara Garden Centerpiece" |
| category | ENUM | centerpiece / arch / boutonniere / ceremony / other |
| version | INTEGER | Auto-incremented on publish |
| status | ENUM | draft / published / archived |
| base_unit | VARCHAR(50) | e.g. "per table", "per person" |
| notes | TEXT | |

**6.3.2 Recipe Stem Line Items**

Each recipe has one or more stem line items:

| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| recipe_id | UUID FK | |
| flower_id | UUID FK | |
| quantity_per_unit | DECIMAL(8,2) | Stems per base unit |
| notes | TEXT | |

**6.3.3 Recipe Versioning**

- Every publish action creates a new version snapshot
- Event builds pin to a specific version at time of assignment
- Designers can view version diffs
- Rollback to any previous version (Owner / Head Designer only)

### 6.4 Order Engine *(Updated)*

**6.4.1 PO Generation Logic**

1. Aggregate stem requirements across all event arrangements
2. Apply category-aware buffer matrix (see Section 15)
3. Net against current inventory
4. Split by vendor using Vendor-Flower Preference Matrix
5. Round up to whole bunches per vendor's bunch size
6. Generate one PO per vendor with line items
7. Calculate PO totals and update event cost estimate

**6.4.2 Vendor-Flower Preference Matrix** *(New)*

Each vendor has a catalog of preferred flowers with priority ranking. When the Order Engine splits a PO across vendors, it uses this matrix:

- **Primary vendor** per flower type (priority 1)
- **Backup vendor** if primary fill rate drops below threshold (priority 2+)
- The matrix is a table: `vendor_id`, `flower_id`, `priority_rank`, `typical_unit_price`, `min_fill_rate_threshold`

**6.4.3 Vendor Substitution Workflow** *(New)*

When a vendor confirms a PO with a variety substitution (e.g., "Ohara unavailable, substituting Mayra"), the system provides:

1. A substitution notification on the PO record
2. The lead designer is alerted to review and approve or reject the substitution
3. If **approved**: the event build is updated with a note; inventory adjusted on receipt
4. If **rejected**: the system triggers a backup vendor order for the original variety

### 6.5 Inventory Management

- Manual inventory entry (opening counts)
- Receiving workflow: confirm receipt against PO line items, enter actual quantities received
- Automatic inventory netting before PO generation
- Post-event wastage entry with reason codes: `damaged`, `over_ordered`, `leftover_repurposed`, `other`
- Inventory snapshot per event for audit trail

### 6.6 Reporting & Analytics

| Report | Access |
|---|---|
| Margin Report (quoted vs. actual per event) | Owner, Head Designer |
| PO Log (all POs, status, totals) | Owner, Operations, Bookkeeper |
| Vendor Fill Rate | Owner, Operations |
| Stem Demand by Season | Owner, Head Designer |
| Wastage Report | Owner, Operations, Warehouse |
| Event Payments Summary | Owner, Bookkeeper |
| Analytics Dashboard | All roles (scoped) |

### 6.7 Recipe Similarity Detection *(New)*

When a designer saves a new recipe, the system checks the existing library for arrangements with similar stem compositions (same flower varieties, within 20% of quantities). If a match above 70% similarity is found, the designer is shown a warning:

> "This looks similar to **[Recipe Name]**. Would you like to extend that recipe instead?"

This prevents library bloat as the studio grows and encourages recipe reuse over duplication.

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Page load < 2s on 10 Mbps connection; PO generation < 5s for 20-arrangement event |
| Availability | 99.5% uptime during business hours (Mon–Sat 7am–8pm local) |
| Data Integrity | All financial calculations use DECIMAL types, not floats |
| Multi-Tenancy | Full row-level isolation per organization_id |
| Audit Trail | All create/update/delete actions logged with user_id, timestamp, and changed fields |
| Accessibility | WCAG 2.1 AA for all core workflows |
| Browser Support | Chrome, Safari, Firefox (latest 2 versions); Edge |

---

## 8. Integrations

| Integration | Phase | Purpose |
|---|---|---|
| Mayesh Wholesale API | Phase 2 | Live pricing and availability |
| Syndicate Sales | Phase 2 | Secondary vendor catalog |
| QuickBooks / Xero | Phase 2 | PO and payment sync |
| SendGrid / Postmark | Phase 1 | Transactional email (PO send, proposal send) |
| Supabase Storage | Phase 1 | PDF storage for POs and proposals |
| Twilio | Phase 3 | SMS alerts for vendor confirmations |

---

## 9. Workflow Diagrams

**W1: New Event Stem Calculation**
1. Designer creates event (date, venue, guest count, package)
2. Designer assigns recipes to rooms/locations
3. System calculates stem totals per flower per arrangement
4. System applies category-aware buffers
5. System nets against current inventory
6. System generates draft POs split by vendor preference
7. Operations reviews and sends POs

**W2: Recipe Versioning**
1. Head Designer opens published recipe
2. Makes edits to stem quantities or flower selections
3. Saves as draft
4. Reviews changes vs. previous version
5. Publishes → new version created
6. Events using old version remain pinned; designer can opt to update

**W3: Inventory Receiving**
1. Vendor delivers order
2. Warehouse staff opens PO in FloraFlow
3. Confirms each line item: quantity received, condition
4. System updates inventory ledger
5. Any discrepancies flagged for Operations review

**W4: Post-Event Reconciliation**
1. Operations opens completed event
2. Enters actual stems used per arrangement
3. Records wastage with reason codes
4. System computes actual cost vs. quoted
5. Margin report updated
6. Wastage data fed into AI buffer model (Phase 2)

**W5: Vendor Substitution Workflow** *(New)*
1. Vendor confirms PO with substitution note
2. System marks PO line item as "substituted — pending approval"
3. Lead designer receives notification: "Mayesh substituted White Ohara → White Mayra on PO #FLW-2026-0847"
4. Designer reviews substitution in context of event build
5. Designer approves or rejects
6. If approved: PO line item updated, event notes flagged, inventory adjusted on receipt
7. If rejected: system creates a new PO line item for the original variety and routes to backup vendor

---

## 10. Permission & Role Structure *(Updated)*

| Permission | Owner | Head Designer | Designer | Operations | Warehouse | Bookkeeper |
|---|---|---|---|---|---|---|
| Flower Catalog CRUD | ✓ | ✓ | Read | Read | Read | Read |
| Recipe Create/Edit | ✓ | ✓ | ✓ | — | — | — |
| Recipe Publish/Archive | ✓ | ✓ | — | — | — | — |
| Event Create/Edit | ✓ | ✓ | ✓ | Read | — | — |
| Event Build (arrangements) | ✓ | ✓ | ✓ | Read | — | — |
| Stem Override | ✓ | ✓ | — | — | — | — |
| PO Generate | ✓ | ✓ | — | ✓ | — | — |
| PO Send | ✓ | — | — | ✓ | — | — |
| PO Log View | ✓ | ✓ | — | ✓ | — | ✓ |
| Inventory Receive | ✓ | — | — | ✓ | ✓ | — |
| Wastage Entry | ✓ | ✓ | — | ✓ | ✓ | — |
| Proposal Create/Send | ✓ | ✓ | — | — | — | — |
| Event Payments | ✓ | — | — | ✓ | — | ✓ |
| Margin Report | ✓ | ✓ | — | — | — | ✓ |
| Analytics Dashboard | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| User Management | ✓ | — | — | — | — | — |

> **Note:** Bookkeeper sees financial data (PO Log, Margin Report, Event Payments, Analytics) but cannot modify any records. This is a read-only role scoped to financial visibility.

---

## 11. Technical Architecture

### 11.1 Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React + TypeScript | Vite build tooling |
| UI Components | shadcn/ui + Tailwind CSS | |
| Backend | Python / FastAPI | REST API |
| Database | PostgreSQL (prod) / SQLite (local dev) | |
| Auth | Supabase Auth | Email + magic link; Row-Level Security |
| File Storage | Supabase Storage | PO PDFs, proposal PDFs, flower photos |
| Cache | Redis (prod) / SimpleCache (local dev) | |
| PDF Generation | WeasyPrint or Puppeteer | Server-side PDF |
| Deployment | Docker Compose (Phase 1) | |

### 11.2 Multi-Tenancy Model

All tables include `organization_id`. Row-Level Security (RLS) policies in Supabase enforce tenant isolation at the database layer. Application-layer middleware validates `organization_id` on every request.

### 11.3 Data Flow

```
Designer Input → Recipe Studio → Event Builder
                                      ↓
                           Stem Aggregation Engine
                                      ↓
                      Inventory Netting ← Inventory Ledger
                                      ↓
                    Vendor Split (Preference Matrix)
                                      ↓
                         PO Generation → PDF → Email
                                      ↓
                        Margin Calculator → Dashboard
```

### 11.4 PWA Strategy (Phase 3 Alternative) *(New)*

Before committing to native iOS/Android apps in Phase 3, evaluate a Progressive Web App (PWA) approach:

- **Service Workers** for offline caching of event builds and inventory data
- **IndexedDB** for offline-first inventory receiving and wastage entry
- **Background sync** for queueing offline mutations until reconnection
- Eliminates separate native codebases and app store maintenance

**Recommended evaluation criteria:** If warehouse workflows require barcode scanning only available via native APIs, proceed with native. Otherwise, PWA delivers equivalent UX at significantly lower cost.

### 11.5 Local Development Configuration *(New)*

For Phase 1 internal deployment at Luxel, a local development mode is provided:

- SQLite database (no PostgreSQL setup required)
- SimpleCache (no Redis required)
- Run via `python run_local.py` from the backend directory
- Auto-creates all tables and seeds sample flowers and vendors on first run

```bash
cd backend
python run_local.py
# → Tables created
# → Sample flowers seeded (50 common wedding varieties)
# → Sample vendors seeded (Mayesh, Syndicate Sales)
# → Running on http://localhost:8000
```

---

## 12. API Design *(Updated)*

### Base URL

```
/api/v1/
```

### Authentication

All endpoints require `Authorization: Bearer <token>`. Token issued by Supabase Auth.

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/flowers` | List flower catalog |
| POST | `/flowers` | Create flower |
| PUT | `/flowers/:id` | Update flower |
| DELETE | `/flowers/:id` | Soft-delete flower |
| GET | `/recipes` | List recipes |
| POST | `/recipes` | Create recipe |
| GET | `/recipes/:id` | Get recipe with stem line items |
| PUT | `/recipes/:id` | Update recipe (creates draft) |
| POST | `/recipes/:id/publish` | Publish recipe version |
| POST | `/recipes/:id/duplicate` | Clone a recipe *(New)* |
| GET | `/events` | List events |
| POST | `/events` | Create event |
| GET | `/events/:id` | Get event with arrangements |
| PUT | `/events/:id` | Update event |
| POST | `/events/:id/duplicate` | Clone an event as a template *(New)* |
| POST | `/events/:id/arrangements` | Add arrangement to event |
| POST | `/events/:id/arrangements/:aid/override` | Override stem count on arrangement *(New)* |
| GET | `/events/:id/checklist` | Get production checklist for event *(New)* |
| POST | `/events/:id/payments` | Record client payment *(New)* |
| GET | `/events/:id/payments` | List payments for event *(New)* |
| GET | `/orders` | List purchase orders |
| POST | `/orders/generate` | Generate POs for event |
| GET | `/orders/:id` | Get PO with line items |
| PUT | `/orders/:id/status` | Update PO status |
| POST | `/orders/:id/substitution` | Record vendor substitution *(New)* |
| POST | `/orders/:id/export-pdf` | Export PO as PDF |
| POST | `/inventory/receive` | Record inventory receipt against PO |
| POST | `/inventory/wastage` | Record post-event wastage |
| GET | `/inventory/snapshot` | Current inventory levels |
| POST | `/proposals` | Create a new proposal *(New)* |
| GET | `/proposals/:id` | Get proposal with line items *(New)* |
| PUT | `/proposals/:id` | Update proposal *(New)* |
| POST | `/proposals/:id/send` | Send proposal to client *(New)* |
| GET | `/proposals/:id/status` | Check read/open status *(New)* |
| GET | `/analytics/dashboard` | Home screen widget data *(New)* |
| GET | `/analytics/margin` | Margin report |
| GET | `/analytics/vendor-fill-rate` | Vendor performance |
| GET | `/analytics/wastage` | Wastage report |

---

## 13. Database Design *(Updated)*

### Core Tables

**organizations**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(200) | |
| slug | VARCHAR(100) | URL-safe identifier |
| currency | VARCHAR(3) | Default 'USD' |
| timezone | VARCHAR(50) | |
| global_buffer_pct | DECIMAL(5,2) | Default buffer |
| po_email_template | TEXT | |
| created_at | TIMESTAMPTZ | |

**flowers**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| common_name | VARCHAR(100) | |
| variety | VARCHAR(100) | |
| color | VARCHAR(50) | |
| cost_per_stem | DECIMAL(8,4) | |
| bunch_size | INTEGER | |
| season_start | SMALLINT | Month number 1–12 |
| season_end | SMALLINT | |
| buffer_pct | DECIMAL(5,2) | Overrides org default |
| photo_url | TEXT | |
| is_active | BOOLEAN | Default true |

**vendors** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| name | VARCHAR(200) | e.g. 'Mayesh Wholesale' |
| contact_name | VARCHAR(200) | |
| email | VARCHAR(255) | |
| phone | VARCHAR(30) | |
| min_order_value | DECIMAL(10,2) | |
| lead_days | INTEGER | Default delivery lead time |
| notes | TEXT | |
| is_active | BOOLEAN | |

**vendor_flower_preferences** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| vendor_id | UUID FK | |
| flower_id | UUID FK | |
| priority_rank | INTEGER | 1 = primary, 2 = backup |
| typical_unit_price | DECIMAL(8,4) | |
| bunch_size_override | INTEGER | Vendor-specific bunch size |
| min_fill_rate | DECIMAL(5,2) | Below this, use next vendor |

**recipes**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| name | VARCHAR(255) | |
| category | ENUM | centerpiece / arch / boutonniere / ceremony / other |
| version | INTEGER | Auto-incremented |
| status | ENUM | draft / published / archived |
| base_unit | VARCHAR(50) | |
| notes | TEXT | |
| created_by | UUID FK | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**recipe_stem_items**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| recipe_id | UUID FK | |
| flower_id | UUID FK | |
| quantity_per_unit | DECIMAL(8,2) | |
| notes | TEXT | |

**events**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| name | VARCHAR(255) | |
| event_date | DATE | |
| venue | VARCHAR(255) | |
| guest_count | INTEGER | |
| package_tier | ENUM | essential / signature / luxe |
| quoted_total | DECIMAL(10,2) | |
| status | ENUM | draft / confirmed / in_production / complete / cancelled |
| lead_designer_id | UUID FK | |
| notes | TEXT | |
| created_at | TIMESTAMPTZ | |

**event_arrangements**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| event_id | UUID FK | |
| recipe_id | UUID FK | |
| recipe_version | INTEGER | Pinned at assignment time |
| location | VARCHAR(100) | |
| quantity | INTEGER | |
| scaled_total_cost | DECIMAL(10,2) | Computed |

**event_stem_overrides** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| event_arrangement_id | UUID FK | |
| flower_id | UUID FK | |
| override_quantity | INTEGER | Replaces calculated quantity |
| reason | TEXT | Why this was overridden |

**event_payments** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| event_id | UUID FK | |
| amount | DECIMAL(10,2) | |
| payment_type | ENUM | deposit / balance / refund |
| payment_date | DATE | |
| method | VARCHAR(50) | e.g. 'bank transfer', 'check', 'card' |
| notes | TEXT | |

**purchase_orders**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| event_id | UUID FK | |
| vendor_id | UUID FK | |
| po_number | VARCHAR(50) | e.g. FLW-2026-0847 |
| status | ENUM | draft / sent / confirmed / received / cancelled |
| order_date | DATE | |
| expected_delivery | DATE | |
| total_amount | DECIMAL(10,2) | |
| pdf_url | TEXT | |
| notes | TEXT | |

**po_line_items** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| po_id | UUID FK | |
| flower_id | UUID FK | |
| stems_required | INTEGER | |
| bunches_required | INTEGER | |
| bunch_size | INTEGER | At time of order |
| unit_price | DECIMAL(8,4) | At time of order |
| line_total | DECIMAL(10,2) | |
| substitution_note | TEXT | Null unless vendor substituted |
| substitution_status | ENUM | null / pending / approved / rejected |

**proposals** *(New)*

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| event_id | UUID FK | |
| title | VARCHAR(255) | |
| status | ENUM | draft / sent / viewed / accepted / declined / expired |
| package_tier | ENUM | essential / signature / luxe |
| expires_at | DATE | Auto-set based on org default (e.g. 14 days from sent) |
| client_email | VARCHAR(255) | |
| sent_at | TIMESTAMPTZ | |
| viewed_at | TIMESTAMPTZ | |
| accepted_at | TIMESTAMPTZ | |
| pdf_url | TEXT | Generated PDF in storage |
| designer_notes | TEXT | |

**inventory_ledger**

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| flower_id | UUID FK | |
| transaction_type | ENUM | received / adjustment / wastage / used |
| quantity | INTEGER | Positive = in, negative = out |
| reference_id | UUID | PO id, event id, or null |
| reason_code | VARCHAR(50) | For wastage entries |
| notes | TEXT | |
| created_by | UUID FK | |
| created_at | TIMESTAMPTZ | |

---

## 14. Proposal System

### 14.1 Proposal Lifecycle

```
draft → sent → viewed → accepted
                    ↘ declined
                    ↘ expired
```

### 14.2 Proposal Features

- Tiered packages: Essential / Signature / Luxe with itemized line items
- Per-arrangement photo and description
- PDF generation (branded with org logo)
- Client-facing view link (no login required)
- Read receipt: `viewed_at` timestamp set on first open
- Configurable expiry (default 14 days from send date; see Appendix C)
- Automatic reminder email 3 days before expiry

### 14.3 Proposal to Event Conversion

When a client accepts a proposal, the system:
1. Creates or updates the associated event record
2. Copies package tier and arrangement selections into the event build
3. Sets event status to `confirmed`
4. Notifies lead designer

---

## 15. AI Feature Roadmap

### Phase 2 AI Features

**AI-1: Demand Forecasting**
Train on historical event data (event type, date, guest count, season) to predict stem volumes for new events. Output: suggested starting quantities per arrangement category.

**AI-2: Vendor Fill Rate Prediction**
Use historical PO data to predict which vendors are likely to have availability issues for specific flower varieties in a given week. Output: vendor risk score per flower per order window.

**AI-3: Buffer Intelligence** *(Updated)*

> **Note:** Before Phase 2 AI-powered buffers, Phase 1 should implement a simple arrangement-category buffer matrix. Rather than a flat 10% per stem, set different buffer defaults per arrangement category: arches and chuppahs get 15% (high handling), centerpieces get 10%, boutonnières get 5%. This is a static improvement that delivers value immediately without AI.

Phase 2 builds on this by learning from post-event wastage data to tune these per-category buffers dynamically. Output: recommended buffer percentage per flower per event type based on historical wastage patterns.

**AI-4: Recipe Suggestions**
When a designer starts a new arrangement for a specific event type and price point, suggest existing recipes from the library (or community templates in Phase 3) ranked by margin and client satisfaction score.

---

## 16. Mobile Experience *(Updated)*

### Priority Mobile Workflows

| Workflow | Device | Priority |
|---|---|---|
| Inventory receiving | Tablet (warehouse) | P1 |
| Event day production checklist | Phone (on-site) | P1 |
| Wastage entry | Tablet (warehouse) | P1 |
| PO status review | Phone | P2 |
| Event overview | Phone | P2 |
| Recipe Studio | Desktop | P3 (complex UI) |

### Mobile Design Principles

- Touch-optimized tap targets (minimum 44px)
- Offline-capable for inventory receiving and checklist (Service Workers)
- Print-optimized layout for production checklists
- Camera integration for receiving condition notes (Phase 2)

> **PWA-First Recommendation:** Before building native apps in Phase 3, evaluate a PWA approach (see Section 11.4). Warehouse receiving and wastage entry on tablet are the critical mobile use cases, and both work well as responsive web apps with offline support via Service Workers.

---

## 17. Testing Strategy

| Layer | Approach |
|---|---|
| Unit tests | Stem calculation engine, buffer matrix, vendor split logic |
| Integration tests | PO generation end-to-end, inventory netting |
| API tests | All endpoints with role-based access checks |
| E2E tests | Core user flows: recipe create → event build → PO generate |
| Load tests | PO generation for 50-arrangement event under concurrent users |
| Data integrity tests | DECIMAL precision for all financial calculations |

---

## 18. Deployment & Infrastructure

### Phase 1

- Docker Compose on a single VPS (DigitalOcean or Hetzner)
- Supabase for Auth and Storage (hosted)
- PostgreSQL managed instance or containerized
- Nginx reverse proxy with SSL (Let's Encrypt)
- Nightly database backups to S3-compatible storage
- Local dev: SQLite + `python run_local.py` (see Section 11.5)

### Phase 2+

- Kubernetes or managed container service (Fly.io, Railway)
- CDN for static assets
- Redis for caching vendor catalog and pricing
- Separate read replica for analytics queries

---

## 19. Open Questions

| Question | Owner | Priority |
|---|---|---|
| Will Luxel handle multi-location events (same date, different venues)? | Product | High |
| What is the desired PO numbering format? (FLW-YYYY-NNNN proposed) | Luxel | Medium |
| Should proposals support payment collection (Stripe integration)? | Product | Medium |
| Barcode/QR scanning for inventory receiving — native API required? | Engineering | High (PWA vs. native decision) |
| Will Luxel want client-facing event portals in Phase 3? | Luxel | Low |
| Recipe template marketplace — curated or open community? | Product | Low |

---

## 20. MVP vs Phase 2 vs Phase 3 *(Updated)*

### Phase 1a — True MVP (Months 1–2): Core Calculation Loop *(New)*

**Goal:** Get Luxel off spreadsheets for the single most painful workflow — stem calculation and PO generation.

| Feature | Notes |
|---|---|
| Flower catalog CRUD | |
| Vendor CRUD | |
| Recipe Studio: create, edit, publish | With stem line items |
| Automatic stem scaling | With category-aware buffer matrix |
| Event Planner: create events, assign arrangements | View totals |
| Basic margin indicator | Quoted vs. estimated cost |
| Purchase Order generation per vendor | |
| PO PDF export | |
| Single-user or minimal auth | Local SQLite |

**Phase 1a Success Criteria:**
1. At least one full event processed through the platform end-to-end
2. PO generated and manually verified against what would have been ordered
3. Stem calculation error rate below 2%

### Phase 1b — Internal Rollout (Months 3–4): Team + Inventory *(New)*

**Goal:** Expand to the full Luxel team with proper auth and inventory tracking.

| Feature | Notes |
|---|---|
| Full RBAC | Owner, Head Designer, Designer, Operations, Warehouse, Bookkeeper |
| Inventory ledger | Manual entry and receiving against PO |
| Inventory reconciliation before PO generation | |
| Post-event wastage capture | With reason codes |
| Event day / production checklist | Mobile-optimized |
| Client payment / deposit tracking | |
| Basic dashboard | Active events, pending POs, inventory alerts |
| Multi-user team collaboration with audit log | |
| Mobile-responsive warehouse receiving workflow | |
| Supabase Auth migration | Email + magic link, Row-Level Security |

### Phase 2 — Intelligence Layer (Months 5–8)

| Feature | Notes |
|---|---|
| Proposal system with PDF and client view | |
| AI buffer optimization (AI-3) | Replaces static matrix over time |
| Vendor fill rate prediction (AI-2) | |
| Demand forecasting (AI-1) | |
| Mayesh / Syndicate API integration | Live pricing |
| QuickBooks / Xero sync | |
| Recipe similarity detection (6.7) | |
| Vendor substitution workflow (6.4.3) | |
| Recipe cost alert thresholds | See Appendix C |
| Proposal expiry + reminder emails | See Appendix C |

### Phase 3 — Scale & Platform (Months 9–14)

| Feature | Notes |
|---|---|
| SaaS multi-tenant launch | Pricing tiers (Section 22) |
| Onboarding wizard | Section 23 |
| Recipe template marketplace | Community library |
| Native mobile apps (or PWA — see Section 11.4) | |
| White-label Enterprise tier | |
| Client portal | Event view, proposal acceptance |
| SSO (SAML/OIDC) | Enterprise tier |

---

## 21. Competitive Differentiation *(New)*

FloraFlow's market differentiation rests on three capabilities that no existing tool combines in a single workflow:

| Competitor | What They Do Well | What They Miss |
|---|---|---|
| Floranext | POS, proposals, client management | No stem calculation engine, no recipe versioning |
| Details Flowers | Costing and recipe building | No PO generation, no inventory tracking |
| Mayesh Marketplace | Wholesale ordering | No recipe/event layer; no margin visibility |
| Generic spreadsheets | Flexible, no learning curve | No scaling, no version control, no PO generation |

**FloraFlow's differentiation:** The only platform that connects the full chain — recipe → event build → automatic stem calculation → PO generation → inventory reconciliation → margin tracking — in a single, versioned, collaborative workflow.

The AI layer in Phase 2 reinforces this by making the calculation engine smarter with every event processed, creating a compounding advantage that spreadsheets and point-solution competitors cannot replicate.

---

## 22. SaaS Pricing Model *(New)*

FloraFlow uses **event-volume-based pricing**, not per-seat. This reflects how floral businesses scale (by event volume, not staff count) and aligns FloraFlow's revenue with client success.

| Tier | Events / Month | Price | Target Customer |
|---|---|---|---|
| Starter | Up to 10 | $79 / month | Solo florist, 1–3 staff |
| Studio | Up to 40 | $199 / month | Mid-size studio, 3–10 staff |
| Professional | Up to 100 | $399 / month | Large studio, Luxel-tier |
| Enterprise | Unlimited | Custom | Multi-location, white-label |

**All tiers include:** Unlimited recipes, full team access (all roles), PO generation, PDF exports.

**Phase 2 AI features** are included from Studio tier and above.

**Enterprise tier includes:** White-label branding, dedicated database schema, SSO (SAML/OIDC), priority support, and dedicated onboarding.

### Pricing Rationale

- A Luxel-tier studio at Professional ($399/month) saves an estimated 20+ hours/month of manual calculation time — a clear ROI even at a $40/hour internal rate
- Event-volume pricing means small studios are not over-paying for seat licenses they don't need
- Enterprise custom pricing enables white-label licensing for wholesale vendors or floral supply chains who want to offer FloraFlow to their customers

---

## 23. Onboarding & Data Import *(New)*

New tenant onboarding follows a 4-step guided wizard that gets a studio operational within one session.

### Step 1 — Studio Setup

Configure: Studio name, logo, currency, timezone, global buffer default, PO email template.

### Step 2 — Flower Catalog Import

**CSV import** for flower catalog (template provided).

Required columns: `common_name`, `variety`, `color`, `cost_per_stem`, `bunch_size`

Optional columns: `season_months`, `buffer_pct`, `photo_url`

Manual entry also supported for small catalogs. A **starter set of 50 popular wedding flowers** is pre-loaded and can be activated with one click.

### Step 3 — Vendor Setup

Add at least one vendor with name, email, and lead days. Assign preferred flowers to each vendor to populate the Vendor-Flower Preference Matrix.

### Step 4 — First Recipe

Guided creation of the first arrangement. The system walks through:
1. Naming the arrangement and selecting category
2. Adding stem line items (search flower catalog)
3. Setting quantities per base unit
4. Previewing the cost calculation
5. Publishing the recipe

### CSV Import Templates

| Template | Description |
|---|---|
| `flower_catalog_import.csv` | Full catalog import with all columns |
| `recipe_import.csv` | Optional; most studios prefer to build from scratch |

### Cold-Start Mitigation

A **public recipe template library** (Phase 3 marketplace concept) will allow new tenants to bootstrap their library from anonymized community recipes — covering common wedding arrangements such as altar arches, sweetheart table arrangements, and centerpiece configurations.

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| Recipe | A named arrangement design with a list of stem types and quantities per unit |
| Recipe Version | An immutable snapshot of a recipe at time of publish |
| Event Build | The full set of arrangements assigned to an event, organized by location |
| PO | Purchase Order sent to a wholesale vendor |
| Buffer | Additional stem percentage ordered above calculated need to account for damage and handling |
| Netting | Reducing a PO quantity by the amount already in inventory |
| Fill Rate | The percentage of a PO that a vendor fulfills as ordered |
| Wastage | Stems ordered but not used in arrangements; captured post-event |
| Base Unit | The unit a recipe is expressed in (per table, per person, per piece) |
| Stem Override | A manual adjustment to a calculated stem quantity, saved separately from the recipe |

---

## Appendix B: Sample Data Structures

### Sample Stem Calculation (Abbreviated)

```
Event: Chen-Williams Wedding (200 guests, 20 tables)
Arrangement: White Garden Rose Centerpiece (Recipe v3)
  - White Ohara Rose: 12 stems/table × 20 tables = 240 stems
  - Buffer (centerpiece, 10%): +24 stems
  - In stock: 30 stems
  - Net order: 234 stems → 24 bunches (bunch size 10)

Arrangement: Ceremony Arch (Recipe v2)
  - White Ohara Rose: 80 stems
  - Eucalyptus: 40 stems
  - Buffer (arch, 15%): +12 stems White Ohara, +6 stems Eucalyptus
  - Net order: 92 White Ohara → 10 bunches; 46 Eucalyptus → 5 bunches
```

### Sample PO Number Format

```
FLW-{YEAR}-{SEQUENCE}
e.g. FLW-2026-0847
```

### Sample Vendor Split

```
Total White Ohara Rose required: 326 stems (including buffer, less inventory)
  → Mayesh Wholesale (priority 1): 326 stems → 33 bunches @ $2.40/stem
  → Syndicate Sales (priority 2, backup): only used if Mayesh fill rate < 85%
```

---

## Appendix C: Quick Wins — Immediate Phase 1 Additions *(New)*

These three features add high value at low implementation cost and should be included in Phase 1b.

### C.1 Recipe Cost Alert Threshold

Each recipe can have an optional **maximum cost-per-unit threshold**. When ingredient price changes push the recipe cost above this threshold, the head designer and owner receive an alert.

- Prevents silent margin erosion from supplier price creep
- Threshold is set per-recipe (e.g., "alert me if this centerpiece exceeds $45/table")
- Alert delivery: in-app notification + email

### C.2 Proposal Expiry

Proposals have a configurable expiry date (default: 14 days from send date).

- Three days before expiry: client receives an automatic reminder email
- On expiry: proposal status moves to `expired`; account manager receives an in-app prompt to follow up
- Creates urgency in the sales process without requiring manual follow-up tracking

### C.3 Event Cloning / Templates

Any completed event can be saved as a named template (e.g., "Standard 100-Guest Wedding").

- Creating a new event from a template pre-fills the entire arrangement build
- Designer customizes quantities, locations, and flower selections for the specific event
- For studios with repeating event structures (e.g., corporate accounts with standard florals), this eliminates re-entry entirely
- Templates are visible to all designers; managed by Head Designer and Owner
- API: `POST /events/:id/duplicate` (see Section 12)
