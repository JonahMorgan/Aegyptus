# Temporal Evolution of Alternative Forms - Example

This document illustrates how the updated v2 network builder now handles alternative forms with temporal information.

## Before (v2 without temporal logic):

All alternative forms were connected to the main lemma as simple `VARIANT` edges, ignoring temporal information:

```
Main Lemma (undated)
    ├─ VARIANT → Alt Form 1 (Old Kingdom)
    ├─ VARIANT → Alt Form 2 (Middle Kingdom)  
    └─ VARIANT → Alt Form 3 (New Kingdom)
```

## After (v2 with temporal logic - like v1):

Alternative forms are now organized chronologically with appropriate edge types:

```
Main Lemma (undated)
    └─ EVOLVES → Alt Form 1 (Old Kingdom) [First attestation]
                     └─ EVOLVES → Alt Form 2 (Middle Kingdom) [Evolution]
                                      └─ EVOLVES → Alt Form 3 (New Kingdom) [Evolution]
```

### With Multiple Forms in Same Period:

```
Main Lemma (undated)
    └─ EVOLVES → Alt Form 1a (Old Kingdom) [First attestation]
                     ├─ VARIANT → Alt Form 1b (Old Kingdom) [Same period variant]
                     └─ EVOLVES → Alt Form 2 (Middle Kingdom) [Evolution]
```

## Key Changes to v2:

1. **Period Ranking System**: Added `get_period_rank()` method that assigns chronological order to periods
   - Predynastic = 0
   - Early Dynastic = 1
   - Old Kingdom = 2
   - ... up to Roman = 10
   - Dynasty numbers (1st-31st) are also mapped
   - Undated = 999

2. **Temporal Grouping**: Alternative forms are grouped by their period rank

3. **Edge Type Selection**:
   - **EVOLVES**: Used for chronological progression between different time periods
   - **VARIANT**: Used for synchronic variation within the same time period

4. **Chain Building**: Forms are connected in chronological order, creating evolutionary chains

## Example Use Case:

For an Egyptian word with attestations across multiple periods:

**Word**: *ḥtp* (to be satisfied, at peace)
- Main form (undated hieroglyphs)
- Old Kingdom variant (specific hieroglyphic writing)
- Middle Kingdom variant (different hieroglyphic writing)
- New Kingdom variant (yet another writing)

The network now shows:
- How the hieroglyphic spelling evolved over ~2000 years
- Which forms are contemporary variants vs. temporal evolutions
- The chronological sequence of attestations

This enables training models that understand both:
- **Diachronic change**: How words evolved over time
- **Synchronic variation**: How words varied within the same period
