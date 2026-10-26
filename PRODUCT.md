# EventFlow

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Visitors discover events and reserve a limited place by email. Organizers create
events, manage participants and waiting lists, and check tickets at the entrance.
The project is a MadDevs Junior Agentic Developer assignment and runs locally.

## Product Purpose

Make finding an event and receiving a valid ticket straightforward while preventing
overbooking. A confirmed event registration is required to receive a ticket;
creating a separate user account is not required in the existing, user-approved scope.

## Operating Context

React/TypeScript/Vite frontend, FastAPI backend, PostgreSQL, local Mailpit and an
outbox worker. Real-time updates use SSE with fallback polling. Users may open two
tabs. Public event browsing is anonymous; organizer mutations require a bearer token.

## Capabilities and Constraints

Events have title, description, date/time and capacity. Email registration,
FIFO waiting list, cancellation/promotion, tickets and single-use check-in work.
Personal management links carry a secret in their fragment. Email delivers the ticket,
not the management secret. No payments, event venues, city inventory, user accounts,
email verification or account recovery exist. Do not invent these capabilities.
Current UI language is Russian. This redesign preserves the existing Russian and
email-only behavior; creating user accounts is outside the requested visual redesign.

## Brand Commitments

Name: EventFlow. The user explicitly rejects the old sparse interface and requests
familiar event-platform UX alongside AllEvents and Ticketon, with the attached
Veltro screenshot as a visual reference. Preserve working business behavior.
This is authorization for a complete visual redesign, not a refinement of the old theme.

## Evidence on Hand

Existing API data, two synthetic demo events from app.seed, verified concurrency
and browser tests, and docs documenting the actual development process. No commercial
attendance figures, customer testimonials, prices, venues or event photos are supplied.
Stock imagery may illustrate community participation; never present it as documentary
proof of a particular event. Source details belong in asset provenance.

## Product Principles

- Browsing is immediate; ticket actions explain event registration versus account creation.
- Visible event dates, availability and statuses come from the backend.
- Every displayed filter, link and button performs a real action.
- Public attendance flows and organizer operations have clear navigation boundaries.
- Protect personal links and keep concurrency guarantees intact.
