"""
Data Loader - Loads raw JSONL/CSV files into staging tables

Supports both BigQuery (GCP) and local SQLite for development.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import sqlite3
from google.cloud import bigquery
from google.oauth2 import service_account
import os


class DataLoader:
    """Load raw data files into staging tables."""
    
    def __init__(
        self,
        target: str = 'local',
        project_id: Optional[str] = None,
        dataset_id: str = 'safety_telemetry',
        credentials_path: Optional[str] = None,
        local_db_path: str = './data/staging/local.db'
    ):
        """
        Initialize loader.
        
        Args:
            target: 'local' or 'bigquery'
            project_id: GCP project ID (for BigQuery)
            dataset_id: BigQuery dataset ID
            credentials_path: Path to service account JSON
            local_db_path: Path to local SQLite database
        """
        self.target = target
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        if target == 'bigquery':
            if credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.client = bigquery.Client(
                    project=project_id,
                    credentials=credentials
                )
            else:
                # Use default credentials
                self.client = bigquery.Client(project=project_id)
            self._setup_bigquery_tables()
        else:
            # Local SQLite
            self.local_db_path = local_db_path
            Path(local_db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(local_db_path)
            self._setup_local_tables()
    
    def _setup_bigquery_tables(self):
        """Create BigQuery staging tables if they don't exist."""
        # In production, tables should be created via DDL
        # This is a placeholder for validation
        print(f"Using BigQuery: {self.project_id}.{self.dataset_id}")
    
    def _setup_local_tables(self):
        """Create local SQLite staging tables."""
        cursor = self.conn.cursor()
        
        # Staging trips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staging_trips (
                trip_id TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                driver_id TEXT,
                start_timestamp TEXT NOT NULL,
                end_timestamp TEXT,
                start_location_lat REAL,
                start_location_lon REAL,
                end_location_lat REAL,
                end_location_lon REAL,
                trip_distance_km REAL,
                trip_duration_seconds INTEGER,
                operating_mode TEXT,
                weather_condition TEXT,
                road_type TEXT,
                ingestion_timestamp TEXT NOT NULL,
                source_file TEXT,
                raw_data TEXT
            )
        """)
        
        # Staging events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staging_events (
                event_id TEXT NOT NULL,
                trip_id TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_severity TEXT,
                event_category TEXT,
                event_subcategory TEXT,
                event_description TEXT,
                intervention_type TEXT,
                fault_code TEXT,
                latency_ms REAL,
                confidence_score REAL,
                sensor_data TEXT,
                metadata TEXT,
                ingestion_timestamp TEXT NOT NULL,
                source_file TEXT
            )
        """)
        
        # Staging mode transitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staging_mode_transitions (
                transition_id TEXT NOT NULL,
                trip_id TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                transition_timestamp TEXT NOT NULL,
                from_mode TEXT NOT NULL,
                to_mode TEXT NOT NULL,
                transition_reason TEXT,
                transition_duration_seconds REAL,
                context_data TEXT,
                ingestion_timestamp TEXT NOT NULL,
                source_file TEXT
            )
        """)
        
        self.conn.commit()
        print(f"Local tables created/verified in {self.local_db_path}")
    
    def load_jsonl_file(self, file_path: Path, table_name: str):
        """Load a JSONL file into staging table."""
        print(f"Loading {file_path} into {table_name}...")
        
        records = []
        with open(file_path, 'r') as f:
            for line in f:
                records.append(json.loads(line.strip()))
        
        if not records:
            print(f"  No records found in {file_path}")
            return
        
        df = pd.DataFrame(records)
        
        if self.target == 'bigquery':
            self._load_to_bigquery(df, table_name)
        else:
            self._load_to_local(df, table_name)
        
        print(f"  Loaded {len(records)} records into {table_name}")
    
    def _load_to_bigquery(self, df: pd.DataFrame, table_name: str):
        """Load DataFrame to BigQuery."""
        table_ref = self.client.dataset(self.dataset_id).table(f"staging_{table_name}")
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        )
        
        # Convert DataFrame to JSON
        json_data = df.to_json(orient='records', lines=True)
        
        job = self.client.load_table_from_file(
            json_data.encode('utf-8'),
            table_ref,
            job_config=job_config
        )
        job.result()  # Wait for job to complete
    
    def _load_to_local(self, df: pd.DataFrame, table_name: str):
        """Load DataFrame to local SQLite."""
        df.to_sql(f"staging_{table_name}", self.conn, if_exists='append', index=False)
    
    def load_directory(self, input_dir: Path):
        """Load all JSONL files from directory."""
        input_dir = Path(input_dir)
        
        # Map file names to table names
        file_mapping = {
            'trips.jsonl': 'trips',
            'events.jsonl': 'events',
            'transitions.jsonl': 'transitions'
        }
        
        for filename, table_name in file_mapping.items():
            file_path = input_dir / filename
            if file_path.exists():
                self.load_jsonl_file(file_path, table_name)
            else:
                print(f"  File not found: {file_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Load raw data into staging tables')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory or file path')
    parser.add_argument('--target', type=str, default='local',
                       choices=['local', 'bigquery'],
                       help='Target: local or bigquery')
    parser.add_argument('--project-id', type=str, default=None,
                       help='GCP project ID (for BigQuery)')
    parser.add_argument('--dataset-id', type=str, default='safety_telemetry',
                       help='BigQuery dataset ID')
    parser.add_argument('--credentials', type=str, default=None,
                       help='Path to GCP service account JSON')
    parser.add_argument('--local-db', type=str, default='./data/staging/local.db',
                       help='Local SQLite database path')
    
    args = parser.parse_args()
    
    loader = DataLoader(
        target=args.target,
        project_id=args.project_id,
        dataset_id=args.dataset_id,
        credentials_path=args.credentials,
        local_db_path=args.local_db
    )
    
    input_path = Path(args.input)
    if input_path.is_file():
        # Load single file
        table_name = input_path.stem  # Remove extension
        loader.load_jsonl_file(input_path, table_name)
    else:
        # Load directory
        loader.load_directory(input_path)
    
    print("\nData loading complete.")


if __name__ == '__main__':
    main()
