"""
Change-Point Detection Model for MTTD Improvement

Uses PyMC to detect shifts in hazard rates (safety regressions) with:
- Bayesian change-point detection
- Credible intervals on change-point location
- Pre/post change hazard rate estimation
- MTTD calculation
"""

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import json


class ChangepointModel:
    """
    Bayesian change-point model for detecting safety regression shifts.
    
    Models time series of event counts with a potential change-point
    where the hazard rate shifts (regression onset).
    """
    
    def __init__(
        self,
        samples: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        random_seed: int = 42
    ):
        """
        Initialize change-point model.
        
        Args:
            samples: Number of posterior samples
            tune: Number of tuning samples
            chains: Number of MCMC chains
            random_seed: Random seed for reproducibility
        """
        self.samples = samples
        self.tune = tune
        self.chains = chains
        self.random_seed = random_seed
        self.model = None
        self.trace = None
        self.idata = None
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        time_col: str = 'date_key',
        event_count_col: str = 'critical_events',
        vehicle_col: Optional[str] = 'vehicle_id',
        exposure_col: Optional[str] = 'trip_count'
    ) -> Dict[str, np.ndarray]:
        """
        Prepare time series data for change-point detection.
        
        Args:
            df: DataFrame with time series data
            time_col: Column name for time (date or timestamp)
            event_count_col: Column name for event counts
            vehicle_col: Column name for vehicle ID (None for aggregate)
            exposure_col: Column name for exposure (e.g., trip count)
        
        Returns:
            Dictionary with prepared arrays
        """
        # Sort by time
        df_sorted = df.sort_values(time_col).copy()
        
        # Convert time to numeric (days since start)
        if df_sorted[time_col].dtype == 'object' or 'datetime' in str(df_sorted[time_col].dtype):
            df_sorted[time_col] = pd.to_datetime(df_sorted[time_col])
            start_date = df_sorted[time_col].min()
            df_sorted['time_numeric'] = (df_sorted[time_col] - start_date).dt.total_seconds() / 86400
        else:
            df_sorted['time_numeric'] = df_sorted[time_col]
            start_date = None
        
        # Aggregate if vehicle_col is provided
        if vehicle_col and vehicle_col in df_sorted.columns:
            # Group by vehicle and time
            grouped = df_sorted.groupby([vehicle_col, time_col]).agg({
                event_count_col: 'sum',
                exposure_col: 'sum' if exposure_col else 'count'
            }).reset_index()
            
            # For each vehicle, create time series
            vehicles = grouped[vehicle_col].unique()
            all_data = []
            vehicle_ids_list = []
            
            for vehicle_id in vehicles:
                vehicle_data = grouped[grouped[vehicle_col] == vehicle_id].sort_values(time_col)
                if len(vehicle_data) >= 10:  # Minimum data points
                    all_data.append({
                        'time': vehicle_data['time_numeric'].values,
                        'events': vehicle_data[event_count_col].values,
                        'exposure': vehicle_data[exposure_col].values if exposure_col else np.ones(len(vehicle_data)),
                        'dates': vehicle_data[time_col].values
                    })
                    vehicle_ids_list.append(vehicle_id)
            
            return {
                'time_series': all_data,
                'vehicle_ids': vehicle_ids_list,
                'start_date': start_date
            }
        else:
            # Aggregate across all vehicles
            grouped = df_sorted.groupby(time_col).agg({
                event_count_col: 'sum',
                exposure_col: 'sum' if exposure_col else 'count'
            }).reset_index()
            
            return {
                'time': grouped['time_numeric'].values,
                'events': grouped[event_count_col].values,
                'exposure': grouped[exposure_col].values if exposure_col else np.ones(len(grouped)),
                'dates': grouped[time_col].values,
                'start_date': start_date
            }
    
    def build_model(
        self,
        time: np.ndarray,
        events: np.ndarray,
        exposure: np.ndarray
    ) -> pm.Model:
        """
        Build PyMC change-point model.
        
        Model specification:
        - Poisson likelihood for event counts
        - Change-point tau (discrete)
        - Pre-change hazard rate: lambda_pre
        - Post-change hazard rate: lambda_post
        - Hazard ratio: lambda_post / lambda_pre
        """
        n = len(time)
        
        with pm.Model() as model:
            # Prior on change-point location (discrete uniform)
            tau = pm.DiscreteUniform('tau', lower=1, upper=n-1)
            
            # Pre-change hazard rate (events per unit exposure)
            lambda_pre = pm.Gamma('lambda_pre', alpha=2.0, beta=1.0)
            
            # Post-change hazard rate
            # Assume regression increases hazard, so lambda_post > lambda_pre
            hazard_ratio = pm.Gamma('hazard_ratio', alpha=2.0, beta=0.5)  # Mean ~4x
            lambda_post = pm.Deterministic('lambda_post', lambda_pre * hazard_ratio)
            
            # Time-dependent hazard rate
            lambda_t = pt.switch(
                pt.arange(n) < tau,
                lambda_pre,
                lambda_post
            )
            
            # Expected event count
            mu = lambda_t * exposure
            
            # Likelihood (Poisson)
            events_obs = pm.Poisson('events_obs', mu=mu, observed=events)
            
            # Derived quantities
            changepoint_probability = pm.Deterministic(
                'changepoint_probability',
                pm.math.sigmoid((tau - n/2) * 0.1)  # Simplified probability
            )
        
        self.model = model
        return model
    
    def fit(
        self,
        data: Dict[str, Any],
        vehicle_idx: Optional[int] = None,
        progressbar: bool = True
    ) -> az.InferenceData:
        """
        Fit change-point model.
        
        Args:
            data: Prepared data dictionary
            vehicle_idx: Index of vehicle to fit (None for aggregate)
            progressbar: Show progress bar
        
        Returns:
            ArviZ InferenceData object
        """
        if 'time_series' in data:
            # Multiple vehicles
            if vehicle_idx is None:
                raise ValueError("Must specify vehicle_idx when data contains multiple vehicles")
            
            ts_data = data['time_series'][vehicle_idx]
            time = ts_data['time']
            events = ts_data['events']
            exposure = ts_data['exposure']
        else:
            # Single aggregate time series
            time = data['time']
            events = data['events']
            exposure = data['exposure']
        
        self.build_model(time, events, exposure)
        
        with self.model:
            self.trace = pm.sample(
                draws=self.samples,
                tune=self.tune,
                chains=self.chains,
                random_seed=self.random_seed,
                progressbar=progressbar,
                return_inferencedata=True,
                step=pm.Metropolis()  # Required for discrete tau
            )
            self.idata = self.trace
        
        return self.idata
    
    def detect_changepoint(
        self,
        data: Dict[str, Any],
        vehicle_idx: Optional[int] = None,
        threshold_probability: float = 0.5
    ) -> Dict[str, Any]:
        """
        Detect change-point and compute MTTD.
        
        Args:
            data: Prepared data dictionary
            vehicle_idx: Vehicle index (if applicable)
            threshold_probability: Minimum probability for detection
        
        Returns:
            Dictionary with detection results
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        posterior = self.idata.posterior
        
        # Get change-point samples
        tau_samples = posterior['tau'].values.flatten()
        lambda_pre_samples = posterior['lambda_pre'].values.flatten()
        lambda_post_samples = posterior['lambda_post'].values.flatten()
        hazard_ratio_samples = posterior['hazard_ratio'].values.flatten()
        
        # Get time series data
        if 'time_series' in data:
            ts_data = data['time_series'][vehicle_idx]
            time = ts_data['time']
            dates = ts_data['dates']
        else:
            time = data['time']
            dates = data['dates']
        
        # Most likely change-point
        tau_mode = int(np.argmax(np.bincount(tau_samples.astype(int))))
        changepoint_time = time[tau_mode]
        
        # Change-point probability (simplified)
        changepoint_prob = np.mean(tau_samples > len(time) * 0.2)  # Not at very beginning
        
        # Hazard rates
        lambda_pre_mean = np.mean(lambda_pre_samples)
        lambda_post_mean = np.mean(lambda_post_samples)
        hazard_ratio_mean = np.mean(hazard_ratio_samples)
        hazard_ratio_lower = np.quantile(hazard_ratio_samples, 0.025)
        hazard_ratio_upper = np.quantile(hazard_ratio_samples, 0.975)
        
        # MTTD: Time from change-point to detection
        # In practice, detection happens when model is run
        detection_time = time[-1]  # Assume detection at end of time series
        mttd_hours = (detection_time - changepoint_time) * 24  # Convert days to hours
        
        # Convert to datetime if possible
        if 'start_date' in data and data['start_date'] is not None:
            changepoint_date = data['start_date'] + timedelta(days=changepoint_time)
        else:
            changepoint_date = None
        
        return {
            'changepoint_detected': changepoint_prob > threshold_probability,
            'changepoint_timestamp': changepoint_date.isoformat() if changepoint_date else None,
            'changepoint_time_numeric': changepoint_time,
            'changepoint_probability': float(changepoint_prob),
            'pre_change_hazard_rate': float(lambda_pre_mean),
            'post_change_hazard_rate': float(lambda_post_mean),
            'hazard_ratio': float(hazard_ratio_mean),
            'hazard_ratio_lower_ci': float(hazard_ratio_lower),
            'hazard_ratio_upper_ci': float(hazard_ratio_upper),
            'mttd_hours': float(mttd_hours)
        }
    
    def get_diagnostics(self) -> pd.DataFrame:
        """Get model diagnostics."""
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        return az.summary(self.idata)
    
    def save_results(
        self,
        output_path: str,
        data: Dict[str, Any],
        vehicle_id: Optional[str] = None,
        model_version: str = "1.0.0"
    ) -> pd.DataFrame:
        """
        Save model results to BigQuery-compatible format.
        
        Args:
            output_path: Output file path
            data: Original data dictionary
            vehicle_id: Vehicle ID (if applicable)
            model_version: Model version string
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        # Detect change-point
        vehicle_idx = 0 if 'time_series' in data else None
        detection = self.detect_changepoint(data, vehicle_idx=vehicle_idx)
        
        # Get diagnostics
        diagnostics = self.get_diagnostics()
        max_rhat = diagnostics['r_hat'].max() if 'r_hat' in diagnostics.columns else 1.0
        
        # Create results record
        result = {
            'model_run_id': f"CP_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'model_run_timestamp': datetime.utcnow().isoformat(),
            'vehicle_id': vehicle_id or 'AGGREGATE',
            'date_key': datetime.utcnow().date().isoformat(),
            'changepoint_detected': detection['changepoint_detected'],
            'changepoint_timestamp': detection['changepoint_timestamp'],
            'changepoint_probability': detection['changepoint_probability'],
            'pre_change_hazard_rate': detection['pre_change_hazard_rate'],
            'post_change_hazard_rate': detection['post_change_hazard_rate'],
            'hazard_ratio': detection['hazard_ratio'],
            'hazard_ratio_lower_ci': detection['hazard_ratio_lower_ci'],
            'hazard_ratio_upper_ci': detection['hazard_ratio_upper_ci'],
            'convergence_flag': max_rhat < 1.01,
            'rhat_max': float(max_rhat),
            'model_version': model_version,
            'hyperparameters': json.dumps({
                'samples': self.samples,
                'tune': self.tune,
                'chains': self.chains
            })
        }
        
        # Save to CSV
        df_results = pd.DataFrame([result])
        df_results.to_csv(output_path, index=False)
        
        return df_results


def main():
    """Example usage."""
    # Generate synthetic time series data
    np.random.seed(42)
    n_days = 90
    
    # Simulate change-point at day 30
    changepoint_day = 30
    lambda_pre = 0.5  # events per trip
    lambda_post = 2.0  # 4x increase
    
    time = np.arange(n_days)
    trips_per_day = np.random.poisson(100, n_days)
    events = np.concatenate([
        np.random.poisson(lambda_pre * trips_per_day[:changepoint_day]),
        np.random.poisson(lambda_post * trips_per_day[changepoint_day:])
    ])
    
    data = {
        'time': time,
        'events': events,
        'exposure': trips_per_day,
        'dates': pd.date_range('2024-01-01', periods=n_days),
        'start_date': pd.Timestamp('2024-01-01')
    }
    
    # Fit model
    model = ChangepointModel(samples=1000, tune=500, chains=2)
    idata = model.fit(data)
    
    # Detect change-point
    detection = model.detect_changepoint(data)
    print(f"Change-point detected: {detection['changepoint_detected']}")
    print(f"Change-point day: {detection['changepoint_time_numeric']:.1f}")
    print(f"Hazard ratio: {detection['hazard_ratio']:.2f}")
    print(f"MTTD: {detection['mttd_hours']:.1f} hours")
    
    # Save results
    model.save_results('changepoint_model_results.csv', data)


if __name__ == '__main__':
    main()
