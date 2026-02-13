"""
Synthetic Data Generator for Safety Telemetry Platform

Generates realistic vehicle telemetry data including:
- Trips with location, duration, mode
- Safety events (interventions, faults, transitions)
- Rare events with configurable rates
- Temporal patterns (regressions, improvements)
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
import numpy as np
import pandas as pd


class SyntheticDataGenerator:
    """Generate synthetic safety telemetry data with realistic patterns."""
    
    def __init__(
        self,
        start_date: datetime,
        days: int,
        trips_per_day: int = 1000,
        rare_event_rate: float = 0.001,
        regression_probability: float = 0.1,
        seed: Optional[int] = None
    ):
        """
        Initialize generator.
        
        Args:
            start_date: Start date for data generation
            days: Number of days to generate
            trips_per_day: Average trips per day
            rare_event_rate: Base rate of rare events (per trip)
            regression_probability: Probability of a safety regression period
            seed: Random seed for reproducibility
        """
        self.start_date = start_date
        self.days = days
        self.trips_per_day = trips_per_day
        self.rare_event_rate = rare_event_rate
        self.regression_probability = regression_probability
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Vehicle and driver pools
        self.vehicle_ids = [f"VH_{i:05d}" for i in range(1, 201)]  # 200 vehicles
        self.driver_ids = [f"DR_{i:05d}" for i in range(1, 501)]  # 500 drivers
        
        # Event types and categories
        self.event_types = {
            'safety_intervention': {
                'severities': ['critical', 'warning'],
                'categories': ['perception', 'planning', 'control'],
                'interventions': ['takeover', 'brake', 'steer', 'none']
            },
            'fault': {
                'severities': ['critical', 'warning', 'info'],
                'categories': ['perception', 'planning', 'control', 'system'],
                'fault_codes': ['FAULT_001', 'FAULT_002', 'FAULT_003', 'FAULT_004']
            },
            'mode_transition': {
                'severities': ['info'],
                'categories': ['system'],
                'reasons': ['user_request', 'system_fault', 'safety_intervention', 'planned']
            },
            'latency_spike': {
                'severities': ['warning', 'info'],
                'categories': ['system'],
                'threshold_ms': 100.0
            }
        }
        
        # Rare event types (low probability, high impact)
        self.rare_event_types = [
            'RARE_CRITICAL_FAULT',
            'RARE_PERCEPTION_FAILURE',
            'RARE_CONTROL_DEGRADATION',
            'RARE_SYSTEM_CASCADE'
        ]
        
        # Operating modes
        self.operating_modes = ['autonomous', 'manual', 'transition']
        
        # Weather and road conditions
        self.weather_conditions = ['clear', 'rain', 'snow', 'fog', 'wind']
        self.road_types = ['highway', 'urban', 'rural', 'parking']
        
        # Track regression periods
        self.regression_periods = self._generate_regression_periods()
    
    def _generate_regression_periods(self) -> List[Dict[str, Any]]:
        """Generate random safety regression periods."""
        periods = []
        current_date = self.start_date
        
        for _ in range(self.days):
            if random.random() < self.regression_probability:
                # Regression period: 3-7 days
                duration = random.randint(3, 7)
                periods.append({
                    'start': current_date,
                    'end': current_date + timedelta(days=duration),
                    'hazard_multiplier': random.uniform(1.5, 3.0)  # 1.5x to 3x increase
                })
                current_date += timedelta(days=duration)
            else:
                current_date += timedelta(days=1)
        
        return periods
    
    def _is_in_regression(self, timestamp: datetime) -> bool:
        """Check if timestamp is in a regression period."""
        for period in self.regression_periods:
            if period['start'] <= timestamp <= period['end']:
                return True, period['hazard_multiplier']
        return False, 1.0
    
    def generate_trip(self, trip_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Generate a single trip record."""
        vehicle_id = random.choice(self.vehicle_ids)
        driver_id = random.choice(self.driver_ids)
        
        # Trip duration: 10-120 minutes
        duration_minutes = random.uniform(10, 120)
        duration_seconds = int(duration_minutes * 60)
        
        # Distance: roughly 5-100 km
        distance_km = duration_minutes * random.uniform(0.5, 1.2)
        
        end_timestamp = timestamp + timedelta(seconds=duration_seconds)
        
        return {
            'trip_id': trip_id,
            'vehicle_id': vehicle_id,
            'driver_id': driver_id,
            'start_timestamp': timestamp.isoformat(),
            'end_timestamp': end_timestamp.isoformat(),
            'start_location_lat': random.uniform(37.0, 38.0),  # SF Bay Area
            'start_location_lon': random.uniform(-122.5, -121.5),
            'end_location_lat': random.uniform(37.0, 38.0),
            'end_location_lon': random.uniform(-122.5, -121.5),
            'trip_distance_km': round(distance_km, 2),
            'trip_duration_seconds': duration_seconds,
            'operating_mode': random.choice(self.operating_modes),
            'weather_condition': random.choice(self.weather_conditions),
            'road_type': random.choice(self.road_types),
            'ingestion_timestamp': datetime.utcnow().isoformat(),
            'source_file': 'synthetic_generator'
        }
    
    def generate_events_for_trip(
        self,
        trip_id: str,
        vehicle_id: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        trip_duration_seconds: int
    ) -> List[Dict[str, Any]]:
        """Generate events for a trip."""
        events = []
        event_id_counter = 0
        
        # Check if in regression period
        in_regression, hazard_mult = self._is_in_regression(start_timestamp)
        
        # Base event rate (events per hour)
        base_rate = random.uniform(0.5, 2.0)  # 0.5-2 events per hour
        if in_regression:
            base_rate *= hazard_mult
        
        # Expected number of events
        trip_hours = trip_duration_seconds / 3600
        expected_events = base_rate * trip_hours
        num_events = np.random.poisson(expected_events)
        
        # Generate regular events
        for i in range(num_events):
            event_time_offset = random.uniform(0, trip_duration_seconds)
            event_timestamp = start_timestamp + timedelta(seconds=event_time_offset)
            
            event_type = random.choice(list(self.event_types.keys()))
            event_config = self.event_types[event_type]
            
            event = {
                'event_id': f"{trip_id}_EVT_{event_id_counter:03d}",
                'trip_id': trip_id,
                'vehicle_id': vehicle_id,
                'event_timestamp': event_timestamp.isoformat(),
                'event_type': event_type,
                'event_severity': random.choice(event_config['severities']),
                'event_category': random.choice(event_config['categories']),
                'event_subcategory': f"{event_type}_sub_{random.randint(1, 5)}",
                'event_description': f"{event_type} event during trip",
                'intervention_type': (
                    random.choice(event_config['interventions'])
                    if 'interventions' in event_config else None
                ),
                'fault_code': (
                    random.choice(event_config['fault_codes'])
                    if 'fault_codes' in event_config else None
                ),
                'latency_ms': (
                    random.uniform(50, 200) if event_type == 'latency_spike'
                    else random.uniform(10, 100)
                ),
                'confidence_score': random.uniform(0.7, 1.0),
                'sensor_data': json.dumps({'sensor_id': f"SENS_{random.randint(1, 10)}"}),
                'metadata': json.dumps({'generated': True}),
                'ingestion_timestamp': datetime.utcnow().isoformat(),
                'source_file': 'synthetic_generator'
            }
            events.append(event)
            event_id_counter += 1
        
        # Generate rare events (with low probability)
        if random.random() < self.rare_event_rate:
            rare_event_time_offset = random.uniform(0, trip_duration_seconds)
            rare_event_timestamp = start_timestamp + timedelta(seconds=rare_event_time_offset)
            
            rare_event = {
                'event_id': f"{trip_id}_RARE_{event_id_counter:03d}",
                'trip_id': trip_id,
                'vehicle_id': vehicle_id,
                'event_timestamp': rare_event_timestamp.isoformat(),
                'event_type': random.choice(self.rare_event_types),
                'event_severity': 'critical',
                'event_category': random.choice(['perception', 'planning', 'control', 'system']),
                'event_subcategory': 'rare_failure_mode',
                'event_description': 'Rare safety-critical event',
                'intervention_type': 'takeover',
                'fault_code': 'RARE_FAULT',
                'latency_ms': random.uniform(200, 500),
                'confidence_score': random.uniform(0.3, 0.7),  # Lower confidence for rare events
                'sensor_data': json.dumps({'rare_event': True}),
                'metadata': json.dumps({'rare_event': True, 'generated': True}),
                'ingestion_timestamp': datetime.utcnow().isoformat(),
                'source_file': 'synthetic_generator'
            }
            events.append(rare_event)
        
        return events
    
    def generate_mode_transitions(
        self,
        trip_id: str,
        vehicle_id: str,
        start_timestamp: datetime,
        end_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Generate mode transition events."""
        transitions = []
        transition_id_counter = 0
        
        # 0-3 transitions per trip
        num_transitions = random.randint(0, 3)
        
        current_mode = random.choice(self.operating_modes)
        current_time = start_timestamp
        
        for _ in range(num_transitions):
            # Transition after 20-40% of trip
            time_offset = random.uniform(0.2, 0.4) * (end_timestamp - start_timestamp).total_seconds()
            transition_timestamp = start_timestamp + timedelta(seconds=time_offset)
            
            # Choose next mode
            next_mode = random.choice([m for m in self.operating_modes if m != current_mode])
            
            transition = {
                'transition_id': f"{trip_id}_TRN_{transition_id_counter:03d}",
                'trip_id': trip_id,
                'vehicle_id': vehicle_id,
                'transition_timestamp': transition_timestamp.isoformat(),
                'from_mode': current_mode,
                'to_mode': next_mode,
                'transition_reason': random.choice(['user_request', 'system_fault', 'safety_intervention', 'planned']),
                'transition_duration_seconds': random.uniform(1.0, 5.0),
                'context_data': json.dumps({'auto_generated': True}),
                'ingestion_timestamp': datetime.utcnow().isoformat(),
                'source_file': 'synthetic_generator'
            }
            transitions.append(transition)
            
            current_mode = next_mode
            current_time = transition_timestamp
            transition_id_counter += 1
        
        return transitions
    
    def generate_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all data for the specified period."""
        all_trips = []
        all_events = []
        all_transitions = []
        
        trip_counter = 0
        current_date = self.start_date
        
        print(f"Generating data for {self.days} days...")
        
        for day in range(self.days):
            date = current_date + timedelta(days=day)
            
            # Vary trips per day (80-120% of average)
            daily_trips = int(self.trips_per_day * random.uniform(0.8, 1.2))
            
            for trip_num in range(daily_trips):
                # Distribute trips throughout the day
                hour = random.randint(6, 22)  # 6 AM to 10 PM
                minute = random.randint(0, 59)
                trip_timestamp = date.replace(hour=hour, minute=minute, second=0)
                
                trip_id = f"TRIP_{date.strftime('%Y%m%d')}_{trip_counter:06d}"
                trip_counter += 1
                
                # Generate trip
                trip = self.generate_trip(trip_id, trip_timestamp)
                all_trips.append(trip)
                
                # Generate events
                events = self.generate_events_for_trip(
                    trip_id,
                    trip['vehicle_id'],
                    trip_timestamp,
                    datetime.fromisoformat(trip['end_timestamp']),
                    trip['trip_duration_seconds']
                )
                all_events.extend(events)
                
                # Generate mode transitions
                transitions = self.generate_mode_transitions(
                    trip_id,
                    trip['vehicle_id'],
                    trip_timestamp,
                    datetime.fromisoformat(trip['end_timestamp'])
                )
                all_transitions.extend(transitions)
            
            if (day + 1) % 10 == 0:
                print(f"  Generated {day + 1}/{self.days} days ({len(all_trips)} trips)")
        
        print(f"Generation complete: {len(all_trips)} trips, {len(all_events)} events, {len(all_transitions)} transitions")
        
        return {
            'trips': all_trips,
            'events': all_events,
            'transitions': all_transitions
        }
    
    def save_to_jsonl(self, data: Dict[str, List[Dict[str, Any]]], output_dir: Path):
        """Save data to JSONL files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for data_type, records in data.items():
            output_file = output_dir / f"{data_type}.jsonl"
            with open(output_file, 'w') as f:
                for record in records:
                    f.write(json.dumps(record) + '\n')
            print(f"Saved {len(records)} {data_type} to {output_file}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Generate synthetic safety telemetry data')
    parser.add_argument('--output', type=str, default='./data/synthetic',
                       help='Output directory for generated data')
    parser.add_argument('--days', type=int, default=90,
                       help='Number of days to generate')
    parser.add_argument('--trips-per-day', type=int, default=1000,
                       help='Average trips per day')
    parser.add_argument('--rare-event-rate', type=float, default=0.001,
                       help='Rare event rate (per trip)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    parser.add_argument('--start-date', type=str, default=None,
                       help='Start date (YYYY-MM-DD), defaults to 90 days ago')
    
    args = parser.parse_args()
    
    # Determine start date
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    else:
        start_date = datetime.now() - timedelta(days=args.days)
    
    # Generate data
    generator = SyntheticDataGenerator(
        start_date=start_date,
        days=args.days,
        trips_per_day=args.trips_per_day,
        rare_event_rate=args.rare_event_rate,
        seed=args.seed
    )
    
    data = generator.generate_all_data()
    
    # Save to files
    output_dir = Path(args.output)
    generator.save_to_jsonl(data, output_dir)
    
    print(f"\nData generation complete. Files saved to: {output_dir}")


if __name__ == '__main__':
    main()
