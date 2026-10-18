# Framing (Step 1)

## Business question (your words)
Which clients should the bank call in the next term-deposit campaign to make the most profit, and how much more profit is that than calling everyone on the list or calling only clients whose previous campaign succeeded?

## The decision
Before the campaign starts, each client on the list is either called or not called. the model ranks clients by how likely they are to subscribe - the call list is the top share of that ranking. The offer, timing and agent are out of scope.


## Target and positive class
`y`: did the cleint subscribe to a term deposit after the campaign call? Positive class: `y == "yes"` ~11% of contacts

## Unit of analysis
1 row is 1 campaign contact with 1 client: the client's profile, the contact history, and the economic context at that time. The same client may appear in more than 1 row (several contacts), so rows are not fully indepenedent

## Money and break-even
- Cost per call: 10 Euros. value per subscription: 70 Euros
- A call pays off only if the client's chance to subscribe is above 10/70 = 14.3%.
- The base rate is ~11.3%

## Success, as numbers
 On the test set, scored once, the champion must:
 1. make more profit per 1,000 clients than calling everyone;
 2. make more profit per 1,000 clients than the simple rule (call only poutcome == "success");
 3. beat the logistic-regression baseline by at least €300 per 1,000 clients.

Why €300: it is about 5 extra subscribers found per 1,000 clients (5 × €60), or 30 wasted calls avoided. The test set has about 2,000 contacts and ~225 subscribers, so a few subscribers more or less moves profit by a few hundred euros per 1,000 by chance alone. A smaller gain would not be distinguishable from noise, nor worth the cost of an Earth search. I will revisit this number after the baselines (Gate 3), once I see the fold-to-fold spread of profit.

## Feature boundary (Step 2): in / out, with a reason per excluded column
The test for every column: is it known **before the campaign starts**, when the call list is made? Evidence is in `work/exploration/EDA.ipynb`.

| Column | In / out | Reason |
|---|---|---|
| `age`, `job`, `marital`, `education`, `default`, `housing`, `loan` | in | Client profile, on file before the campaign. `unknown` is kept as its own category (see below). |
| `previous`, `poutcome` | in | History from earlier campaigns, known before this one starts. |
| `contact` | in | Phone type (cellular / telephone) is on file before calling. |
| `pdays` | out (as a number) | 999 is a code ("never contacted" or not recorded) for 96.6% of rows, not a number of days. Its signal is "contacted before or not" (raw corr −0.32 = corr of the flag), which `poutcome` and `previous` already carry. Real day counts exist for only 342 rows. If a model needs it, use the flag `pdays != 999`, never the raw value. |
| `duration` | out | Target leakage: the call length is known only after the call, when `y` is already known (`bank-additional-names.txt`). |
| `campaign` | out | Number of contacts with the client *in this campaign, including this one*. It does not exist before the campaign starts. |
| `month`, `day_of_week` | out | Date of the *last* contact: set during the campaign, not before it, and when to call is out of scope (brief). `month` is also partly a clock: the rare high-rate months (mar/sep/oct/dec) come mostly from 2009–2010. |
| `emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed` | out | They describe the period, not the client: in the next campaign every client has the same values, so they cannot help choose *who* to call. They encode time (rate 4.5% in 2008, 21% in 2009, 53% in 2010), so with a random split they inflate the score without helping the next campaign. |
| `contact_order` | out | Row ID and a clock. The rate rises from 3% to 47% across its deciles because of time, and a future campaign's values lie outside the training range. Not target leakage (the date is known before calling), but temporal leakage under a random split. |
| `y` | target | The label. |

What the excluded time columns do to the score (logistic regression, 5-fold CV on `train.csv`, ROC-AUC): features in the boundary 0.713; + economic columns 0.785; + `contact_order` 0.781; + `month` 0.757. The jump comes from recognising the period, which a random split rewards and the next campaign will not. So my scores will be lower than with these columns, and more honest.

## Messy values
- `unknown` (in `default` 20.5%, `education` 4.1%, `housing`/`loan` 2.3% on the same rows, `job`, `marital`) is the dataset's missing value. It carries information (`default = unknown` subscribes at 4.6% vs 13.0% for `no`), so it stays as its own category, not imputed.
- `pdays = 999` is a code, not a number of days: excluded as a number (see the table).

## Split and its limits
The split is frozen once: stratified random 80/20 on `y`, seed 42 (`work/exploration/prepare_split.py`, `split_metadata.json`). Rows are in date order and the world changes strongly over time (2008: 68% of rows at 4.5%; 2010: 5% of rows at 53%). A random split mixes the periods, so train and test look alike and the test profit is probably optimistic for the next campaign. A chronological split (train on 2008–2009, test on 2010) would answer "how will this work next campaign" better, but would test on only ~470 rows with a very different rate. Keeping time columns out of the features limits the damage; the remaining optimism is a stated limitation in the report.
