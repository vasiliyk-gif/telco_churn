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
