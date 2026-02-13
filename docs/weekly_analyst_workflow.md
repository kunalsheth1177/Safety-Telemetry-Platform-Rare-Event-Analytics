# Weekly Safety Analyst Workflow - Tableau Dashboard

## Overview

This document describes how a safety analyst uses the Tableau dashboard for weekly safety investigations. The workflow is designed to be efficient, systematic, and defensible for safety-critical decision-making.

---

## Monday Morning Routine (30 minutes)

### Step 1: Open Dashboard → Page 1: Fleet Safety Overview

**Time**: 5 minutes

**Actions**:
1. Open Tableau dashboard
2. Navigate to Page 1: Fleet Safety Overview
3. Set date filter to "Last 7 days" (weekend coverage)

**What to Check**:
- **Total Trips**: Verify weekend activity levels (should be 60-80% of weekday average)
- **Safe Ride Rate**: Should be >95%. If below 95%, flag for investigation
- **Critical Events**: Check for spikes. If >10% increase week-over-week, investigate
- **Safety Score Trend**: Look for downward trends (red flags)

**Decision Points**:
- ✅ **All metrics normal**: Proceed to Step 2 (routine check)
- ⚠️ **Anomaly detected**: Note the metric and proceed to Step 2 with focus

**Evidence to Capture**:
- Screenshot of KPI cards
- Note any metrics outside normal ranges

---

### Step 2: Investigate Anomalies → Page 3: Change-Point Detection

**Time**: 10 minutes

**Actions**:
1. Navigate to Page 3: Change-Point Detection
2. Review "Daily Failure Rate Trend" chart
3. Check "Change-Point Detection Indicators" for new detections

**What to Check**:
- **New Regression Detections**: Look for red markers in the last 7 days
- **MTTD**: If regression detected, check MTTD. Target: <24 hours (excellent)
- **Hazard Ratio**: If >1.5, this is a confirmed regression
- **Change-Point Probability**: If >0.5, regression is statistically significant

**Decision Points**:
- ✅ **No new regressions**: Proceed to Step 3 (routine monitoring)
- ⚠️ **Regression detected**: 
  - Note: Detection date, MTTD, Hazard Ratio, Probability
  - Proceed to Step 3 for root cause analysis
  - Flag for engineering team notification

**Evidence to Capture**:
- Screenshot of change-point detection chart
- Export "Change-Point Summary Table" for regressions detected
- Document MTTD and hazard ratio in weekly report

---

### Step 3: Root Cause Analysis → Page 2: Rare Event Monitoring

**Time**: 10 minutes (or longer if regression detected)

**Actions**:
1. Navigate to Page 2: Rare Event Monitoring
2. If regression detected (from Step 2):
   - Filter by regression period (date range from Page 3)
   - Review "Failure Mode Distribution" treemap
3. If routine check:
   - Review "Rare Event Timeline" for patterns
   - Check "Rare Events by Vehicle" heatmap for outliers

**What to Check**:
- **Top Failure Modes**: Which failure modes are most common?
- **Vehicle Patterns**: Are specific vehicles or models affected?
- **Latency Patterns**: Are rare events correlated with high latency?
- **Intervention Patterns**: What types of interventions are most common?

**Decision Points**:
- ✅ **No patterns identified**: Document as routine monitoring
- ⚠️ **Pattern identified**:
  - Document failure mode, affected vehicles, latency patterns
  - Export "Rare Event Details Table" filtered by pattern
  - Create ticket for engineering team with evidence

**Evidence to Capture**:
- Screenshot of failure mode distribution
- Export filtered rare event details (CSV)
- Document patterns in weekly report

---

### Step 4: Method Validation → Page 4: MTTD Comparison

**Time**: 5 minutes

**Actions**:
1. Navigate to Page 4: MTTD Comparison
2. Review "MTTD Comparison Bar Chart"
3. Check "MTTD Improvement Percentage" chart

**What to Check**:
- **MTTD Improvement**: Did importance sampling improve MTTD?
  - Target: 30-40% improvement vs baseline
- **Sensitivity**: Did detection sensitivity improve?
  - Target: >85% sensitivity with importance sampling
- **Method Performance**: Which method performed best this week?

**Decision Points**:
- ✅ **Methods performing as expected**: Document in weekly report
- ⚠️ **Performance degradation**: 
  - Investigate if sampling method needs adjustment
  - Review with data science team

**Evidence to Capture**:
- Screenshot of MTTD comparison
- Note improvement percentages in weekly report

---

## Weekly Report Generation (1 hour)

### Section 1: Executive Summary (Page 1)

**Content**:
- KPI snapshot (Total Trips, Safe Ride Rate, Critical Events)
- Week-over-week comparison
- Safety score trend chart
- Key highlights (good news) and concerns (red flags)

**Format**: 
- Screenshot of Page 1 with annotations
- Table with week-over-week metrics

**Audience**: Leadership, Safety Engineering Manager

---

### Section 2: Regression Analysis (Page 3)

**Content**:
- List of regressions detected this week
- For each regression:
  - Detection date and MTTD
  - Hazard ratio and probability
  - Status (resolved/pending/investigation)
- MTTD summary statistics
- Trend analysis (improving/worsening)

**Format**:
- Table exported from "Change-Point Summary Table"
- Chart showing MTTD distribution
- Narrative describing each regression

**Audience**: Safety Engineering Team, Data Science Team

---

### Section 3: Rare Event Summary (Page 2)

**Content**:
- Top 5 failure modes (by count)
- Vehicle-level breakdown (which vehicles had most rare events)
- Intervention patterns (takeover vs brake vs steer)
- Latency analysis (are rare events correlated with high latency?)

**Format**:
- Treemap screenshot (failure mode distribution)
- Table of top vehicles with rare events
- Scatter plot (latency vs confidence)
- Narrative describing patterns

**Audience**: Safety Engineering Team, Vehicle Engineering Team

---

### Section 4: Method Performance (Page 4)

**Content**:
- MTTD improvement metrics (this week)
- Sensitivity comparison
- Method recommendations
- Performance trends (improving/degrading)

**Format**:
- Bar chart (MTTD comparison)
- Scatter plot (method performance)
- Table with improvement percentages
- Narrative with recommendations

**Audience**: Data Science Team, Safety Analytics Team

---

## Ad-Hoc Investigations

### When Alert Received (Email/Slack)

**Scenario**: Alert received for regression detection or threshold exceeded

**Workflow** (15 minutes):

1. **Navigate to Page 3** → Find alert date
   - Filter by date range around alert
   - Check change-point probability and hazard ratio
   - Verify if this is a true regression or false positive

2. **Navigate to Page 2** → Filter by date and failure mode
   - Review rare events during alert period
   - Check if specific failure mode is driving the alert
   - Identify affected vehicles

3. **Export Evidence**
   - Export event details (CSV)
   - Screenshot relevant charts
   - Document findings

4. **Update Dashboard Filters**
   - Set filters to monitor resolution
   - Create bookmark for tracking

5. **Notify Engineering Team**
   - Send alert details with evidence
   - Include exported CSV and screenshots
   - Request investigation

---

### When Vehicle Issue Reported

**Scenario**: Engineering team reports issue with specific vehicle

**Workflow** (10 minutes):

1. **Navigate to Page 2** → Filter by Vehicle ID
   - Review rare event history for this vehicle
   - Check latency patterns
   - Review intervention types

2. **Navigate to Page 1** → Compare to fleet average
   - Check if vehicle's safety score is below fleet average
   - Compare critical event rate to fleet average
   - Identify if this is an isolated issue or fleet-wide

3. **Export Vehicle Report**
   - Export vehicle-specific rare events
   - Screenshot vehicle performance vs fleet
   - Document findings

4. **Provide Analysis**
   - Send vehicle report to engineering team
   - Include recommendations (firmware update, maintenance, etc.)

---

## Best Practices

### Data Quality Checks

**Before Starting Analysis**:
- Verify extract refresh completed (check manifest timestamp)
- Check for missing dates in time series
- Verify vehicle counts match expected (200 vehicles)

**During Analysis**:
- Cross-reference metrics across pages
- Verify calculations (e.g., safe ride rate = safe rides / total trips)
- Check for data anomalies (negative values, impossible dates)

### Documentation

**Always Document**:
- Date and time of analysis
- Filters applied
- Key findings
- Screenshots with annotations
- Exported data files

**Weekly Report Template**:
- Executive Summary (1 page)
- Regression Analysis (2-3 pages)
- Rare Event Summary (2 pages)
- Method Performance (1 page)
- Appendix: Exported data, detailed charts

### Collaboration

**Share Findings**:
- Use Tableau Server/Online for team access
- Create bookmarks for specific investigations
- Share exported CSVs via shared drive
- Document in JIRA/Confluence tickets

**Escalation**:
- Critical regression (hazard ratio >2.0, MTTD >72h): Immediate escalation
- Pattern identified (3+ vehicles, same failure mode): Escalate within 24h
- Routine findings: Include in weekly report

---

## Troubleshooting

### Dashboard Not Loading
- Check extract refresh status
- Verify CSV files exist in `tableau/extracts/`
- Check Tableau Server connection

### Missing Data
- Verify Airflow pipeline completed successfully
- Check extract generation script ran
- Review manifest.json for extract timestamps

### Unexpected Metrics
- Verify filters are set correctly
- Check calculated fields for errors
- Review data source joins

### Performance Issues
- Use data extracts (.hyper) instead of live connections
- Limit date range to last 90 days
- Enable query caching

---

## Weekly Checklist

- [ ] Monday: Complete morning routine (30 min)
- [ ] Monday: Generate weekly report (1 hour)
- [ ] Monday: Share report with stakeholders
- [ ] Tuesday-Friday: Monitor for alerts
- [ ] Friday: Review week's regressions and resolutions
- [ ] Friday: Update dashboard bookmarks for next week

---

## Success Metrics

**Dashboard Usage**:
- Weekly report generated on time: 100%
- Ad-hoc investigations completed within SLA: >95%
- Stakeholder satisfaction: >4.0/5.0

**Analysis Quality**:
- Regression detection accuracy: >90%
- MTTD improvement: 30-40% vs baseline
- False positive rate: <10%

**Impact**:
- Safety regressions detected faster (MTTD <24h)
- Root cause identification improved (patterns identified)
- Engineering team response time improved

---

*Last Updated: 2024-01-15*  
*Dashboard Version: 1.0.0*
