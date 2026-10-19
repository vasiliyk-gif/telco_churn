# Hints (support track)

Starting points, not answers: you still make the decisions.

## Step 2 — EDA questions for your agent

- Median `SalePrice` by `Yr Sold`. Do prices rise or fall from 2006 to 2009? What could that mean for
  2010?
- Median price and the spread (10th–90th percentile) by `Overall Qual` and by decade of `Year Built`.
  Where is a price model likely to be least sure?
- How many homes have `Gr Liv Area` above 4,000 sq ft, and what did they sell for?
- `Sale Condition` by year: how many foreclosures (`Abnorml`)? Is that known when a home is listed?

## Step 3 — reading the baseline

`classic_baseline.py` prints the RMSE of each value model and the risk-adjusted profit per listing for
each flat margin. Look at the curve: a low margin buys many homes and loses on the overvalued ones, a
high margin buys few homes and leaves money on the table. The best flat margin is the classic answer.

Questions for Gate 3: on which homes does the classic model make its biggest errors (old? cheap? large?
unusual neighbourhoods)? Should the margin be the same on those homes?

## Step 5 — the valuation block of `chromosome.yaml`

The skeleton's `Valuer` reads these genes. Copy them under `content:`, and change ranges if you want:

```yaml
# iBuyer on Ames: the valuation pipeline and the pricing policy evolve together.
chromosome:
  type: dict
  generation:
    type: per_item
    non_required_probability: 0
  mutation:
    type: random
    percentage_to_mutate: 0.15
    max_percentage_to_mutate: 0.25
    num_items_to_mutate: 2
    max_num_items_to_mutate: 3
    drift_factor: 1.1
  crossover:
    type: per_item_crossover
    per_item_select_strategy: random
  content:
    w_xgb:
      type: float
      min_value: 0.0
      max_value: 1.0
      generation: { type: uniform }
      mutation: { percentage_change: 0.2 }
      crossover: { type: random }
    ridge_alpha:
      type: float
      min_value: 0.3
      max_value: 100.0
      generation: { type: uniform }
      mutation: { percentage_change: 0.3 }
      crossover: { type: random }
    quantile_alpha:
      type: float
      min_value: 0.15
      max_value: 0.5
      generation: { type: uniform }
      mutation: { percentage_change: 0.2 }
      crossover: { type: random }
    log_price:
      type: bool
    drop_big_houses:
      type: bool
    use_quantile:
      type: bool
    use_age:
      type: bool
    use_location:
      type: bool
    use_basement_garage:
      type: bool
    use_extras:
      type: bool
    xgb:
      type: dict
      generation: { type: per_item, non_required_probability: 0 }
      mutation: { type: random, percentage_to_mutate: 0.3 }
      crossover: { type: per_item_crossover }
      content:
        n_estimators:
          type: int
          min_value: 200
          max_value: 800
          generation: { type: uniform }
          mutation: { step_size: 50, percentage_change: 0.2 }
          crossover: { type: random }
        max_depth:
          type: int
          min_value: 2
          max_value: 6
          generation: { type: uniform }
          mutation: { step_size: 1, percentage_change: 0.2 }
          crossover: { type: random }
        learning_rate:
          type: float
          min_value: 0.02
          max_value: 0.15
          generation: { type: uniform }
          mutation: { percentage_change: 0.2 }
          crossover: { type: random }
        subsample:
          type: float
          min_value: 0.6
          max_value: 1.0
          generation: { type: uniform }
          mutation: { percentage_change: 0.1 }
          crossover: { type: random }
        colsample_bytree:
          type: float
          min_value: 0.4
          max_value: 1.0
          generation: { type: uniform }
          mutation: { percentage_change: 0.1 }
          crossover: { type: random }
```

## Step 5 — a first policy (the classic one, as a gene)

```yaml
    policy:
      type: dict
      generation: { type: per_item, non_required_probability: 0 }
      mutation: { type: random, percentage_to_mutate: 0.3 }
      crossover: { type: per_item_crossover }
      content:
        base_margin:
          type: float
          min_value: 0.0
          max_value: 0.3
          generation: { type: uniform }
          mutation: { percentage_change: 0.2 }
          crossover: { type: random }
```

```python
def offer_prices(policy, value, ridge, xgb, x):
    margin = np.full(len(value), policy["base_margin"])
    offer = value * (1 - margin)
    make = np.ones(len(value), dtype=bool)
    return offer, make
```

That reproduces the classic policy, with the price model also evolving. Now make it smarter, one gene
at a time, each with a reason. Patterns that work with numpy:

```python
disagree = np.abs(xgb - ridge) / value                  # 0.05 = the two models differ by 5%
margin = margin + policy["k_disagree"] * disagree        # pay less when unsure
built = x["Year Built"].to_numpy()
margin = margin + np.where(built < 1950, policy["adj_age_old"], 0.0)
make = make & (disagree <= policy["abstain_disagree"])  # no offer when very unsure
```

Keep segment adjustments small (for example −0.08 to +0.08), so the search does not waste time on
policies that never buy or always lose.

## Step 5 — the score

`risk_adj` is dollars per listing and can be negative. A linear map that puts break-even at 0.5 and
keeps most candidates between 0 and 1 works: `score = (risk_adj + 3000) / 6000`. The skeleton already
floors the result at 1e-9.

## Step 7 — re-scoring with one gene changed

```python
import importlib.util, json
spec = importlib.util.spec_from_file_location("fit", "work/optimization/fitness.py")
fit = importlib.util.module_from_spec(spec); spec.loader.exec_module(fit)
F = fit.FitnessClass("work/exploration")
genes = json.load(open("work/runs/run1/champion_chromosome.json"))["chromosome"]
print(F.calculate_fitness(genes).scalars)
genes["policy"]["k_disagree"] = 0.0          # switch one idea off
print(F.calculate_fitness(genes).scalars)
```
