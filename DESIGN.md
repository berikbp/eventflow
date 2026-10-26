---
name: EventFlow
description: Forest-and-lime event discovery and email ticket flows.
colors:
  ink: "#173c32"
  forest: "#123e33"
  lime: "#d5f58a"
  paper: "#fafbf7"
  white: "#fff"
  muted: "#58675e"
  line: "#dfe5dc"
  soft: "#f0f3eb"
  focus: "#397858"
  primary-hover: "#235745"
  secondary: "#edf1e8"
  secondary-hover: "#e1e9d8"
  lime-hover: "#c5eb72"
  error: "#a2392e"
  success: "#267045"
  confirmed-bg: "#e8f1df"
  confirmed-text: "#285f38"
  waiting-bg: "#fbefd4"
  waiting-text: "#7e5410"
  cancelled-bg: "#edf0eb"
typography:
  display:
    fontFamily: "Onest, sans-serif"
    fontSize: "3.5rem"
    fontWeight: 650
    lineHeight: 1.1
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Onest, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 650
    lineHeight: 1.16
    letterSpacing: "-0.035em"
  section:
    fontFamily: "Onest, sans-serif"
    fontSize: "2rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Onest, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Onest, sans-serif"
    fontSize: "0.875rem"
    lineHeight: 1.7
  label:
    fontFamily: "Onest, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 550
  button:
    fontFamily: "Onest, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 550
    lineHeight: 1.25
rounded:
  control: "8px"
  date: "9px"
  field: "10px"
  photo: "12px"
  surface: "16px"
  pill: "100px"
spacing:
  compact: "8px"
  control-gap: "10px"
  small: "12px"
  inset: "18px"
  medium: "22px"
  section: "24px"
  panel: "28px"
  large: "32px"
  feature: "48px"
components:
  button-primary:
    backgroundColor: "{colors.forest}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    typography: "{typography.button}"
    padding: "13px 21px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.forest}"
    rounded: "{rounded.control}"
    padding: "13px 21px"
  button-lime:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.forest}"
    rounded: "{rounded.control}"
    padding: "13px 21px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.forest}"
    rounded: "{rounded.control}"
    padding: "13px 21px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "13px 14px"
  card:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.surface}"
  status-confirmed:
    backgroundColor: "{colors.confirmed-bg}"
    textColor: "{colors.confirmed-text}"
    rounded: "{rounded.pill}"
    padding: "6px 10px"
---

# Design System: EventFlow

## Overview

**Creative North Star: "Forest-and-lime event marketplace"**

EventFlow uses the confirmed forest-and-lime event marketplace direction: warm near-white pages, deep green text, restrained borders and community imagery. Russian interface copy and compact organizer tools keep discovery approachable and operational screens readable.

The recurring date block connects event listings, detail pages and tickets. Local photographs illustrate the two seeded events; other events receive a typographic poster. Short state transitions support interaction without entrance choreography.

**Key Characteristics:**

- Forest ink and lime emphasis on warm paper.
- Onest throughout, with compact labels and balanced headings.
- Image-led discovery and a recurring day/month date block.
- Flat bordered surfaces and explicit status labels.

## Colors

Deep green provides the primary action and text hierarchy; lime adds emphasis against warm paper and white.

### Primary

- **Forest:** primary buttons, organizer callout and poster foundations.
- **Lime:** brand tile, callout action and small photo-caption action accent.

### Neutral

- **Ink:** primary text; **Muted:** supporting copy and metadata.
- **Paper:** page canvas; **White:** cards and fields; **Soft:** quiet utility surfaces.
- **Line:** dividers and surface borders; **Focus:** keyboard and field outlines.

### Status

Confirmed states pair pale green with green text. Waiting states use warm amber; cancelled states use quiet gray-green. Error text uses brick red. Labels always carry the meaning alongside color.

## Typography

**Display Font:** Onest (sans-serif fallback).
**Body Font:** Onest (sans-serif fallback).

The locally hosted variable font gives headings a compact, rounded character. Negative heading tracking and medium-to-semibold weights provide hierarchy without a second display face.

### Hierarchy

- **Display:** discovery heading; reduces to 2.8rem below 1000px, 2.6rem below 760px and 2.35rem below 480px.
- **Headline / Section / Title:** shared heading foundations; event-card titles use 1.35rem with a 1.35 line height on desktop.
- **Body:** compact event previews and forms; longer descriptions use 0.9375rem, a 1.85 line height and a 70ch maximum.
- **Label:** form labels and metadata. Status pills use 0.6875rem, with larger variants for prominent states.
- **Date and ticket codes:** tabular numerals; date days use 1.65rem and weight 650. Ticket codes wrap and use Onest, not a separate monospace face.

**The Date Continuity Rule.** Carry the same day/month block from discovery to detail to ticket; derive its content from the event date.

## Layout

The shared shell has a 1200px maximum and 32px side gutters. Gutters reduce to 20px below 760px and 16px below 480px; the supported minimum viewport is 320px. Main content uses 42px top and 72px bottom padding by default. Narrow working pages cap at 820px.

Discovery uses a split hero, a search/date toolbar and two event columns. The hero and toolbar stack below 760px; event cards become one column below 480px. Working panels use compact labels and 22–28px padding rather than discovery-scale whitespace. Detail pages stack below 760px and expose a registration jump link; final source order keeps content before registration.

The participant table becomes labeled records below 600px: email and status span the record, followed by queue and check-in values in two columns. Headers remain available to assistive technology. Below 480px authenticated header actions wrap onto a full-width second line. Secondary desktop navigation hides below 760px while the organizer action remains visible.

## Elevation & Depth

Surfaces stay flat: pale tonal backgrounds, fine borders and photograph crops establish depth. Event-card hover changes its border rather than lifting the card. Photo-caption text alone has a soft readability shadow (`0 2px 12px #102b23`).

**The Flat Surface Rule.** Separate working surfaces with pale fills and fine borders; reserve text shadow for the photograph caption.

## Shapes

Large surfaces use gently rounded corners; controls use a tighter radius. Date blocks have their own compact rounded rectangle, status chips are pill-shaped, and step markers are circles. Event cards clip their photographs to the outer surface. Tickets use a dashed divider between event information and the code area.

## Components

### Buttons

Forest primary buttons use white text; lime buttons provide emphasis on dark green callouts. Secondary buttons use pale green and a subtle border; ghost buttons retain a transparent fill and line border. Standard controls have a 48px minimum height; compact header and organizer variants reduce to 40–42px. Primary hover deepens the fill. Focus-visible uses a 3px focus outline offset by 4px; disabled controls have half opacity and a not-allowed cursor.

### Chips

Status pills are compact text labels with semantic background/text pairs. Confirmed, waiting and cancelled states share the same silhouette and differ in tone and wording.

### Cards / Containers

White event cards and working panels share the surface radius and line border. Cards use 22px internal content padding; panels use 28px by default. Card titles underline on hover and card borders strengthen on hover. Empty states use a soft fill and centered content.

### Inputs / Fields

White fields use a pale green stroke, control radius, 48px minimum height and 13px by 14px padding. Labels sit above fields. Focus uses a 2px outline with 2px offset. Search/date wrappers use a slightly wider radius and focus-within outline. Textareas resize vertically. Errors remain explicit text.

### Navigation

The header combines brand, public navigation and organizer action. Desktop links use muted text with forest hover/active color. Organizer workspace links form a separate working navigation. Footer links use pale green on forest. Skip navigation becomes visible on focus.

### Date Block and Ticket

The date block stacks a large zero-padded day over the localized abbreviated month. It appears over event imagery, beside organizer rows and in the ticket. The ticket carries pale green branding, event details, explicit status and a wrapping code beneath a dashed perforation line.

### Motion

Buttons and event borders transition over 0.18s. Anchor scrolling is smooth. Reduced-motion preference removes transitions and animations and restores immediate scrolling; there is no entrance choreography.

## Do's and Don'ts

### Do:

- Do use the shared forest, paper and lime palette and Onest type family.
- Do preserve visible focus indicators and reduced-motion behavior.
- Do label participant values on small screens and allow long emails and ticket codes to wrap.
- Do keep event imagery illustrative and status values grounded in actual event data.

### Don't:

- Don't present illustrative photographs as evidence of a particular event.
- Don't introduce account, payment, venue or rating cues unsupported by the product.
- Don't replace explicit ticket and queue labels with color alone.
