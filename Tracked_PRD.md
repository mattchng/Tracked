# Tracked PRD

| | |
|---|---|
| Author | Matthew Cheng |
| Status | Draft, V1 in development |
| Target release | End of June 2026 |
| Last updated | May 20, 2026 |

## 1. Objective

Build a web app that shows NYC subway riders what the system is actually doing right now: which trains are running, where they are, what's delayed, what's rerouted.

The MTA publishes accurate real-time data publicly. Google Maps leans on the schedule, the official MTA app shows it as a list, and Citymapper buries it inside a routing flow. Nobody leads with a live map. That's the gap.

Two pain moments drive the product:
1. Standing on a platform when a train doesn't come when it said it would
2. Knowing something is wrong but not knowing what

Both are about being in the middle of a trip, not planning one. That's the wedge.

This is a portfolio project, not a commercial launch. V1 success means a deployed, working app that proves the framing.

## 2. Release

| Release | Target | Scope |
|---|---|---|
| V1 | End of June 2026 | Lex Ave (4/5/6) only. Live train map, station arrivals, service alerts. |
| V2 | Post-V1 | More lines, mobile layout, AI alert summaries. |
| V3 | TBD | Reliability scoring, saved routes, push notifications. |

Only V1 is specified in detail below.

## 3. Features

### F1. Live train positions on the map

As a rider, I want to see every active 4/5/6 train on a map so I can tell what the system is doing.

Acceptance criteria:
- 4/5/6 lines drawn as polylines in MTA green (#00933C)
- Active trains appear as dots within 30 seconds of the MTA feed update
- Dots show direction (north or south) via icon or color
- Positions come from the train's current or next stop coordinates, since the feed has no GPS
- Dots animate along the line geometry between updates, not in straight lines
- Trains with no assigned stop don't render

Priority: P0. This is the product.

### F2. Click a station to see next arrivals

As a rider, I want to click a station to see what's coming, so I can decide whether to wait or switch lines.

Acceptance criteria:
- Stations render as clickable markers
- Click opens a side panel with the next 6 arrivals
- Each arrival shows line, direction, ETA, and a delay flag if more than 2 min off schedule
- Panel closes on outside click or Escape
- Empty state handled

Priority: P0.

### F3. Active service alerts panel

As a rider, I want to see what disruptions are live, so I know what's happening when my train is late.

Acceptance criteria:
- Sidebar lists every active alert scoped to 4/5/6
- Each alert shows affected line, summary, and effective time
- Refreshes every 30 seconds
- Empty state ("system running normally") handled

Priority: P0.

### F4. Auto-refresh with freshness indicator

As a rider, I want to trust that what I'm seeing is current.

Acceptance criteria:
- Frontend polls backend every 30 seconds
- "Last updated X ago" timestamp visible
- Timestamp turns red and shows "data may be stale" if no fresh data in 2+ minutes

Priority: P0. Trust is the product.

### F5. Desktop layout

Acceptance criteria:
- Works on Chrome, Safari, Firefox at 1280px+
- No horizontal scroll
- Panels don't cover key map areas
- Mobile out of scope for V1

Priority: P1.

## 4. Design

Dark mode, map-centric, minimal chrome. The map is the product.

```
┌────────────────────────────────────────────────────────────┐
│  Tracked                              Last updated: 0:12   │
│                                                            │
│                                          ┌──────────────┐  │
│                                          │  Alerts      │  │
│      [Dark map of Manhattan + Bronx,     │              │  │
│       4/5/6 in green, animated dots]     │  4 rerouted  │  │
│                                          │  6 delayed   │  │
│                                          └──────────────┘  │
│                                                            │
│  ┌─ Station panel ──────────────────────────────────┐      │
│  │  86 St                                            │      │
│  │  4 N · 2 min   6 S · 4 min   5 N · 6 min (late)   │      │
│  └───────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────┘
```

Looking at: Linear (dark mode density), Citymapper (color), Flighty (info hierarchy). Explicitly not looking at: MTA app or Google Maps. Different category.

Interactions:
- Pan and zoom (Leaflet defaults)
- Click station, panel opens
- Click out or Escape, panel closes
- Hover train, tooltip with ID, direction, last update
- Alerts panel always visible, scrolls internally

Wireframes not done yet. Lo-fi sketches before frontend work starts.

## 5. Open questions

1. **Train direction.** Color, shape, or motion vector? Color is simplest. Motion is intuitive but breaks for stopped trains. Decide before F1.

2. **Alert severity.** MTA gives cause and effect, no tier. Either invent a tier or show alerts flat. Leaning flat with an icon for V1.

3. **Manual refresh button.** 30s polling matches feed cadence but might feel slow on bad connections. Hold off until V1 testing.

4. **Stop coordinates source.** Using nyct-gtfs's bundled station table. Convenient but tied to library updates. Could load NYC Open Data GeoJSON directly. Fine for V1.

5. **Demo format.** Live URL is necessary but probably not enough for portfolio use. A 60-second Loom is probably the real deliverable.

## 6. Not doing

| Cut | Why | Future |
|---|---|---|
| Trip routing | Different product. Google Maps and Citymapper already do this. Routing dilutes the wedge. | Never. This is the differentiation. |
| Other subway lines | Smaller V1 surface. One feed, one set of geometries. | V2: full IRT, then BMT/IND. |
| Bus, ferry, commuter rail | Different feeds, different UX. | V3+ if ever. |
| Accounts and logins | No personalization needed for V1. | V2 if engagement justifies. |
| Mobile-native app | Web reaches users without app store friction. | V2 if web traction justifies. |
| Historical delay analytics | Needs a storage layer and weeks of data. | V3 as a reliability score. |
| AI alert summaries | Layer on top of raw feed. Raw alerts are usable. | V2 quick add. |
| Push notifications | Needs service workers, permissions, saved routes. | V3. |

---

## Appendix A. Architecture

Backend:
- Python 3.11 + FastAPI
- nyct-gtfs for feed parsing
- In-memory cache, 30s TTL
- Deployed to Railway or Fly.io free tier
- Endpoints (planned): `GET /trains/lex`, `GET /stations/{id}/arrivals`, `GET /alerts`

Frontend:
- Next.js (App Router) + TypeScript
- Tailwind, shadcn/ui for panels
- Leaflet + Carto dark basemap
- Framer Motion for train animation
- Polling via SWR or TanStack Query
- Deployed to Vercel

**Discovered during Day 1 build:** The MTA GTFS-RT feed has no GPS coordinates. Trains are stop-based, with status (STOPPED_AT or IN_TRANSIT_TO) and a stop_id. Lat/lon comes from looking up the stop in the bundled MTA station table. This is how every NYC subway tracker works.

Why split frontend and backend:
1. MTA feed has no CORS headers, browser fetches fail
2. One backend pull serves many clients
3. Protobuf parsing is Python-only via nyct-gtfs

## Appendix B. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Animation feels janky | Medium | High | Dedicated polish day. Interpolate along line geometry. |
| MTA feed outage during demo | Low | High | Cache last good response, show staleness. |
| Railway cold-start lag | Medium | Medium | Free uptime pinger keeps service warm. |
| Solo capacity insufficient for V1 | Medium | High | Scope is tight. V2 deferred. |
| Dismissed as "already exists" | High | Medium | PRD framing puts situational awareness vs. navigation up front. |

## Appendix C. Discovery

User research: n=1, structured rank-ordering of 6 pain moments. Top two were both in-trip (platform waiting, "something is wrong"). Planning ranked lower. n=1 is real and acknowledged. External validation deferred to post-V1.

Competitive scan (5 products): Google Maps and MTA app dominate by volume. Citymapper and Transit own routing UX. realtimerail.nyc is the closest live tool but presents a station list, not a map. No one leads with system view.

Wedge: situational awareness, not navigation. Tracked is not a routing app. It fills a category (consumer transit observability) that doesn't have a dedicated product.
