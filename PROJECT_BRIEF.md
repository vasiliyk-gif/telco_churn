# Project brief — Instant offers on Ames homes (Lab 2)

## Background

It is early 2010 in Ames, Iowa. A new **iBuyer** company buys homes for cash, fast: it looks at a
listed home, makes an instant offer, and if the seller accepts, it buys the home and resells it on the
open market. Sellers accept a lower price in exchange for speed and certainty. The company earns the
gap between the resale price and its offer, minus its costs.

The danger is the **winner's curse**: sellers happily accept offers that are too high, and refuse the
ones that are too low. A company whose price model overvalues homes buys exactly the wrong ones. (A
real iBuyer, Zillow Offers, closed in 2021 after losing hundreds of millions this way.)

## The decision

For every home listed in 2010: **offer or not, and at what price.**

## Business question

> What offers should we make on the 2010 listings to make the most money without taking on big losses,
> and how much better is that than the classic approach (the most accurate price model plus one flat
> margin)?

## The market rule (fixed for everyone)

Teaching assumptions, not real market figures. The code is in `earth/ibuyer_market.py`.

| Item | Value | Meaning |
|------|-------|---------|
| Offer | `predicted value × (1 − margin)` | You choose the value model and the margin policy |
| Seller flexibility | uniform between **2% and 20%** | A seller accepts if `offer ≥ (1 − flex) × true value` |
| Resale | **true value − 5%** | Fees and holding costs |
| Largest offer | **$500,000** | Company rule |

So an accepted home makes `0.95 × true value − offer`, which is negative when you offered more than 95%
of its value. Because flexibility is uniform, the **chance** a seller accepts is known exactly, and the
fitness uses expected values: no dice.

**Risk-adjusted profit** = expected profit − 0.5 × |expected losses| (losing deals count extra: the
company's investors hate them). It is reported per listing.

## Data

The Ames Housing data (De Cock, 2011): every home sold in Ames from 2006 to mid-2010, with about 80
columns describing it (size, quality, age, location, basement, garage...). Column guide:
`data/data_dictionary.md`.

| File | Rows | What you have |
|------|------|---------------|
| `data/ames_history.csv` | 2,589 sales, 2006–2009 | Features **and** `SalePrice` (the true value) |
| `data/ames_2010_listings.csv` | 341 homes listed in 2010 | Features and `ListingID`, **no price** |

The 2010 sale prices are held by the teacher until the end of the lab. Then you score your own offers on
what the homes really sold for, once. (The Ames data is public. Looking up 2010 prices defeats the point: please don't.)

## Target and unit

One row is one home. The value model predicts `SalePrice`. The decision is per listing.

## What you will decide

1. **Feature boundary.** Which columns are known when a home is listed? (Look at `Sale Type`,
   `Sale Condition`, `Mo Sold`, `Yr Sold`.)
2. **Evaluation.** The fitness tests a candidate on three past years: train on the years before Y,
   offer on Y, for Y = 2007, 2008, 2009. Why years, and not a random split?
3. **The policy.** What should a margin depend on? One flat number, or more?
4. **Success.** How much risk-adjusted profit per listing above the classic baseline would convince you?

## Out of scope

Renovations, mortgage costs, how long a resale takes, and negotiation after the offer.
