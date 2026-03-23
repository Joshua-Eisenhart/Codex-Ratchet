# Loop Shape

## Decision modes

For every candidate path, decide exactly one:
- `KEEP_ACTIVE`
- `MOVE_TO_ARCHIVE`
- `MOVE_TO_QUARANTINE`
- `BLOCKED_REQUIRES_PREP`

## Good loop shape

1. inspect only allowlisted paths
2. classify candidates exactly
3. move only clearly safe exact candidates
4. emit a report
5. stop

## Bad loop shape

- delete in place
- “bonus cleanup”
- broad temp sweeping
- touching mixed path trees without prep
- chaining multiple cleanup waves automatically

## Required report fields

- moved items
- source paths
- destination paths
- blocked items
- reasons
- items intentionally kept

