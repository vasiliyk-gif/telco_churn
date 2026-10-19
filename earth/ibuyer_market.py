"""The iBuyer market rule for Lab 2. Fixed for everyone; never a gene.

A seller accepts an offer when  offer >= (1 - flex) x true value,  with flex ~ Uniform(2%, 20%)
(how far below value a seller will go for a fast, certain sale). An accepted home is resold at its
true value minus 5% costs. The company never offers above $500,000. Because flex is uniform, the chance of acceptance is exact: no dice.

The same rule is copied into earth/fitness_skeleton.py (Earth uploads the fitness as one file).
"""
import numpy as np

COST = 0.05            # resale fees and holding costs, as a share of the true value
FLEX = (0.02, 0.20)    # seller flexibility range
RISK_WEIGHT = 0.5      # losses count once in profit and again at this weight in the risk-adjusted profit
MAX_OFFER = 500_000    # company rule: never offer more than this on one home


def expected_outcome(offer: np.ndarray, make: np.ndarray, value: np.ndarray) -> dict:
    """Expected result of offering `offer` on the homes where `make` is True. `value` is the true value."""
    make = make & (offer <= MAX_OFFER)
    p_accept = np.clip((FLEX[1] - (1 - offer / value)) / (FLEX[1] - FLEX[0]), 0, 1) * make
    gain = value * (1 - COST) - offer
    profit = float((p_accept * gain).sum())
    losses = float((p_accept * np.minimum(gain, 0)).sum())
    return {"profit": profit, "losses": losses, "risk_adj": profit + RISK_WEIGHT * losses,
            "bought": float(p_accept.sum()), "offers_made": int(np.sum(make))}
