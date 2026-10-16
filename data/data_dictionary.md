# Data dictionary — Bank Marketing (homework copy)

**Source.** UCI Machine Learning Repository, "Bank Marketing"
(`bank-additional-full.csv`; S. Moro, P. Cortez, P. Rita, 2014; CC BY 4.0). The
original documentation is in `bank-additional-names.txt`.

**This file.** `bank_10k.csv`: 10,000 of the 41,188 contacts, sampled at random
and stratified on `y`, kept in the original date order (May 2008 – November
2010). 11.3% of contacts end in a subscription.

**What a row is.** One phone contact with one client during a term-deposit
campaign, with the client's profile, the contact history, and the economic
context at the time.

**The label.** `y`: did the client subscribe to a term deposit? (`yes` / `no`)

| Column | Meaning | Values / notes |
|---|---|---|
| `contact_order` | Position of the contact in the original, date-ordered file (smaller = earlier) | Integer. Added for this homework; an identifier, and also a clock |
| `age` | Client age | Years |
| `job` | Type of job | 12 categories, incl. `unknown` |
| `marital` | Marital status | `married`, `single`, `divorced`, `unknown` |
| `education` | Education level | 8 categories, incl. `unknown` |
| `default` | Has credit in default? | `no`, `unknown` (`yes` is almost absent in the full data and absent here) |
| `housing` | Has a housing loan? | `no`, `yes`, `unknown` |
| `loan` | Has a personal loan? | `no`, `yes`, `unknown` |
| `contact` | Phone type used for the contact | `cellular`, `telephone` |
| `month` | Month of the last contact | `mar` … `dec` (no contacts in January or February) |
| `day_of_week` | Weekday of the last contact | `mon` … `fri` |
| `duration` | Length of the last call, in seconds | **Read the note in `bank-additional-names.txt` before using it** |
| `campaign` | Number of contacts with this client in this campaign, including this one | Integer |
| `pdays` | Days since the client was last contacted in a previous campaign | Integer; **999 means never contacted before** |
| `previous` | Number of contacts with this client before this campaign | Integer |
| `poutcome` | Outcome of the previous campaign | `failure`, `nonexistent`, `success` |
| `emp.var.rate` | Employment variation rate, quarterly | Economy, same for everyone in the period |
| `cons.price.idx` | Consumer price index, monthly | Economy |
| `cons.conf.idx` | Consumer confidence index, monthly | Economy |
| `euribor3m` | 3-month Euribor interest rate, daily | Economy |
| `nr.employed` | Number of employees, quarterly | Economy |
| `y` | **Label.** Subscribed to a term deposit? | `yes`, `no` |
