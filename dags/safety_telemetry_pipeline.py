"""
Safety Telemetry Platform - Airflow DAG

End-to-end pipeline:
1. Daily data ingestion
2. Staging to analytics transformation
3. Model scoring (survival + change-point)
4. Importance sampling evaluation
5. Alert generation
6. Results publication
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
    BigQueryCheckOperator
)
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.utils.dates import days_ago
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Default arguments
default_args = {
    'owner': 'safety_analytics',
    'depends_on_past': False,
    'email': ['alerts@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# DAG definition
dag = DAG(
    'safety_telemetry_pipeline',
    default_args=default_args,
    description='Daily safety telemetry processing pipeline',
    schedule_interval='@daily',  # Run daily at midnight
    catchup=False,
    tags=['safety', 'telemetry', 'analytics'],
)


# ============================================================================
# Task Definitions
# ============================================================================

def ingest_data(**context):
    """Ingest raw data files into staging tables."""
    from ingestion.loader import DataLoader
    
    execution_date = context['execution_date']
    data_date = execution_date.strftime('%Y-%m-%d')
    
    # In production, would read from GCS or other source
    input_dir = f'/opt/airflow/data/raw/{data_date}'
    target = os.getenv('TARGET_DB', 'local')
    
    loader = DataLoader(target=target)
    loader.load_directory(input_dir)
    
    return f"Data ingested for {data_date}"


def run_transforms(**context):
    """Run SQL transformations from staging to analytics."""
    # In production, would execute BigQuery SQL
    # For local, would execute SQLite SQL
    execution_date = context['execution_date']
    data_date = execution_date.strftime('%Y-%m-%d')
    
    # Placeholder: In production, use BigQueryExecuteQueryOperator
    print(f"Running transforms for {data_date}")
    
    return f"Transforms completed for {data_date}"


def run_survival_model(**context):
    """Run survival model for safety regression prediction."""
    from models.survival_model import SurvivalModel
    import pandas as pd
    
    execution_date = context['execution_date']
    
    # Load analytics data
    # In production, query from BigQuery
    # For demo, use local data
    query = """
    SELECT 
        vehicle_id,
        trip_id,
        DATE_DIFF(CURRENT_DATE(), date_key, DAY) * 24 AS time_to_event_hours,
        CASE WHEN critical_events > 0 THEN 1 ELSE 0 END AS regression_occurred
    FROM fact_trip_safety
    WHERE date_key >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    """
    
    # For local demo, use synthetic data
    import numpy as np
    np.random.seed(42)
    n_samples = 500
    df = pd.DataFrame({
        'vehicle_id': [f"VH_{i:05d}" for i in np.random.randint(1, 201, n_samples)],
        'time_to_event_hours': np.random.weibull(1.5, n_samples) * 100,
        'regression_occurred': np.random.binomial(1, 0.7, n_samples)
    })
    
    # Prepare data
    model = SurvivalModel(samples=1000, tune=500, chains=2)
    data = model.prepare_data(df)
    
    # Fit model
    idata = model.fit(data, progressbar=False)
    
    # Save results
    output_path = f'/opt/airflow/data/results/survival_{execution_date.strftime("%Y%m%d")}.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_results(output_path, data)
    
    return output_path


def run_changepoint_model(**context):
    """Run change-point detection model."""
    from models.changepoint_model import ChangepointModel
    import pandas as pd
    
    execution_date = context['execution_date']
    
    # Load time series data
    # In production, query from BigQuery
    query = """
    SELECT 
        date_key,
        vehicle_id,
        SUM(critical_events) AS critical_events,
        COUNT(DISTINCT trip_id) AS trip_count
    FROM fact_trip_safety
    WHERE date_key >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    GROUP BY date_key, vehicle_id
    ORDER BY date_key
    """
    
    # For local demo, use synthetic data
    import numpy as np
    np.random.seed(42)
    n_days = 90
    changepoint_day = 30
    
    dates = pd.date_range(execution_date - timedelta(days=n_days), periods=n_days)
    data = {
        'time': np.arange(n_days),
        'events': np.concatenate([
            np.random.poisson(0.5 * 100, changepoint_day),
            np.random.poisson(2.0 * 100, n_days - changepoint_day)
        ]),
        'exposure': np.random.poisson(100, n_days),
        'dates': dates,
        'start_date': dates[0]
    }
    
    # Fit model
    model = ChangepointModel(samples=1000, tune=500, chains=2)
    idata = model.fit(data, progressbar=False)
    
    # Detect change-point
    detection = model.detect_changepoint(data)
    
    # Save results
    output_path = f'/opt/airflow/data/results/changepoint_{execution_date.strftime("%Y%m%d")}.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_results(output_path, data, vehicle_id='AGGREGATE')
    
    return output_path


def run_importance_sampling(**context):
    """Run importance sampling experiment."""
    from models.importance_sampling import ImportanceSampling
    import pandas as pd
    
    execution_date = context['execution_date']
    
    # Load analytics data
    # In production, query from BigQuery
    query = """
    SELECT 
        trip_id,
        vehicle_id,
        total_events,
        critical_events,
        avg_latency_ms,
        safety_score,
        has_rare_event,
        rare_event_count
    FROM fact_trip_safety
    WHERE date_key >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    """
    
    # For local demo, use synthetic data
    import numpy as np
    np.random.seed(42)
    n_samples = 10000
    
    df = pd.DataFrame({
        'trip_duration': np.random.uniform(10, 120, n_samples),
        'total_events': np.random.poisson(2, n_samples),
        'critical_events': np.random.poisson(0.1, n_samples),
        'avg_latency_ms': np.random.uniform(10, 200, n_samples),
        'safety_score': np.random.uniform(50, 100, n_samples)
    })
    
    rare_event_prob = 0.01
    df['has_rare_event'] = np.random.binomial(1, rare_event_prob, n_samples)
    df.loc[df['avg_latency_ms'] > 150, 'has_rare_event'] = np.random.binomial(
        1, 0.1, df.loc[df['avg_latency_ms'] > 150].shape[0]
    )
    
    # Run experiment
    is_sampler = ImportanceSampling(rare_event_rate=rare_event_prob)
    results = is_sampler.run_experiment(df)
    
    # Save results
    output_path = f'/opt/airflow/data/results/importance_sampling_{execution_date.strftime("%Y%m%d")}.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    is_sampler.save_results(results, output_path)
    
    return output_path


def generate_alerts(**context):
    """Generate safety alerts based on model outputs."""
    import pandas as pd
    
    execution_date = context['execution_date']
    
    # Load model results
    changepoint_path = f'/opt/airflow/data/results/changepoint_{execution_date.strftime("%Y%m%d")}.csv'
    
    if os.path.exists(changepoint_path):
        df_cp = pd.read_csv(changepoint_path)
        
        # Generate alerts for detected regressions
        alerts = []
        for _, row in df_cp.iterrows():
            if row['changepoint_detected']:
                alerts.append({
                    'alert_id': f"ALERT_{execution_date.strftime('%Y%m%d')}_{len(alerts)}",
                    'alert_timestamp': execution_date.isoformat(),
                    'alert_type': 'regression_detected',
                    'severity': 'critical' if row['hazard_ratio'] > 2.0 else 'warning',
                    'vehicle_id': row['vehicle_id'],
                    'alert_message': f"Safety regression detected: hazard ratio {row['hazard_ratio']:.2f}",
                    'alert_metric': 'hazard_ratio',
                    'alert_value': row['hazard_ratio'],
                    'alert_threshold': 1.5,
                    'is_acknowledged': False,
                    'is_resolved': False,
                    'source_model_run_id': row['model_run_id'],
                    'notification_sent': False
                })
        
        # Save alerts
        if alerts:
            alerts_path = f'/opt/airflow/data/alerts/alerts_{execution_date.strftime("%Y%m%d")}.csv'
            os.makedirs(os.path.dirname(alerts_path), exist_ok=True)
            df_alerts = pd.DataFrame(alerts)
            df_alerts.to_csv(alerts_path, index=False)
            print(f"Generated {len(alerts)} alerts")
        else:
            print("No alerts generated")
    
    return f"Alerts generated for {execution_date.strftime('%Y-%m-%d')}"


def publish_results(**context):
    """Publish results to BigQuery and trigger dashboard refresh."""
    execution_date = context['execution_date']
    
    # In production, would:
    # 1. Load CSV results to BigQuery
    # 2. Trigger Power BI dataset refresh
    # 3. Send summary email
    
    print(f"Publishing results for {execution_date.strftime('%Y-%m-%d')}")
    
    return "Results published"


# ============================================================================
# Task Dependencies
# ============================================================================

# Task 1: Data Ingestion
task_ingest = PythonOperator(
    task_id='ingest_data',
    python_callable=ingest_data,
    dag=dag,
)

# Task 2: Data Quality Check
task_data_quality = BigQueryCheckOperator(
    task_id='check_data_quality',
    sql="""
    SELECT COUNT(*) > 0
    FROM `safety_telemetry.staging_trips`
    WHERE DATE(start_timestamp) = '{{ ds }}'
    """,
    dag=dag,
)

# Task 3: Transform Staging to Analytics
task_transform = PythonOperator(
    task_id='transform_staging_to_analytics',
    python_callable=run_transforms,
    dag=dag,
)

# Task 4: Run Survival Model
task_survival = PythonOperator(
    task_id='run_survival_model',
    python_callable=run_survival_model,
    dag=dag,
)

# Task 5: Run Change-Point Model
task_changepoint = PythonOperator(
    task_id='run_changepoint_model',
    python_callable=run_changepoint_model,
    dag=dag,
)

# Task 6: Run Importance Sampling
task_importance = PythonOperator(
    task_id='run_importance_sampling',
    python_callable=run_importance_sampling,
    dag=dag,
)

# Task 7: Generate Alerts
task_alerts = PythonOperator(
    task_id='generate_alerts',
    python_callable=generate_alerts,
    dag=dag,
)

# Task 8: Publish Results
task_publish = PythonOperator(
    task_id='publish_results',
    python_callable=publish_results,
    dag=dag,
)

# ============================================================================
# Define DAG Flow
# ============================================================================

task_ingest >> task_data_quality >> task_transform
task_transform >> [task_survival, task_changepoint, task_importance]
[task_survival, task_changepoint, task_importance] >> task_alerts
task_alerts >> task_publish
