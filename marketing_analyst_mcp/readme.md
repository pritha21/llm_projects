# Marketing Analyst MCP Server

A BigQuery-powered marketing data analysis tool using the Model Context Protocol (MCP) to enable AI assistants to query and analyze marketing campaign data.

## 📋 Overview

This project provides an MCP server that connects AI assistants to Google BigQuery, allowing them to analyze marketing campaign data through natural language queries. The system uses the **iFood Marketing Campaign dataset** to provide insights on customer demographics, spending patterns, and campaign performance.

## 🏗️ Architecture

```
marketing_analyst/
├── scripts/
│   └── bigquery_mcp.py      # MCP server with BigQuery connector
├── skills/
│   └── analyzing-marketing-data.md  # AI skill definition for data analysis
├── kaggle_data/
│   ├── ifood_df.csv         # Marketing campaign dataset
│   └── dictionary.png       # Data dictionary reference
├── key.json                 # GCP service account credentials
└── README.md
```

## 🗄️ Dataset

The project uses the **iFood Marketing Campaign dataset** stored in BigQuery at `marketing_db.campaigns`.

### Key Metrics

| Category | Columns |
|----------|---------|
| **Spending** | `MntWines`, `MntFruits`, `MntMeatProducts`, `MntFishProducts`, `MntSweetProducts`, `MntGoldProds` |
| **Campaign Response** | `AcceptedCmp1` - `AcceptedCmp5`, `Response` (last campaign) |
| **Demographics** | `Education`, `Marital`, `Income`, `Kidhome`, `Teenhome` |
| **Purchase Channels** | `NumWebPurchases`, `NumCatalogPurchases`, `NumStorePurchases`, `NumDealsPurchases` |
| **Engagement** | `NumWebVisitsMonth`, `Recency`, `DtCustomer` |

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Cloud Platform account with BigQuery enabled
- Service account with BigQuery permissions

### Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   pip install mcp google-cloud-bigquery
   ```

3. **Configure GCP credentials**
   
   Set the environment variable to point to your service account key:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

4. **Load data to BigQuery**
   
   Upload `kaggle_data/ifood_df.csv` to your BigQuery dataset as `marketing_db.campaigns`.

### Running the MCP Server

```bash
python scripts/bigquery_mcp.py
```

## 🔧 MCP Tool

### `run_sql_query`

Executes StandardSQL queries against BigQuery and returns results as JSON.

**Parameters:**
- `sql` (str): The SQL query to execute

**Returns:** JSON string with query results

**Example:**
```python
run_sql_query("SELECT Education, AVG(Income) FROM `marketing_db.campaigns` WHERE Income IS NOT NULL GROUP BY Education")
```

## 📊 Sample Queries

### Average spending by education level
```sql
SELECT 
    Education, 
    AVG(MntWines + MntFruits + MntMeatProducts + MntFishProducts + MntSweetProducts + MntGoldProds) as avg_total_spending
FROM `marketing_db.campaigns`
GROUP BY Education
ORDER BY avg_total_spending DESC
```

### Campaign conversion rate for parents
```sql
SELECT
    COUNT(*) as total_parents,
    SUM(Response) as accepted_last_campaign,
    (SUM(Response) / COUNT(*)) * 100 as conversion_rate
FROM `marketing_db.campaigns`
WHERE Kidhome > 0 OR Teenhome > 0
```

### Top 5 highest income customers
```sql
SELECT ID, Education, Income
FROM `marketing_db.campaigns`
WHERE Income IS NOT NULL
ORDER BY Income DESC
LIMIT 5
```

## 🤖 AI Skills

The `skills/analyzing-marketing-data.md` file provides structured guidance for AI assistants to:

- Map natural language terms to database columns
- Follow a consistent analysis workflow
- Apply critical constraints (e.g., filtering NULL incomes)
- Use few-shot examples for accurate query generation

## ⚠️ Important Notes

- Always filter `WHERE Income IS NOT NULL` when calculating income-related averages
- The `Response` column refers to the **last campaign** only
- Columns `AcceptedCmp1` through `AcceptedCmp5` refer to **previous campaigns**
- All queries are **read-only** (SELECT statements only)

## 📝 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- Dataset: [iFood Marketing Campaign](https://www.kaggle.com/datasets/rodsaldanha/arketing-campaign) from Kaggle
- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
