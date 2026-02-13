"""
Tests for data ingestion module.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json
from ingestion.generator import SyntheticDataGenerator
from ingestion.loader import DataLoader
from datetime import datetime, timedelta


def test_generator_creates_trips():
    """Test that generator creates trip data."""
    generator = SyntheticDataGenerator(
        start_date=datetime.now() - timedelta(days=7),
        days=7,
        trips_per_day=10,
        seed=42
    )
    
    data = generator.generate_all_data()
    
    assert 'trips' in data
    assert len(data['trips']) > 0
    assert 'trip_id' in data['trips'][0]
    assert 'vehicle_id' in data['trips'][0]


def test_generator_creates_events():
    """Test that generator creates event data."""
    generator = SyntheticDataGenerator(
        start_date=datetime.now() - timedelta(days=7),
        days=7,
        trips_per_day=10,
        seed=42
    )
    
    data = generator.generate_all_data()
    
    assert 'events' in data
    assert len(data['events']) > 0
    assert 'event_id' in data['events'][0]
    assert 'event_type' in data['events'][0]


def test_generator_rare_events():
    """Test that generator creates rare events."""
    generator = SyntheticDataGenerator(
        start_date=datetime.now() - timedelta(days=7),
        days=7,
        trips_per_day=100,
        rare_event_rate=0.1,  # 10% for testing
        seed=42
    )
    
    data = generator.generate_all_data()
    
    rare_events = [e for e in data['events'] if 'RARE' in e.get('event_type', '')]
    
    # Should have some rare events with 10% rate
    assert len(rare_events) > 0


def test_loader_saves_jsonl():
    """Test that generator saves to JSONL."""
    generator = SyntheticDataGenerator(
        start_date=datetime.now() - timedelta(days=1),
        days=1,
        trips_per_day=5,
        seed=42
    )
    
    data = generator.generate_all_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator.save_to_jsonl(data, output_dir)
        
        trips_file = output_dir / 'trips.jsonl'
        assert trips_file.exists()
        
        # Verify JSONL format
        with open(trips_file, 'r') as f:
            line = f.readline()
            assert line.strip()
            json.loads(line)  # Should be valid JSON


def test_loader_creates_tables():
    """Test that loader creates local tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'test.db'
        
        loader = DataLoader(target='local', local_db_path=str(db_path))
        
        # Check that tables exist
        conn = loader.conn
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'staging_%'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'staging_trips' in tables
        assert 'staging_events' in tables
        assert 'staging_mode_transitions' in tables
        
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__])
