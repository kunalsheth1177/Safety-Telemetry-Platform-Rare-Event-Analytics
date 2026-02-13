-- ============================================================================
-- Staging to Analytics Transformation SQL
-- ============================================================================
-- Transforms raw staging data into star schema analytics tables
-- Designed for BigQuery but adaptable to other SQL engines
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Dimension: Time
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.dim_time`
SELECT DISTINCT
    date_key,
    EXTRACT(YEAR FROM date_key) AS year,
    EXTRACT(QUARTER FROM date_key) AS quarter,
    EXTRACT(MONTH FROM date_key) AS month,
    EXTRACT(WEEK FROM date_key) AS week,
    EXTRACT(DAYOFYEAR FROM date_key) AS day_of_year,
    EXTRACT(DAY FROM date_key) AS day_of_month,
    EXTRACT(DAYOFWEEK FROM date_key) AS day_of_week,
    EXTRACT(DAYOFWEEK FROM date_key) IN (1, 7) AS is_weekend,
    FALSE AS is_holiday,  -- Simplified; can be enhanced with holiday table
    EXTRACT(YEAR FROM date_key) AS fiscal_year,
    EXTRACT(QUARTER FROM date_key) AS fiscal_quarter
FROM (
    SELECT DISTINCT DATE(start_timestamp) AS date_key
    FROM `safety_telemetry.staging_trips`
    WHERE DATE(start_timestamp) NOT IN (
        SELECT date_key FROM `safety_telemetry.dim_time`
    )
);

-- ----------------------------------------------------------------------------
-- Dimension: Vehicles (SCD Type 2)
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.dim_vehicles`
SELECT DISTINCT
    vehicle_id,
    CONCAT('Model_', CAST(MOD(ABS(FARM_FINGERPRINT(vehicle_id)), 10) AS STRING)) AS vehicle_model,
    CAST(2020 + MOD(ABS(FARM_FINGERPRINT(vehicle_id)), 5) AS INT64) AS vehicle_year,
    CONCAT('FW_', CAST(MOD(ABS(FARM_FINGERPRINT(vehicle_id)), 3) AS STRING)) AS firmware_version,
    CONCAT('HW_', CAST(MOD(ABS(FARM_FINGERPRINT(vehicle_id)), 2) AS STRING)) AS hardware_config,
    MIN(DATE(start_timestamp)) AS first_seen_date,
    MAX(DATE(start_timestamp)) AS last_seen_date,
    COUNT(DISTINCT trip_id) AS total_trips,
    CURRENT_TIMESTAMP() AS valid_from,
    CAST(NULL AS TIMESTAMP) AS valid_to,
    TRUE AS is_current
FROM `safety_telemetry.staging_trips`
WHERE vehicle_id NOT IN (
    SELECT vehicle_id FROM `safety_telemetry.dim_vehicles` WHERE is_current = TRUE
)
GROUP BY vehicle_id;

-- ----------------------------------------------------------------------------
-- Dimension: Drivers
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.dim_drivers`
SELECT DISTINCT
    driver_id,
    CAST(2 + MOD(ABS(FARM_FINGERPRINT(driver_id)), 20) AS INT64) AS driver_experience_years,
    CASE MOD(ABS(FARM_FINGERPRINT(driver_id)), 3)
        WHEN 0 THEN 'professional'
        WHEN 1 THEN 'consumer'
        ELSE 'test'
    END AS driver_category,
    MIN(DATE(start_timestamp)) AS first_seen_date,
    MAX(DATE(start_timestamp)) AS last_seen_date,
    CURRENT_TIMESTAMP() AS valid_from,
    CAST(NULL AS TIMESTAMP) AS valid_to,
    TRUE AS is_current
FROM `safety_telemetry.staging_trips`
WHERE driver_id IS NOT NULL
    AND driver_id NOT IN (
        SELECT driver_id FROM `safety_telemetry.dim_drivers` WHERE is_current = TRUE
    )
GROUP BY driver_id;

-- ----------------------------------------------------------------------------
-- Dimension: Event Types
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.dim_event_types`
SELECT DISTINCT
    event_type AS event_type_key,
    event_type,
    event_category,
    event_severity,
    event_severity = 'critical' AS is_critical,
    -- Mark rare events (events with 'RARE' prefix or specific fault codes)
    STARTS_WITH(event_type, 'RARE') OR fault_code = 'RARE_FAULT' AS is_rare_event,
    event_description
FROM `safety_telemetry.staging_events`
WHERE event_type NOT IN (
    SELECT event_type_key FROM `safety_telemetry.dim_event_types`
);

-- ----------------------------------------------------------------------------
-- Fact: Trip Safety Metrics
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.fact_trip_safety`
SELECT
    t.trip_id,
    t.vehicle_id,
    t.driver_id,
    DATE(t.start_timestamp) AS date_key,
    t.start_timestamp,
    t.end_timestamp,
    t.trip_duration_seconds,
    t.trip_distance_km,
    t.operating_mode,
    -- Event counts
    COALESCE(event_counts.total_events, 0) AS total_events,
    COALESCE(event_counts.critical_events, 0) AS critical_events,
    COALESCE(event_counts.safety_interventions, 0) AS safety_interventions,
    COALESCE(transition_counts.mode_transitions, 0) AS mode_transitions,
    -- Latency metrics
    event_counts.max_latency_ms,
    event_counts.avg_latency_ms,
    -- Rare event flags
    COALESCE(event_counts.has_rare_event, FALSE) AS has_rare_event,
    COALESCE(event_counts.rare_event_count, 0) AS rare_event_count,
    -- Composite metrics
    COALESCE(event_counts.critical_events, 0) = 0 AS safe_ride_flag,
    -- Safety score: 100 - (critical_events * 20) - (total_events * 2), min 0
    GREATEST(0, 100 - (COALESCE(event_counts.critical_events, 0) * 20) - (COALESCE(event_counts.total_events, 0) * 2)) AS safety_score,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `safety_telemetry.staging_trips` t
LEFT JOIN (
    SELECT
        trip_id,
        COUNT(*) AS total_events,
        SUM(CASE WHEN event_severity = 'critical' THEN 1 ELSE 0 END) AS critical_events,
        SUM(CASE WHEN event_type = 'safety_intervention' THEN 1 ELSE 0 END) AS safety_interventions,
        MAX(latency_ms) AS max_latency_ms,
        AVG(latency_ms) AS avg_latency_ms,
        BOOL_OR(STARTS_WITH(event_type, 'RARE') OR fault_code = 'RARE_FAULT') AS has_rare_event,
        SUM(CASE WHEN STARTS_WITH(event_type, 'RARE') OR fault_code = 'RARE_FAULT' THEN 1 ELSE 0 END) AS rare_event_count
    FROM `safety_telemetry.staging_events`
    GROUP BY trip_id
) event_counts ON t.trip_id = event_counts.trip_id
LEFT JOIN (
    SELECT
        trip_id,
        COUNT(*) AS mode_transitions
    FROM `safety_telemetry.staging_mode_transitions`
    GROUP BY trip_id
) transition_counts ON t.trip_id = transition_counts.trip_id
WHERE t.trip_id NOT IN (
    SELECT trip_id FROM `safety_telemetry.fact_trip_safety`
);

-- ----------------------------------------------------------------------------
-- Fact: Event Details
-- ----------------------------------------------------------------------------
INSERT INTO `safety_telemetry.fact_events`
SELECT
    e.event_id,
    e.trip_id,
    e.vehicle_id,
    t.driver_id,
    DATE(e.event_timestamp) AS date_key,
    e.event_timestamp,
    e.event_type AS event_type_key,
    e.event_severity,
    e.intervention_type,
    e.latency_ms,
    e.confidence_score,
    STARTS_WITH(e.event_type, 'RARE') OR e.fault_code = 'RARE_FAULT' AS is_rare_event,
    -- Time-to-event features
    TIMESTAMP_DIFF(e.event_timestamp, t.start_timestamp, SECOND) AS time_since_trip_start_seconds,
    TIMESTAMP_DIFF(
        e.event_timestamp,
        COALESCE(
            LAG(e.event_timestamp) OVER (PARTITION BY e.trip_id ORDER BY e.event_timestamp),
            t.start_timestamp
        ),
        SECOND
    ) AS time_since_last_event_seconds,
    ROW_NUMBER() OVER (PARTITION BY e.trip_id ORDER BY e.event_timestamp) - 1 AS events_in_trip_before,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `safety_telemetry.staging_events` e
INNER JOIN `safety_telemetry.staging_trips` t ON e.trip_id = t.trip_id
WHERE e.event_id NOT IN (
    SELECT event_id FROM `safety_telemetry.fact_events`
);

-- ----------------------------------------------------------------------------
-- Fact: Safety Regression Episodes (detected via change-point model)
-- ----------------------------------------------------------------------------
-- This table is populated by the change-point detection model
-- Placeholder query structure for manual regression entry
INSERT INTO `safety_telemetry.fact_safety_regressions`
SELECT
    CONCAT('REGR_', FORMAT_TIMESTAMP('%Y%m%d_%H%M%S', CURRENT_TIMESTAMP()), '_', vehicle_id) AS regression_id,
    vehicle_id,
    date_key,
    regression_start_timestamp,
    regression_end_timestamp,
    TIMESTAMP_DIFF(regression_end_timestamp, regression_start_timestamp, HOUR) AS regression_duration_hours,
    detection_timestamp,
    TIMESTAMP_DIFF(detection_timestamp, regression_start_timestamp, HOUR) AS mttd_hours,
    'changepoint' AS detection_method,
    baseline_hazard_rate,
    regression_hazard_rate,
    regression_hazard_rate / NULLIF(baseline_hazard_rate, 0) AS hazard_ratio,
    affected_trips,
    affected_events,
    FALSE AS is_resolved,
    CAST(NULL AS TIMESTAMP) AS resolution_timestamp,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM (
    -- This would be populated from model outputs
    -- For now, this is a placeholder structure
    SELECT
        vehicle_id,
        DATE(regression_start_timestamp) AS date_key,
        regression_start_timestamp,
        regression_end_timestamp,
        detection_timestamp,
        baseline_hazard_rate,
        regression_hazard_rate,
        affected_trips,
        affected_events
    FROM `safety_telemetry.model_changepoint_outputs`
    WHERE changepoint_detected = TRUE
        AND changepoint_timestamp NOT IN (
            SELECT regression_start_timestamp FROM `safety_telemetry.fact_safety_regressions`
        )
);
