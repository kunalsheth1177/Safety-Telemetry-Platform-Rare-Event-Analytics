"""
Tests for statistical models.
"""

import pytest
import numpy as np
import pandas as pd
from models.survival_model import SurvivalModel
from models.changepoint_model import ChangepointModel
from models.importance_sampling import ImportanceSampling
from datetime import datetime, timedelta


def test_survival_model_prepare_data():
    """Test survival model data preparation."""
    np.random.seed(42)
    n_samples = 100
    
    df = pd.DataFrame({
        'vehicle_id': [f"VH_{i:05d}" for i in np.random.randint(1, 21, n_samples)],
        'time_to_event_hours': np.random.weibull(1.5, n_samples) * 100,
        'regression_occurred': np.random.binomial(1, 0.7, n_samples)
    })
    
    model = SurvivalModel()
    data = model.prepare_data(df)
    
    assert 'time' in data
    assert 'event' in data
    assert 'vehicle_idx' in data
    assert len(data['time']) == n_samples
    assert data['n_vehicles'] > 0


def test_survival_model_build():
    """Test survival model building."""
    np.random.seed(42)
    n_vehicles = 10
    n_samples = 50
    
    data = {
        'time': np.random.weibull(1.5, n_samples) * 100,
        'event': np.random.binomial(1, 0.7, n_samples),
        'vehicle_idx': np.random.randint(0, n_vehicles, n_samples),
        'n_vehicles': n_vehicles,
        'vehicle_ids': [f"VH_{i:05d}" for i in range(n_vehicles)]
    }
    
    model = SurvivalModel(samples=100, tune=50, chains=1)  # Small for testing
    model.build_model(data)
    
    assert model.model is not None


def test_changepoint_model_prepare_data():
    """Test change-point model data preparation."""
    np.random.seed(42)
    n_days = 30
    
    dates = pd.date_range('2024-01-01', periods=n_days)
    df = pd.DataFrame({
        'date_key': dates,
        'critical_events': np.random.poisson(2, n_days),
        'trip_count': np.random.poisson(100, n_days)
    })
    
    model = ChangepointModel()
    data = model.prepare_data(df, time_col='date_key', event_count_col='critical_events')
    
    assert 'time' in data or 'time_series' in data
    assert 'events' in data or 'time_series' in data


def test_importance_sampling_compute_weights():
    """Test importance sampling weight computation."""
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'feature1': np.random.uniform(0, 1, n_samples),
        'feature2': np.random.uniform(0, 1, n_samples),
        'has_rare_event': np.random.binomial(1, 0.01, n_samples)
    })
    
    is_sampler = ImportanceSampling(rare_event_rate=0.01)
    
    # Test uniform weights
    weights_uniform = is_sampler.compute_importance_weights(df, method='uniform')
    assert len(weights_uniform) == n_samples
    assert np.allclose(weights_uniform, 1.0)
    
    # Test stratified weights
    weights_stratified = is_sampler.compute_importance_weights(df, method='stratified')
    assert len(weights_stratified) == n_samples
    assert np.all(weights_stratified > 0)


def test_importance_sampling_resample():
    """Test importance sampling resampling."""
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'feature1': np.random.uniform(0, 1, n_samples),
        'feature2': np.random.uniform(0, 1, n_samples),
        'has_rare_event': np.random.binomial(1, 0.01, n_samples)
    })
    
    is_sampler = ImportanceSampling(rare_event_rate=0.01)
    
    df_resampled = is_sampler.resample(df, method='stratified', n_samples=500)
    
    assert len(df_resampled) == 500
    assert 'has_rare_event' in df_resampled.columns


if __name__ == '__main__':
    pytest.main([__file__])
