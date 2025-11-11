import os
from typing import List, Dict

from flask import Flask, jsonify
from flask import request
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

from config import PROJECT_ID, DATASET_ID, GOOGLE_APPLICATION_CREDENTIALS


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configure CORS
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN")
if FRONTEND_ORIGIN:
    CORS(app, resources={r"/*": {"origins": [FRONTEND_ORIGIN]}}, supports_credentials=True)
else:
    # Allow all in dev by default
    CORS(app, resources={r"/*": {"origins": "*"}})


_bq_client: bigquery.Client | None = None


def get_bigquery_client() -> bigquery.Client:
    """Create or return a cached BigQuery client using ADC.

    Requires GOOGLE_APPLICATION_CREDENTIALS to be set or gcloud ADC available.
    """
    global _bq_client
    if _bq_client is not None:
        return _bq_client

    # Ensure credentials are discoverable for local dev
    if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", GOOGLE_APPLICATION_CREDENTIALS)

    _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def rows_to_dicts(rows: List[bigquery.table.Row]) -> List[Dict]:
    return [dict(row) for row in rows]


@app.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.get("/")
def root() -> tuple:
    return jsonify({
        "service": "stream_api",
        "endpoints": ["/most_streamed/top5", "/most_streamed/top6", "/games/<game_name>", "/health"]
    }), 200


@app.get("/most_streamed/top5")
def most_streamed_top5() -> tuple:
    """Return top 10 streamed games from the most_streamed table.

    Optional query params:
      - dataset: override dataset id
      - table: override table name (default: most_streamed)
    """
    dataset = request.args.get("dataset") or DATASET_ID
    table = request.args.get("table") or "game_streams"

    if not PROJECT_ID or not dataset:
        return jsonify({
            "error": "Missing PROJECT_ID or DATASET_ID in environment/config",
        }), 500

    table_fqn = f"`{PROJECT_ID}.{dataset}_datamart.{table}`"
    game_table = f"`{PROJECT_ID}.{dataset}_dim.games`"

    # Use a generic aggregation that works even if the table stores raw rows
    sql = f"""

        with games as (
            select distinct game_name, image
            from {game_table} 
        )
        SELECT
          game_name
          , times_played
          , image
        FROM {table_fqn}
        left join games using (game_name)
        where created_dt = (select max(created_dt) from {table_fqn})
        and game_name is not null 
        ORDER BY times_played DESC
        
        LIMIT 5
    """

    try:
        client = get_bigquery_client()
        job = client.query(sql)
        rows = list(job.result())
        return jsonify({
            "project_id": PROJECT_ID,
            "dataset_id": dataset,
            "table": table,
            "data": rows_to_dicts(rows),
        }), 200
    except GoogleAPIError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    



@app.get("/most_streamed/top6")
def most_streamed_top6() -> tuple:
    """Return top 10 streamed games from the most_streamed table.

    Optional query params:
      - dataset: override dataset id
      - table: override table name (default: most_streamed)
    """
    dataset = request.args.get("dataset") or DATASET_ID
    table = request.args.get("table") or "game_streams"

    if not PROJECT_ID or not dataset:
        return jsonify({
            "error": "Missing PROJECT_ID or DATASET_ID in environment/config",
        }), 500

    table_fqn = f"`{PROJECT_ID}.{dataset}_datamart.{table}`"

    # Use a generic aggregation that works even if the table stores raw rows
    sql = f"""
        SELECT
          game_name,
          times_played
        FROM {table_fqn}
        where created_dt = (select max(created_dt) from {table_fqn})
        and game_name is not null 
        ORDER BY times_played DESC
        
        LIMIT 5
    """

    try:
        client = get_bigquery_client()
        job = client.query(sql)
        rows = list(job.result())
        return jsonify({
            "project_id": PROJECT_ID,
            "dataset_id": dataset,
            "table": table,
            "data": rows_to_dicts(rows),
        }), 200
    except GoogleAPIError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.get("/games/<game_name>")
def game_details(game_name: str) -> tuple:
    """Return details for a single game by name.

    Looks up the latest snapshot in the datamart table and joins to the dim.games
    table to provide image/description metadata where available.
    """
    dataset = request.args.get("dataset") or DATASET_ID
    table = request.args.get("table") or "game_streams"

    if not PROJECT_ID or not dataset:
        return jsonify({
            "error": "Missing PROJECT_ID or DATASET_ID in environment/config",
        }), 500

    table_fqn = f"`{PROJECT_ID}.{dataset}_datamart.{table}`"
    game_table = f"`{PROJECT_ID}.{dataset}_dim.games`"

    sql = f"""
        with games as (
            select distinct game_name, image, description
            from {game_table}
        )
        select
          gs.game_name,
          gs.times_played,
          g.image,
          g.description
        from {table_fqn} gs
        left join games g using (game_name)
        where gs.created_dt = (select max(created_dt) from {table_fqn})
        and gs.game_name = @game_name
        limit 1
    """

    try:
        client = get_bigquery_client()
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("game_name", "STRING", game_name)]
        )
        job = client.query(sql, job_config=job_config)
        rows = list(job.result())
        data = rows_to_dicts(rows)
        # return object (or empty) under data key for consistency with other endpoints
        return jsonify({
            "project_id": PROJECT_ID,
            "dataset_id": dataset,
            "table": table,
            "data": data[0] if data else None,
        }), 200
    except GoogleAPIError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Serve on port 8000 so that the FastAPI proxy in app.py can forward to us.
    app.run(host="0.0.0.0", port=8000, debug=True)
