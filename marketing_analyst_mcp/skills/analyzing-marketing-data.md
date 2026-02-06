---
name: analyzing-marketing-data
description: Analyzes the marketing_db dataset using BigQuery to extract insights on spending, campaigns, and customer demographics. Use when the user asks about marketing metrics, customer segments, or campaign performance.
metadata:
  version: "1.0"
  author: "marketing-team"
---

# Marketing Data Analysis

## 1. Context & Data Dictionary
You are analyzing the `marketing_db.campaigns` table. Map user terms strictly to these definitions:

### Metrics
* **"Spending"**: Sum of `MntWines`, `MntFruits`, `MntMeatProducts`, `MntFishProducts`, `MntSweetProducts`, `MntGoldProds`.
* **"Campaign Success"**: `Response` = 1 (This refers to the *last* campaign).
* **"Previous Campaigns"**: `AcceptedCmp1` through `AcceptedCmp5` (1 = Yes, 0 = No).

### Attributes
* **"Education"**: Values are `'Graduation'`, `'PhD'`, `'Master'`, `'Basic'`, `'2n Cycle'`.
* **"Income"**: Column `Income`. **CRITICAL:** Always filter `WHERE Income IS NOT NULL` when calculating averages.

## 2. Analysis Workflow
Follow this checklist for every query to ensure accuracy:

1.  [ ] **Map Terms**: Identify which columns match the user's specific words (e.g., "Rich" -> `Income`, "Parents" -> `Kidhome > 0`).
2.  [ ] **Select Tool**: Use the `run_sql_query` tool.
3.  [ ] **Constraint Check**:
    * Are you filtering NULL incomes?
    * Are you using the correct table `marketing_db.campaigns`?
    * Are you using `READ ONLY` syntax (SELECT only)?
4.  [ ] **Execute & Synthesize**: Run the query and summarize the returned JSON data in plain English.

## 3. Example Patterns (Few-Shot)

**Example 1: Aggregation**
*Input:* "Do PhDs spend more on wine than Masters?"
*Output:*
```sql
SELECT Education, AVG(MntWines) as avg_wine
FROM `marketing_db.campaigns`
WHERE Education IN ('PhD', 'Master')
GROUP BY Education

**Example 2: Filtering & Ranking** 
*Input:* "List the top 5 customers with the highest income." 
*Output:*

```sql
SELECT ID, Education, Income
FROM `marketing_db.campaigns`
WHERE Income IS NOT NULL
ORDER BY Income DESC
LIMIT 5

**Example 3: Complex Segmentation** 
*Input:* "What is the conversion rate of the last campaign for parents?*Output:*

```sql
SELECT
  COUNT(*) as total_parents,
  SUM(Response) as accepted_last_campaign,
  (SUM(Response) / COUNT(*)) * 100 as conversion_rate
FROM `marketing_db.campaigns`
WHERE Kidhome > 0 OR Teenhome > 0