# Project brief — Term-deposit phone campaign (homework)

## Background

A Portuguese retail bank sells **term deposits** (money locked for a fixed
period at a fixed interest rate) through outbound phone campaigns. Agents call
existing clients, often more than once, and offer the deposit. Most calls end
in "no": about 1 call in 9 leads to a subscription.

Calls cost money, and most of them are wasted. The marketing team wants to stop
calling everyone on the list and call only the clients who are worth a call.

## The decision

Before the next campaign starts, the bank decides **which clients to call**.
Each client on the list is either called or not called.

## Business question

> Which clients should we call in the next campaign to make the most money,
> and how much more is that than calling everyone or using a simple rule?

## Money

Teaching assumptions (illustrative, not the bank's real figures):

| Item | Value | Meaning |
|------|-------|---------|
| Cost of one call | **€10** | Agent time, dialing, and overhead, paid for every call |
| Value of one subscription | **€70** | Net margin the bank earns on an average deposit over its term |

So one call pays off only when the chance that the client subscribes is above
€10 / €70 ≈ **14%**. On the historical data, about 11% of calls end in a
subscription: **calling everyone loses money.**

Campaign profit = €70 × (subscriptions among the clients we call) − €10 × (calls we make)

## Goal

Build a model that ranks clients by how likely they are to subscribe, and a
rule that turns that ranking into a call list, so the campaign makes
as much profit as possible. Compare it with two references: calling everyone,
and a simple business rule.

## Target

`y`: did the client subscribe to a term deposit after the campaign call?
(`yes` / `no`). The positive class is `yes`.

## Unit of analysis

One row is one campaign contact with one client, with the client's profile,
the contact history, and the economic context at the time.

## Data

`data/bank_10k.csv`: 10,000 contacts sampled from the UCI "Bank Marketing"
dataset (bank-additional-full, Moro et al., 2014; CC BY 4.0). The rows are in
date order from May 2008 to November 2010 (`contact_order`). Column meanings:
`data/data_dictionary.md` and the original `data/bank-additional-names.txt`.

## What you will decide in framing

These are your decisions; write each one down with a reason.

1. **Feature boundary.** Which columns are known *before* you decide to call?
   Read the description of every column, especially `duration`.
2. **Economic context.** The five economic columns describe the period, not the
   client. Can you use them for the next campaign? What do they do to your
   score?
3. **Split.** The homework freezes a stratified random split. The rows are in
   date order: what would a chronological split (train on earlier contacts,
   test on later ones) tell you that the random split cannot? Which one answers
   "how will this work next campaign"?
4. **Messy values.** `unknown` in several columns, and `pdays = 999`. What do
   they mean, and how will you treat them?
5. **Metric.** The model ranks clients; the call list is the top share of the
   ranking. The fitness picks that share on the training folds and reports the
   profit on the validation folds. Why not pick the share on the validation
   folds? And why is profit a better score here than F1 or AUC?
6. **Success.** Your model's profit must beat both references (call everyone,
   simple rule) on the test set, scored once. How much better than the
   logistic-regression baseline would make the Earth search worth it?

## Out of scope

The offer itself, interest rates, which agent calls, when to call, and the
long-term value of a client beyond this deposit.
