# Framing (Steps 1–2)

## Business question (your words)

For each home listed in Ames in 2010, should we make an instant cash offer, and at what price, so that
the company earns the most risk-adjusted profit? And does a price model and pricing policy evolved
together by Earth beat the classic approach (the most accurate price model plus one flat margin) on
those same homes?

## The decision

Per listing, two things: **offer or not**, and **the offer price** = predicted value × (1 − margin),
never above $500,000 (an offer above the cap is not made). We control the value model and the margin
policy; the seller controls acceptance, and we only know the chance they accept, not the outcome.

## The money: when does one purchase make or lose money?

An accepted home is resold at 95% of its true value, so one purchase makes `0.95 × true value − offer`:

- **Offer ≤ 80% of true value:** no seller accepts. No deal, no money (a missed opportunity, not a loss).
- **Offer between 80% and 95%:** some sellers accept, and every accepted deal makes money. Lower offers
  earn more per deal but are accepted less often. At 90%: 56% chance of acceptance, +5% of value per
  deal, about +2.8% of value expected.
- **Offer above 95%:** sellers accept very often (always from 98%), and every deal loses money. At 97%:
  94% chance of acceptance, −2% per deal.

The model's error decides where an offer falls in that range. A home that the model overvalues by 10%
gets an offer near the true value, which the seller accepts and we lose on: the **winner's curse**. A
home it undervalues gets an offer the seller refuses, which costs nothing. So errors are lopsided:
overvaluing loses money, undervaluing only loses deals.

## Why losses count extra (risk-adjusted profit)

Risk-adjusted profit = expected profit − 0.5 × |expected losses|, so every dollar lost counts as $1.50.

- Investors judge the company on losses: a few large losing purchases make the model look broken even
  when total profit is positive (Zillow Offers closed for this reason).
- Losses tie up capital: a home we overpaid for still has to be held and resold.
- It rewards a policy that is careful where the model is unsure, not only one that is right on average.
  Two policies with the same profit are not equal if one gets there through big wins and big losses.

## Success, as numbers (vs the classic baseline, on the 2010 listings)

Measured once, on the 2010 listings with the real 2010 prices, using the same market rule for both:

1. **Risk-adjusted profit at least $1,000 per listing above the classic baseline** (about $340,000 over
   the 341 listings).
2. **Expected losses no larger than the classic baseline's.** A higher profit that comes from more
   losing deals does not count as a win.

Why $1,000: a good offer earns roughly 5% of a ~$180k home on about half the listings, so a policy
makes at most a few thousand dollars per listing. $1,000 is a large share of that, enough that a gain
is not just noise from one year's 341 homes, and enough to pay for building and running a more complex
policy. If the gain is positive but smaller, the verdict is "better, but not proven". (To be checked
against the baseline numbers in Step 3, before the search.)

## Feature boundary (Step 2): columns left out, with a reason each

The offer is made when a home is listed, before any sale. Every column that is only known once the sale
closes is left out of the value model and the policy. (Evidence: `work/exploration/eda.ipynb`.)

| Column | Decision | Reason |
|--------|----------|--------|
| `Sale Condition` | Drop | It describes how the sale ended: a foreclosure or short sale (`Abnorml`, median $131k), a new home sold before completion (`Partial`, $249k), a family sale. It is the outcome of the deal, not a fact about the house, and it is not in the 2010 listings. Keeping it would let the model learn from the answer. |
| `Sale Type` | Drop | The kind of deed or contract (`WD`, `New`, `COD`, contract terms). It is set when the sale is signed, and it is not in the 2010 listings. |
| `Mo Sold` | Drop | The month the sale **closed**, not the month the home was listed: we would not know it when we make the offer. It also carries almost no signal (monthly medians $152k–$177k, no season pattern). |
| `Yr Sold` | Drop as a feature; keep for the folds | We know the year at offer time, but every 2010 listing has the same value, one the model never saw in training: a tree model treats it as 2009 and a linear model extrapolates a trend that is not there (medians were flat at $160–165k from 2006 to 2009). It is used only to build the past-year folds. |
| `Order`, `PID`, `ListingID` | Drop | Row and parcel identifiers: no information about value. |

Kept: every other column describes the house and its lot, which is known from the listing. `NA` in
basement, garage, pool and similar columns means "none", so it stays as a category.

