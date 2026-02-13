#!/usr/bin/env python3
"""
Run SQL transformations from staging to analytics.

Supports both BigQuery and local SQLite.
"""

import argparse
import os
import sys
from pathlib import Path
import sqlite3
from google.cloud import bigquery
from google.oauth2 import service_account


def run_sql_file(file_path: Path, target: str, **kwargs):
    """Execute SQL file against target database."""
    with open(file_path, 'r') as f:
        sql = f.read()
    
    if target == 'bigquery':
        client = kwargs.get('client')
        if client is None:
            raise ValueError("BigQuery client required")
        
        # Split SQL by semicolons (simple approach)
        queries = [q.strip() for q in sql.split(';') if q.strip()]
        
        for query in queries:
            if query:
                print(f"Executing query...")
                job = client.query(query)
                job.result()  # Wait for completion
                print(f"Query completed: {job.job_id}")
    
    elif target == 'local':
        db_path = kwargs.get('db_path', './data/staging/local.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQLite doesn't support all BigQuery syntax
        # This is a simplified version
        queries = [q.strip() for q in sql.split(';') if q.strip()]
        
        for query in queries:
            if query and not query.startswith('--'):
                try:
                    cursor.execute(query)
                    conn.commit()
                    print(f"Query executed successfully")
                except sqlite3.Error as e:
                    print(f"Error executing query: {e}")
        
        conn.close()
    
    else:
        raise ValueError(f"Unknown target: {target}")


def main():
    parser = argparse.ArgumentParser(description='Run SQL transformations')
    parser.add_argument('--target', type=str, default='local',
                       choices=['local', 'bigquery'],
                       help='Target database')
    parser.add_argument('--project-id', type=str, default=None,
                       help='GCP project ID (for BigQuery)')
    parser.add_argument('--credentials', type=str, default=None,
                       help='Path to GCP service account JSON')
    parser.add_argument('--local-db', type=str, default='./data/staging/local.db',
                       help='Local SQLite database path')
    parser.add_argument('--sql-file', type=str,
                       default='transforms/sql/staging_to_analytics.sql',
                       help='SQL file to execute')
    
    args = parser.parse_args()
    
    sql_file = Path(args.sql_file)
    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        sys.exit(1)
    
    kwargs = {}
    if args.target == 'bigquery':
        if args.credentials:
            credentials = service_account.Credentials.from_service_account_file(
                args.credentials
            )
            kwargs['client'] = bigquery.Client(
                project=args.project_id,
                credentials=credentials
            )
        else:
            kwargs['client'] = bigquery.Client(project=args.project_id)
    else:
        kwargs['db_path'] = args.local_db
    
    print(f"Running transformations from {sql_file} to {args.target}...")
    run_sql_file(sql_file, args.target, **kwargs)
    print("Transformations complete.")


if __name__ == '__main__':
    main()
