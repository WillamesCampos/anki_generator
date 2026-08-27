## ADDED Requirements

### Requirement: The layout does not break horizontally at tablet width
The system SHALL apply a breakpoint around ~1024px so that the sidebar, Home grid, and forms render without horizontal overflow or broken layout at tablet viewport widths.

#### Scenario: Sidebar auto-collapses below the breakpoint
- **WHEN** the viewport width crosses below ~1024px and the user has no manually-saved sidebar preference
- **THEN** the sidebar automatically collapses to its icon-only state (the same state already reachable via the manual toggle)

#### Scenario: Manual sidebar preference takes precedence
- **WHEN** the user has manually expanded or collapsed the sidebar (saved in `localStorage`)
- **THEN** that preference is respected regardless of viewport width, not overridden by the automatic breakpoint behavior

#### Scenario: Forms and grid do not overflow at tablet width
- **WHEN** the Home page or login form is viewed at a tablet viewport width
- **THEN** no element causes horizontal scrolling or visually breaks the layout

### Requirement: Mobile-specific navigation is explicitly out of scope
The system SHALL NOT require a mobile-specific navigation pattern (drawer, bottom bar) as part of this change — only tablet-and-above breakpoints are addressed.

#### Scenario: Phone-width viewport is not a target
- **WHEN** the viewport is phone-sized
- **THEN** no specific navigation redesign is expected from this change; only the same tablet-oriented adjustments apply
