-- ============================================================================
-- Analytics Views for Common Queries
-- ============================================================================

-- View: Weekly Safety Trends
CREATE OR REPLACE VIEW `safety_telemetry.v_weekly_safety_trends` AS
SELECT
    EXTRACT(YEAR FROM date_key) AS year,
    EXTRACT(WEEK FROM date_key) AS week,
    COUNT(DISTINCT trip_id) AS total_trips,
    COUNT(DISTINCT vehicle_id) AS active_vehicles,
    SUM(total_events) AS total_events,
    SUM(critical_events) AS total_critical_events,
    SUM(safety_interventions) AS total_interventions,
    AVG(safety_score) AS avg_safety_score,
    SUM(CASE WHEN safe_ride_flag THEN 1 ELSE 0 END) AS safe_rides,
    SUM(CASE WHEN safe_ride_flag THEN 1 ELSE 0 END) / COUNT(*) AS safe_ride_rate,
    SUM(CASE WHEN has_rare_event THEN 1 ELSE 0 END) AS trips_with_rare_events,
    SUM(rare_event_count) AS total_rare_events,
    AVG(avg_latency_ms) AS avg_latency_ms,
    MAX(max_latency_ms) AS max_latency_ms
FROM `safety_telemetry.fact_trip_safety`
GROUP BY year, week
ORDER BY year DESC, week DESC;

-- View: Vehicle Safety Performance
CREATE OR REPLACE VIEW `safety_telemetry.v_vehicle_safety_performance` AS
SELECT
    v.vehicle_id,
    v.vehicle_model,
    v.firmware_version,
    COUNT(DISTINCT f.trip_id) AS total_trips,
    AVG(f.safety_score) AS avg_safety_score,
    SUM(f.critical_events) AS total_critical_events,
    SUM(f.total_events) AS total_events,
    SUM(f.safety_interventions) AS total_interventions,
    AVG(f.avg_latency_ms) AS avg_latency_ms,
    SUM(CASE WHEN f.safe_ride_flag THEN 1 ELSE 0 END) / COUNT(*) AS safe_ride_rate,
    SUM(CASE WHEN f.has_rare_event THEN 1 ELSE 0 END) AS trips_with_rare_events,
    MIN(f.date_key) AS first_trip_date,
    MAX(f.date_key) AS last_trip_date
FROM `safety_telemetry.fact_trip_safety` f
INNER JOIN `safety_telemetry.dim_vehicles` v ON f.vehicle_id = v.vehicle_id
WHERE v.is_current = TRUE
GROUP BY v.vehicle_id, v.vehicle_model, v.firmware_version;

-- View: Rare Event Analysis
CREATE OR REPLACE VIEW `safety_telemetry.v_rare_event_analysis` AS
SELECT
    e.event_type_key,
    et.event_category,
    et.event_severity,
    DATE(e.event_timestamp) AS event_date,
    COUNT(*) AS event_count,
    COUNT(DISTINCT e.trip_id) AS affected_trips,
    COUNT(DISTINCT e.vehicle_id) AS affected_vehicles,
    AVG(e.latency_ms) AS avg_latency_ms,
    AVG(e.confidence_score) AS avg_confidence_score,
    AVG(e.time_since_trip_start_seconds) AS avg_time_since_trip_start
FROM `safety_telemetry.fact_events` e
INNER JOIN `safety_telemetry.dim_event_types` et ON e.event_type_key = et.event_type_key
WHERE e.is_rare_event = TRUE
GROUP BY e.event_type_key, et.event_category, et.event_severity, DATE(e.event_timestamp)
ORDER BY event_date DESC, event_count DESC;

-- View: Safety Regression Summary
CREATE OR REPLACE VIEW `safety_telemetry.v_safety_regression_summary` AS
SELECT
    r.regression_id,
    r.vehicle_id,
    v.vehicle_model,
    r.date_key,
    r.regression_start_timestamp,
    r.regression_end_timestamp,
    r.regression_duration_hours,
    r.detection_timestamp,
    r.mttd_hours,
    r.detection_method,
    r.baseline_hazard_rate,
    r.regression_hazard_rate,
    r.hazard_ratio,
    r.affected_trips,
    r.affected_events,
    r.is_resolved,
    r.resolution_timestamp,
    CASE
        WHEN r.mttd_hours < 24 THEN 'excellent'
        WHEN r.mttd_hours < 72 THEN 'good'
        WHEN r.mttd_hours < 168 THEN 'acceptable'
        ELSE 'poor'
    END AS mttd_category
FROM `safety_telemetry.fact_safety_regressions` r
LEFT JOIN `safety_telemetry.dim_vehicles` v ON r.vehicle_id = v.vehicle_id AND v.is_current = TRUE
ORDER BY r.regression_start_timestamp DESC;

-- View: Event Type Distribution
CREATE OR REPLACE VIEW `safety_telemetry.v_event_type_distribution` AS
SELECT
    et.event_type_key,
    et.event_category,
    et.event_severity,
    et.is_critical,
    et.is_rare_event,
    COUNT(*) AS total_events,
    COUNT(DISTINCT e.trip_id) AS affected_trips,
    COUNT(DISTINCT e.vehicle_id) AS affected_vehicles,
    AVG(e.latency_ms) AS avg_latency_ms,
    AVG(e.confidence_score) AS avg_confidence_score,
    MIN(e.event_timestamp) AS first_occurrence,
    MAX(e.event_timestamp) AS last_occurrence
FROM `safety_telemetry.fact_events` e
INNER JOIN `safety_telemetry.dim_event_types` et ON e.event_type_key = et.event_type_key
GROUP BY et.event_type_key, et.event_category, et.event_severity, et.is_critical, et.is_rare_event
ORDER BY total_events DESC;
