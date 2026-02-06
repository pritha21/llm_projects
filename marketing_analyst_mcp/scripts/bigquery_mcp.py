from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
import json

# MCP = "Tool Connectivity" (Connecting AI to external systems)
mcp = FastMCP("BigQuery Connector")

@mcp.tool()
def run_sql_query(sql: str) -> str:
    """
    Executes a Standard SQL query against BigQuery. 
    Returns the raw results as JSON.
    """
    client = bigquery.Client()
    try:
        query_job = client.query(sql)
        rows = [dict(row) for row in query_job.result()]
        # Helper to fix date objects for JSON
        for row in rows:
            for k, v in row.items():
                if hasattr(v, 'isoformat'): row[k] = v.isoformat()
        return json.dumps(rows, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()