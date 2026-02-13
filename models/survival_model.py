"""
Survival Model for Safety Regression Detection

Uses PyMC to model time-to-event (safety regression) with:
- Weibull hazard function
- Vehicle-level random effects
- Credible intervals
- Posterior predictive checks
"""

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json


class SurvivalModel:
    """
    Bayesian survival model for time-to-safety-regression.
    
    Models the hazard rate of safety regressions using a Weibull distribution
    with vehicle-level random effects.
    """
    
    def __init__(
        self,
        samples: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        random_seed: int = 42
    ):
        """
        Initialize survival model.
        
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
        time_col: str = 'time_to_event_hours',
        event_col: str = 'regression_occurred',
        vehicle_col: str = 'vehicle_id'
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data for survival analysis.
        
        Args:
            df: DataFrame with survival data
            time_col: Column name for time to event
            event_col: Column name for event indicator (1 = occurred, 0 = censored)
            vehicle_col: Column name for vehicle ID
        
        Returns:
            Dictionary with prepared arrays
        """
        # Filter out missing values
        df_clean = df[[time_col, event_col, vehicle_col]].dropna()
        
        # Create vehicle index mapping
        vehicle_ids = df_clean[vehicle_col].unique()
        vehicle_to_idx = {vid: idx for idx, vid in enumerate(vehicle_ids)}
        df_clean['vehicle_idx'] = df_clean[vehicle_col].map(vehicle_to_idx)
        
        return {
            'time': df_clean[time_col].values,
            'event': df_clean[event_col].values.astype(int),
            'vehicle_idx': df_clean['vehicle_idx'].values,
            'n_vehicles': len(vehicle_ids),
            'vehicle_ids': vehicle_ids
        }
    
    def build_model(self, data: Dict[str, np.ndarray]) -> pm.Model:
        """
        Build PyMC survival model.
        
        Model specification:
        - Weibull hazard: h(t) = (alpha/lambda) * (t/lambda)^(alpha-1)
        - Vehicle random effects on scale parameter
        - Log-normal priors for hyperparameters
        """
        time = data['time']
        event = data['event']
        vehicle_idx = data['vehicle_idx']
        n_vehicles = data['n_vehicles']
        
        with pm.Model() as model:
            # Hyperparameters
            alpha_mu = pm.Normal('alpha_mu', mu=1.0, sigma=0.5)  # Shape parameter
            alpha_sigma = pm.HalfNormal('alpha_sigma', sigma=0.3)
            
            # Vehicle-level random effects on scale parameter (lambda)
            lambda_mu = pm.Normal('lambda_mu', mu=100.0, sigma=50.0)  # Scale parameter
            lambda_sigma = pm.HalfNormal('lambda_sigma', sigma=20.0)
            lambda_vehicle = pm.Normal(
                'lambda_vehicle',
                mu=lambda_mu,
                sigma=lambda_sigma,
                shape=n_vehicles
            )
            
            # Individual-level parameters
            alpha = pm.Lognormal('alpha', mu=alpha_mu, sigma=alpha_sigma)
            lambda_i = pm.Deterministic(
                'lambda_i',
                pt.exp(pt.log(lambda_vehicle[vehicle_idx]))
            )
            
            # Weibull survival model
            # Log-likelihood for Weibull survival
            # For event=1: log(hazard) + log(survival)
            # For event=0: log(survival)
            
            log_hazard = (
                pt.log(alpha) - alpha * pt.log(lambda_i) +
                (alpha - 1) * pt.log(time)
            )
            log_survival = -pt.power(time / lambda_i, alpha)
            
            # Log-likelihood
            log_likelihood = event * (log_hazard + log_survival) + (1 - event) * log_survival
            
            # Likelihood
            pm.Potential('log_likelihood', log_likelihood)
            
            # Derived quantities
            hazard_rate = pm.Deterministic(
                'hazard_rate',
                (alpha / lambda_i) * pt.power(time / lambda_i, alpha - 1)
            )
            
            mean_time_to_event = pm.Deterministic(
                'mean_time_to_event',
                lambda_i * pt.gamma(1 + 1/alpha)
            )
        
        self.model = model
        return model
    
    def fit(
        self,
        data: Dict[str, np.ndarray],
        progressbar: bool = True
    ) -> az.InferenceData:
        """
        Fit the survival model using MCMC.
        
        Args:
            data: Prepared data dictionary
            progressbar: Show progress bar
        
        Returns:
            ArviZ InferenceData object
        """
        if self.model is None:
            self.build_model(data)
        
        with self.model:
            self.trace = pm.sample(
                draws=self.samples,
                tune=self.tune,
                chains=self.chains,
                random_seed=self.random_seed,
                progressbar=progressbar,
                return_inferencedata=True
            )
            self.idata = self.trace
        
        return self.idata
    
    def predict_hazard_rate(
        self,
        time_points: np.ndarray,
        vehicle_idx: Optional[int] = None,
        quantiles: Tuple[float, float] = (0.025, 0.975)
    ) -> Dict[str, np.ndarray]:
        """
        Predict hazard rates at given time points.
        
        Args:
            time_points: Array of time points (hours)
            vehicle_idx: Vehicle index (None for population average)
            quantiles: Credible interval quantiles
        
        Returns:
            Dictionary with mean, lower CI, upper CI
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        posterior = self.idata.posterior
        
        # Get posterior samples
        alpha_samples = posterior['alpha'].values.flatten()
        if vehicle_idx is not None:
            lambda_samples = np.exp(posterior['lambda_vehicle'].isel(vehicle_idx=vehicle_idx).values.flatten())
        else:
            lambda_samples = np.exp(posterior['lambda_mu'].values.flatten())
        
        # Compute hazard for each time point
        n_samples = len(alpha_samples)
        n_times = len(time_points)
        
        hazard_samples = np.zeros((n_samples, n_times))
        for i, t in enumerate(time_points):
            for j in range(n_samples):
                alpha = alpha_samples[j]
                lam = lambda_samples[j]
                if t > 0:
                    hazard_samples[j, i] = (alpha / lam) * ((t / lam) ** (alpha - 1))
        
        # Compute statistics
        mean_hazard = np.mean(hazard_samples, axis=0)
        lower_ci = np.quantile(hazard_samples, quantiles[0], axis=0)
        upper_ci = np.quantile(hazard_samples, quantiles[1], axis=0)
        
        return {
            'time_points': time_points,
            'mean_hazard_rate': mean_hazard,
            'hazard_rate_lower_ci': lower_ci,
            'hazard_rate_upper_ci': upper_ci
        }
    
    def predict_time_to_event(
        self,
        vehicle_idx: Optional[int] = None,
        quantiles: Tuple[float, float] = (0.025, 0.975)
    ) -> Dict[str, float]:
        """
        Predict mean time to event.
        
        Args:
            vehicle_idx: Vehicle index (None for population average)
            quantiles: Credible interval quantiles
        
        Returns:
            Dictionary with mean, lower CI, upper CI
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        posterior = self.idata.posterior
        
        if vehicle_idx is not None:
            mean_ttf = posterior['mean_time_to_event'].isel(vehicle_idx=vehicle_idx).values.flatten()
        else:
            # Population average
            alpha_samples = posterior['alpha'].values.flatten()
            lambda_samples = np.exp(posterior['lambda_mu'].values.flatten())
            mean_ttf = lambda_samples * np.array([np.math.gamma(1 + 1/a) for a in alpha_samples])
        
        return {
            'mean_time_to_event': float(np.mean(mean_ttf)),
            'time_to_event_lower_ci': float(np.quantile(mean_ttf, quantiles[0])),
            'time_to_event_upper_ci': float(np.quantile(mean_ttf, quantiles[1]))
        }
    
    def posterior_predictive_check(
        self,
        data: Dict[str, np.ndarray],
        n_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Perform posterior predictive check.
        
        Args:
            data: Original data
            n_samples: Number of posterior predictive samples
        
        Returns:
            Dictionary with check results
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        with self.model:
            ppc = pm.sample_posterior_predictive(
                self.idata,
                predictions=True,
                random_seed=self.random_seed
            )
        
        # Compare observed vs predicted event rates
        observed_event_rate = np.mean(data['event'])
        # Note: This is simplified; full PPC would compare distributions
        
        return {
            'observed_event_rate': observed_event_rate,
            'posterior_predictive_samples': ppc,
            'convergence_diagnostics': az.summary(self.idata)
        }
    
    def get_diagnostics(self) -> pd.DataFrame:
        """
        Get model diagnostics (R-hat, ESS, etc.).
        
        Returns:
            DataFrame with diagnostics
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        return az.summary(self.idata)
    
    def save_results(
        self,
        output_path: str,
        data: Dict[str, np.ndarray],
        model_version: str = "1.0.0"
    ):
        """
        Save model results to BigQuery-compatible format.
        
        Args:
            output_path: Output file path
            data: Original data dictionary
            model_version: Model version string
        """
        if self.idata is None:
            raise ValueError("Model must be fitted first")
        
        posterior = self.idata.posterior
        
        # Extract key statistics
        results = []
        for vehicle_idx in range(data['n_vehicles']):
            vehicle_id = data['vehicle_ids'][vehicle_idx]
            
            # Get vehicle-specific predictions
            preds = self.predict_time_to_event(vehicle_idx=vehicle_idx)
            hazard_preds = self.predict_hazard_rate(
                time_points=np.array([24.0, 168.0]),  # 1 day, 1 week
                vehicle_idx=vehicle_idx
            )
            
            # Get diagnostics
            diagnostics = self.get_diagnostics()
            max_rhat = diagnostics['r_hat'].max()
            min_ess = diagnostics['ess_bulk'].min()
            
            results.append({
                'model_run_id': f"SRV_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'model_run_timestamp': datetime.utcnow().isoformat(),
                'vehicle_id': vehicle_id,
                'date_key': datetime.utcnow().date().isoformat(),
                'baseline_hazard_rate': float(np.mean(hazard_preds['mean_hazard_rate'])),
                'hazard_rate_lower_ci': float(np.mean(hazard_preds['hazard_rate_lower_ci'])),
                'hazard_rate_upper_ci': float(np.mean(hazard_preds['hazard_rate_upper_ci'])),
                'predicted_time_to_event_hours': preds['mean_time_to_event'],
                'predicted_time_lower_ci': preds['time_to_event_lower_ci'],
                'predicted_time_upper_ci': preds['time_to_event_upper_ci'],
                'convergence_flag': max_rhat < 1.01,
                'rhat_max': float(max_rhat),
                'effective_sample_size': int(min_ess),
                'model_version': model_version,
                'hyperparameters': json.dumps({
                    'samples': self.samples,
                    'tune': self.tune,
                    'chains': self.chains
                })
            })
        
        # Save to CSV (can be loaded to BigQuery)
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        
        return df_results


def main():
    """Example usage."""
    # Generate synthetic survival data
    np.random.seed(42)
    n_vehicles = 50
    n_observations = 500
    
    # Simulate data
    vehicle_ids = [f"VH_{i:05d}" for i in range(n_vehicles)]
    data_dict = {
        'time': np.random.weibull(1.5, n_observations) * 100,  # hours
        'event': np.random.binomial(1, 0.7, n_observations),
        'vehicle_idx': np.random.randint(0, n_vehicles, n_observations),
        'n_vehicles': n_vehicles,
        'vehicle_ids': vehicle_ids
    }
    
    # Fit model
    model = SurvivalModel(samples=1000, tune=500, chains=2)
    idata = model.fit(data_dict)
    
    # Get predictions
    preds = model.predict_time_to_event()
    print(f"Mean time to event: {preds['mean_time_to_event']:.2f} hours")
    print(f"95% CI: [{preds['time_to_event_lower_ci']:.2f}, {preds['time_to_event_upper_ci']:.2f}]")
    
    # Diagnostics
    diagnostics = model.get_diagnostics()
    print("\nModel Diagnostics:")
    print(diagnostics.head())
    
    # Save results
    model.save_results('survival_model_results.csv', data_dict)


if __name__ == '__main__':
    main()
