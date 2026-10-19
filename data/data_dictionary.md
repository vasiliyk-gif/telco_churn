# Data dictionary — Ames Housing (Lab 2)

Source: the Ames Housing data (Dean De Cock, *Journal of Statistics Education*, 2011), via the
`AmesHousing` R package (`ames_raw`). Every residential sale in Ames, Iowa, 2006 – July 2010.
Read the CSVs with `pd.read_csv(path, keep_default_na=False, na_values=[""])`: otherwise pandas turns
real categories such as `"None"` (no masonry veneer) into missing values. `NA` in many quality columns
means "no such thing" (no basement, no garage, no pool), not "unknown".

## Columns by group (as used by the fitness skeleton)

| Group | Columns | Notes |
|-------|---------|-------|
| Target | `SalePrice` | Dollars. Only in `ames_history.csv` |
| Id | `ListingID` | Only in `ames_2010_listings.csv` |
| Quality (always used) | `Overall Qual`, `Overall Cond` (1–10), `Exter Qual`, `Exter Cond`, `Kitchen Qual`, `Heating QC` (Ex/Gd/TA/Fa/Po), `Functional` | |
| Size (always used) | `Gr Liv Area` (above-ground sq ft), `Total Bsmt SF`, `1st Flr SF`, `2nd Flr SF`, `Low Qual Fin SF`, `Lot Area`, `Lot Frontage`, room and bath counts | `Lot Frontage` has missing values |
| Age | `Year Built`, `Year Remod/Add`, `Garage Yr Blt` | |
| Location | `Neighborhood` (28 areas), `MS Zoning`, `Condition 1/2` (near roads, rail, parks), lot shape, slope, contour, street, alley | |
| Basement and garage | `Bsmt Qual/Cond/Exposure`, finished types and areas, `Garage Type/Finish/Cars/Area/Qual/Cond`, `Paved Drive` | `NA` = none |
| Extras | everything else: `MS SubClass`, `House Style`, `Bldg Type`, roof, exterior, masonry, foundation, heating, `Central Air`, electrical, fireplaces, porches, deck, pool, fence, `Misc Feature`, `Misc Val`, `Utilities` | |
| Sale (history only) | `Mo Sold`, `Yr Sold`, `Sale Type`, `Sale Condition` | Known only when the sale happens. `Sale Condition` = Abnorml (foreclosure, short sale), Partial (new home), Family, ... Not in the 2010 listings, except the year and month |

Full descriptions of every column and code: the original documentation,
<https://jse.amstat.org/v19n3/decock/DataDocumentation.txt>.
