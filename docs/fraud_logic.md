# Fraud Injection Logic

## Fraud Rate
- Default fraud injection rate: 3%

## Fraud Types
- none
- velocity
- geo
- merchant
- amount

## Design
Each card has a normal behavioral profile:
- home geography
- usual merchant categories
- typical amount range
- common transaction channel
- normal activity hours

Most transactions follow the profile.
Fraud transactions intentionally violate one dimension of that profile.

## Fraud Patterns

### velocity
Multiple transactions on the same card within a short time window.

### geo
Transaction location is inconsistent with the card's historical geography.

### merchant
Merchant category is not part of the card's normal pattern.

### amount
Transaction amount is much larger than the card's normal range.