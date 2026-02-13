-- ============================================================================
-- Safety Telemetry Platform - BigQuery Schema Definitions
-- ============================================================================
-- This schema is designed for GCP BigQuery but can be adapted for local SQL
-- All timestamps are in UTC
-- ============================================================================

-- ----------------------------------------------------------------------------
-- STAGING TABLES (Raw ingested data)
-- ----------------------------------------------------------------------------

-- Raw trip telemetry data
CREATE TABLE IF NOT EXISTS `safety_telemetry.staging_trips` (
    trip_id STRING NOT NULL,
    vehicle_id STRING NOT NULL,
    driver_id STRING,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP,
    start_location_lat FLOAT64,
    start_location_lon FLOAT64,
    end_location_lat FLOAT64,
    end_location_lon FLOAT64,
    trip_distance_km FLOAT64,
    trip_duration_seconds INT64,
    operating_mode STRING,  -- 'autonomous', 'manual', 'transition'
    weather_condition STRING,
    road_type STRING,
    ingestion_timestamp TIMESTAMP NOT NULL,
    source_file STRING,
    raw_data JSON
) PARTITION BY DATE(start_timestamp)
CLUSTER BY vehicle_id, start_timestamp;

-- Raw event telemetry (safety events, faults, interventions)
CREATE TABLE IF NOT EXISTS `safety_telemetry.staging_events` (
    event_id STRING NOT NULL,
    trip_id STRING NOT NULL,
    vehicle_id STRING NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    event_type STRING NOT NULL,  -- 'safety_intervention', 'fault', 'mode_transition', 'latency_spike'
    event_severity STRING,  -- 'critical', 'warning', 'info'
    event_category STRING,  -- 'perception', 'planning', 'control', 'system'
    event_subcategory STRING,
    event_description STRING,
    intervention_type STRING,  -- 'takeover', 'brake', 'steer', 'none'
    fault_code STRING,
    latency_ms FLOAT64,
    confidence_score FLOAT64,
    sensor_data JSON,
    metadata JSON,
    ingestion_timestamp TIMESTAMP NOT NULL,
    source_file STRING
) PARTITION BY DATE(event_timestamp)
CLUSTER BY trip_id, event_timestamp, event_type;

-- Raw mode transition events
CREATE TABLE IF NOT EXISTS `safety_telemetry.staging_mode_transitions` (
    transition_id STRING NOT NULL,
    trip_id STRING NOT NULL,
    vehicle_id STRING NOT NULL,
    transition_timestamp TIMESTAMP NOT NULL,
    from_mode STRING NOT NULL,  -- 'autonomous', 'manual', 'standby'
    to_mode STRING NOT NULL,
    transition_reason STRING,  -- 'user_request', 'system_fault', 'safety_intervention', 'planned'
    transition_duration_seconds FLOAT64,
    context_data JSON,
    ingestion_timestamp TIMESTAMP NOT NULL,
    source_file STRING
) PARTITION BY DATE(transition_timestamp)
CLUSTER BY trip_id, transition_timestamp;

-- ----------------------------------------------------------------------------
-- ANALYTICS TABLES (Star Schema - Fact & Dimension Tables)
-- ----------------------------------------------------------------------------

-- Dimension: Vehicles
CREATE TABLE IF NOT EXISTS `safety_telemetry.dim_vehicles` (
    vehicle_id STRING NOT NULL,
    vehicle_model STRING,
    vehicle_year INT64,
    firmware_version STRING,
    hardware_config STRING,
    first_seen_date DATE,
    last_seen_date DATE,
    total_trips INT64,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_current BOOL
) CLUSTER BY vehicle_id;

-- Dimension: Drivers
CREATE TABLE IF NOT EXISTS `safety_telemetry.dim_drivers` (
    driver_id STRING NOT NULL,
    driver_experience_years INT64,
    driver_category STRING,  -- 'professional', 'consumer', 'test'
    first_seen_date DATE,
    last_seen_date DATE,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_current BOOL
) CLUSTER BY driver_id;

-- Dimension: Time (Date dimension)
CREATE TABLE IF NOT EXISTS `safety_telemetry.dim_time` (
    date_key DATE NOT NULL,
    year INT64,
    quarter INT64,
    month INT64,
    week INT64,
    day_of_year INT64,
    day_of_month INT64,
    day_of_week INT64,
    is_weekend BOOL,
    is_holiday BOOL,
    fiscal_year INT64,
    fiscal_quarter INT64
) CLUSTER BY date_key;

-- Dimension: Event Types
CREATE TABLE IF NOT EXISTS `safety_telemetry.dim_event_types` (
    event_type_key STRING NOT NULL,
    event_type STRING NOT NULL,
    event_category STRING,
    event_severity STRING,
    is_critical BOOL,
    is_rare_event BOOL,  -- Flag for rare failure modes
    description STRING
) CLUSTER BY event_type_key;

-- Fact: Trip Safety Metrics
CREATE TABLE IF NOT EXISTS `safety_telemetry.fact_trip_safety` (
    trip_id STRING NOT NULL,
    vehicle_id STRING NOT NULL,
    driver_id STRING,
    date_key DATE NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP,
    trip_duration_seconds INT64,
    trip_distance_km FLOAT64,
    operating_mode STRING,
    -- Safety metrics
    total_events INT64,
    critical_events INT64,
    safety_interventions INT64,
    mode_transitions INT64,
    max_latency_ms FLOAT64,
    avg_latency_ms FLOAT64,
    -- Rare event flags
    has_rare_event BOOL,
    rare_event_count INT64,
    -- Composite metrics
    safe_ride_flag BOOL,  -- True if no critical events
    safety_score FLOAT64,  -- 0-100, higher is safer
    -- Load metadata
    load_timestamp TIMESTAMP NOT NULL
) PARTITION BY date_key
CLUSTER BY vehicle_id, start_timestamp;

-- Fact: Event Details
CREATE TABLE IF NOT EXISTS `safety_telemetry.fact_events` (
    event_id STRING NOT NULL,
    trip_id STRING NOT NULL,
    vehicle_id STRING NOT NULL,
    driver_id STRING,
    date_key DATE NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    event_type_key STRING NOT NULL,
    event_severity STRING,
    intervention_type STRING,
    latency_ms FLOAT64,
    confidence_score FLOAT64,
    is_rare_event BOOL,
    -- Time-to-event features (for survival analysis)
    time_since_trip_start_seconds FLOAT64,
    time_since_last_event_seconds FLOAT64,
    events_in_trip_before INT64,
    -- Load metadata
    load_timestamp TIMESTAMP NOT NULL
) PARTITION BY date_key
CLUSTER BY trip_id, event_timestamp, event_type_key;

-- Fact: Safety Regression Episodes (for modeling)
CREATE TABLE IF NOT EXISTS `safety_telemetry.fact_safety_regressions` (
    regression_id STRING NOT NULL,
    vehicle_id STRING,
    date_key DATE NOT NULL,
    regression_start_timestamp TIMESTAMP NOT NULL,
    regression_end_timestamp TIMESTAMP,
    regression_duration_hours FLOAT64,
    -- Detection metrics
    detection_timestamp TIMESTAMP,  -- When regression was detected
    mttd_hours FLOAT64,  -- Mean Time To Detection
    detection_method STRING,  -- 'changepoint', 'threshold', 'manual'
    -- Regression characteristics
    baseline_hazard_rate FLOAT64,
    regression_hazard_rate FLOAT64,
    hazard_ratio FLOAT64,  -- regression / baseline
    affected_trips INT64,
    affected_events INT64,
    -- Status
    is_resolved BOOL,
    resolution_timestamp TIMESTAMP,
    -- Load metadata
    load_timestamp TIMESTAMP NOT NULL
) PARTITION BY date_key
CLUSTER BY vehicle_id, regression_start_timestamp;

-- ----------------------------------------------------------------------------
-- MODEL OUTPUT TABLES
-- ----------------------------------------------------------------------------

-- Survival model outputs (hazard rates, predictions)
CREATE TABLE IF NOT EXISTS `safety_telemetry.model_survival_outputs` (
    model_run_id STRING NOT NULL,
    model_run_timestamp TIMESTAMP NOT NULL,
    vehicle_id STRING,
    date_key DATE NOT NULL,
    -- Hazard rate estimates
    baseline_hazard_rate FLOAT64,
    hazard_rate_lower_ci FLOAT64,
    hazard_rate_upper_ci FLOAT64,
    -- Predictions
    predicted_time_to_event_hours FLOAT64,
    predicted_time_lower_ci FLOAT64,
    predicted_time_upper_ci FLOAT64,
    -- Model diagnostics
    convergence_flag BOOL,
    rhat_max FLOAT64,
    effective_sample_size INT64,
    -- Metadata
    model_version STRING,
    hyperparameters JSON
) PARTITION BY date_key
CLUSTER BY vehicle_id, model_run_timestamp;

-- Change-point detection outputs
CREATE TABLE IF NOT EXISTS `safety_telemetry.model_changepoint_outputs` (
    model_run_id STRING NOT NULL,
    model_run_timestamp TIMESTAMP NOT NULL,
    vehicle_id STRING,
    date_key DATE NOT NULL,
    -- Change-point detection
    changepoint_detected BOOL,
    changepoint_timestamp TIMESTAMP,
    changepoint_probability FLOAT64,
    -- Pre/post change metrics
    pre_change_hazard_rate FLOAT64,
    post_change_hazard_rate FLOAT64,
    hazard_ratio FLOAT64,
    -- Credible intervals
    hazard_ratio_lower_ci FLOAT64,
    hazard_ratio_upper_ci FLOAT64,
    -- Model diagnostics
    convergence_flag BOOL,
    rhat_max FLOAT64,
    -- Metadata
    model_version STRING,
    hyperparameters JSON
) PARTITION BY date_key
CLUSTER BY vehicle_id, model_run_timestamp;

-- Importance sampling experiment results
CREATE TABLE IF NOT EXISTS `safety_telemetry.model_importance_sampling_results` (
    experiment_id STRING NOT NULL,
    experiment_timestamp TIMESTAMP NOT NULL,
    -- Experiment configuration
    sampling_method STRING,  -- 'uniform', 'importance', 'stratified'
    rare_event_rate FLOAT64,
    sample_size INT64,
    reweighting_scheme STRING,
    -- Results
    detection_sensitivity FLOAT64,  -- True positive rate
    false_positive_rate FLOAT64,
    mttd_hours FLOAT64,
    mttd_improvement_pct FLOAT64,  -- vs baseline
    -- Statistical significance
    p_value FLOAT64,
    effect_size FLOAT64,
    -- Metadata
    experiment_config JSON
) CLUSTER BY experiment_id, experiment_timestamp;

-- ----------------------------------------------------------------------------
-- ALERT TABLES
-- ----------------------------------------------------------------------------

-- Safety alerts (for dashboard and notifications)
CREATE TABLE IF NOT EXISTS `safety_telemetry.alerts` (
    alert_id STRING NOT NULL,
    alert_timestamp TIMESTAMP NOT NULL,
    alert_type STRING NOT NULL,  -- 'regression_detected', 'threshold_exceeded', 'rare_event_spike'
    severity STRING,  -- 'critical', 'warning', 'info'
    vehicle_id STRING,
    trip_id STRING,
    event_id STRING,
    regression_id STRING,
    -- Alert details
    alert_message STRING,
    alert_metric STRING,
    alert_value FLOAT64,
    alert_threshold FLOAT64,
    -- Status
    is_acknowledged BOOL,
    acknowledged_by STRING,
    acknowledged_timestamp TIMESTAMP,
    is_resolved BOOL,
    resolved_timestamp TIMESTAMP,
    -- Metadata
    source_model_run_id STRING,
    notification_sent BOOL
) PARTITION BY DATE(alert_timestamp)
CLUSTER BY alert_timestamp, alert_type, severity;

-- ----------------------------------------------------------------------------
-- INDEXES AND VIEWS (for common queries)
-- ----------------------------------------------------------------------------

-- View: Daily safety summary
CREATE OR REPLACE VIEW `safety_telemetry.v_daily_safety_summary` AS
SELECT
    date_key,
    COUNT(DISTINCT trip_id) AS total_trips,
    COUNT(DISTINCT vehicle_id) AS active_vehicles,
    SUM(total_events) AS total_events,
    SUM(critical_events) AS total_critical_events,
    SUM(safety_interventions) AS total_interventions,
    AVG(safety_score) AS avg_safety_score,
    SUM(CASE WHEN safe_ride_flag THEN 1 ELSE 0 END) AS safe_rides,
    SUM(CASE WHEN has_rare_event THEN 1 ELSE 0 END) AS trips_with_rare_events,
    SUM(rare_event_count) AS total_rare_events
FROM `safety_telemetry.fact_trip_safety`
GROUP BY date_key;

-- View: Vehicle safety trends
CREATE OR REPLACE VIEW `safety_telemetry.v_vehicle_safety_trends` AS
SELECT
    vehicle_id,
    date_key,
    COUNT(DISTINCT trip_id) AS trips,
    AVG(safety_score) AS avg_safety_score,
    SUM(critical_events) AS total_critical_events,
    AVG(avg_latency_ms) AS avg_latency_ms
FROM `safety_telemetry.fact_trip_safety`
GROUP BY vehicle_id, date_key;
