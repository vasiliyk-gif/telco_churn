# Run notes

One line per run: what you changed, what you expected, what happened.

| Run | What is different | My prediction | Score | Profit per 1,000 (mean ± std) | Real or noise? What I learned |
|-----|-------------------|---------------|-------|-------------------------------|-------------------------------|
| run1 | profit fitness, 7 genes (LR / XGBoost, class weight, `pdays` flag); pop 10, stopped at gen 20 (no gain after gen 9) | Not written down before the run. | 0.251 | €1,698 ± 248 (LR baseline €1,489 ± 231) | Champion: XGBoost, depth 6, 152 trees, learning rate 0.019, `pdays` flag on, no class weight; calls 13.0%. +€209 over LR, below the €300 target (€1,790). Wins 4 of 5 folds (+225, −56, +244, +575, +56): uneven, most of the gain is fold 3, so partly noise. `xgb_max_depth` hit its upper bound (6): widen it in run3. |
| run2 | F1 fitness, same chromosome | F1 at 0.5 rewards predicting "yes" often enough, so the champion will use `class_weight_balanced = true` (without it, few clients reach 0.5 when 11% subscribe). Its ranking is tuned for F1, not for the top of the list, so it will make less money than run1 (below €1,698 per 1,000), probably close to the LR baseline. | F1 0.309 (not comparable with run1's profit score) | €1,544 ± 204 | Champion: logistic regression, C = 0.029 (strong regularization), no class weight, `pdays` flag on (its `xgb_*` genes are unused); calls 18.0%; stopped at gen 14. €154 per 1,000 less than run1, and run1 wins all 5 folds (−163, −19, −138, −369, −81): real, not noise. Only €55 above the LR baseline. Prediction half right: less money, near the baseline; but no class weight. Without it the `poutcome = success` clients (67%) already pass 0.5, which gives F1 ≈ 0.31 by high precision and low recall. |
| run3 | | | | | |

## Profit fitness vs F1 fitness (Step 7)
- **More money on the validation folds:** run1 (profit fitness), €1,698 vs €1,544 per 1,000, winning all 5 folds.
- **Why the F1 champion differs:** F1 at threshold 0.5 looks only at clients above 50% probability, mostly the small `poutcome = success` group (~3–4%). The money is made further down the ranking: the call list goes to the top 13–18%, where probabilities are ~14–30%, and F1 never looks there. F1 also ignores the costs (a missed subscriber loses €60, a wasted call €10). So the F1 search picked a heavily regularized logistic regression that is good at the 0.5 cut-off but ranks the rest of the list worse; the profit rule then calls more clients (18% vs 13%) for less money. The metric the search optimizes decides which model wins.
