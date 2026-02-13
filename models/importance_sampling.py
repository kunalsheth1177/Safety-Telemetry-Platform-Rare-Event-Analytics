"""
Importance Sampling / Reweighting for Rare Event Detection

Implements reweighting schemes to upweight rare event strata,
improving detection sensitivity and reducing MTTD.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from datetime import datetime
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_recall_curve, roc_auc_score, confusion_matrix,
    classification_report
)


class ImportanceSampling:
    """
    Importance sampling for rare event detection.
    
    Implements multiple reweighting schemes:
    1. Uniform sampling (baseline)
    2. Stratified sampling (by rare event flag)
    3. Importance sampling (by predicted rare event probability)
    4. Adaptive sampling (dynamic reweighting)
    """
    
    def __init__(
        self,
        rare_event_label: str = 'has_rare_event',
        rare_event_rate: float = 0.001
    ):
        """
        Initialize importance sampling.
        
        Args:
            rare_event_label: Column name for rare event indicator
            rare_event_rate: Expected rare event rate in population
        """
        self.rare_event_label = rare_event_label
        self.rare_event_rate = rare_event_rate
        self.reweighting_model = None
    
    def compute_importance_weights(
        self,
        df: pd.DataFrame,
        method: str = 'stratified',
        target_rate: Optional[float] = None
    ) -> np.ndarray:
        """
        Compute importance weights for samples.
        
        Args:
            df: DataFrame with rare event labels
            method: 'uniform', 'stratified', 'importance', 'adaptive'
            target_rate: Target rare event rate (for stratified)
        
        Returns:
            Array of importance weights
        """
        if method == 'uniform':
            return np.ones(len(df))
        
        elif method == 'stratified':
            # Upweight rare events to achieve target rate
            if target_rate is None:
                target_rate = 0.1  # 10% rare events in sample
            
            rare_count = df[self.rare_event_label].sum()
            total_count = len(df)
            current_rate = rare_count / total_count if total_count > 0 else 0
            
            if current_rate == 0:
                return np.ones(len(df))
            
            # Compute weights
            weights = np.ones(len(df))
            rare_weight = target_rate / current_rate
            normal_weight = (1 - target_rate) / (1 - current_rate)
            
            weights[df[self.rare_event_label] == 1] = rare_weight
            weights[df[self.rare_event_label] == 0] = normal_weight
            
            # Normalize
            weights = weights / weights.sum() * len(df)
            
            return weights
        
        elif method == 'importance':
            # Use predicted probabilities from model
            if self.reweighting_model is None:
                raise ValueError("Must fit reweighting model first")
            
            # Get predicted probabilities
            feature_cols = [c for c in df.columns if c != self.rare_event_label]
            X = df[feature_cols].values
            probs = self.reweighting_model.predict_proba(X)[:, 1]
            
            # Importance weights: inverse of sampling probability
            # Upweight samples with high rare event probability
            weights = probs / self.rare_event_rate
            weights = weights / weights.sum() * len(df)
            
            return weights
        
        elif method == 'adaptive':
            # Adaptive: combine stratified and importance
            stratified_weights = self.compute_importance_weights(
                df, method='stratified', target_rate=0.1
            )
            
            if self.reweighting_model is not None:
                importance_weights = self.compute_importance_weights(
                    df, method='importance'
                )
                # Combine: weighted average
                weights = 0.5 * stratified_weights + 0.5 * importance_weights
            else:
                weights = stratified_weights
            
            return weights
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def fit_reweighting_model(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ):
        """
        Fit a model to predict rare event probability.
        
        Args:
            df: Training DataFrame
            feature_cols: Feature columns (None = all except label)
        """
        if feature_cols is None:
            feature_cols = [c for c in df.columns if c != self.rare_event_label]
        
        X = df[feature_cols].values
        y = df[self.rare_event_label].values
        
        # Use class weights to handle imbalance
        from sklearn.utils.class_weight import compute_sample_weight
        sample_weights = compute_sample_weight('balanced', y)
        
        self.reweighting_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            class_weight='balanced',
            random_state=42
        )
        self.reweighting_model.fit(X, y, sample_weight=sample_weights)
    
    def resample(
        self,
        df: pd.DataFrame,
        method: str = 'stratified',
        n_samples: Optional[int] = None,
        target_rate: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Resample data using importance sampling.
        
        Args:
            df: Input DataFrame
            method: Sampling method
            n_samples: Number of samples (None = same as input)
            target_rate: Target rare event rate
        
        Returns:
            Resampled DataFrame
        """
        if n_samples is None:
            n_samples = len(df)
        
        weights = self.compute_importance_weights(df, method, target_rate)
        
        # Sample with replacement using weights
        indices = np.random.choice(
            len(df),
            size=n_samples,
            replace=True,
            p=weights / weights.sum()
        )
        
        return df.iloc[indices].copy()
    
    def evaluate_detection_performance(
        self,
        df_train: pd.DataFrame,
        df_test: pd.DataFrame,
        methods: List[str] = ['uniform', 'stratified', 'importance', 'adaptive'],
        feature_cols: Optional[List[str]] = None,
        detection_model: Optional[Callable] = None
    ) -> pd.DataFrame:
        """
        Evaluate detection performance across sampling methods.
        
        Args:
            df_train: Training data
            df_test: Test data (held out)
            methods: List of sampling methods to compare
            feature_cols: Feature columns
            detection_model: Detection model (None = use default)
        
        Returns:
            DataFrame with performance metrics
        """
        if feature_cols is None:
            feature_cols = [c for c in df_train.columns if c != self.rare_event_label]
        
        results = []
        
        for method in methods:
            print(f"\nEvaluating method: {method}")
            
            # Fit reweighting model if needed
            if method in ['importance', 'adaptive']:
                if self.reweighting_model is None:
                    self.fit_reweighting_model(df_train, feature_cols)
            
            # Resample training data
            df_resampled = self.resample(df_train, method=method)
            
            # Train detection model
            if detection_model is None:
                from sklearn.ensemble import RandomForestClassifier
                detection_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    class_weight='balanced',
                    random_state=42
                )
            
            X_train = df_resampled[feature_cols].values
            y_train = df_resampled[self.rare_event_label].values
            detection_model.fit(X_train, y_train)
            
            # Evaluate on test set
            X_test = df_test[feature_cols].values
            y_test = df_test[self.rare_event_label].values
            
            y_pred = detection_model.predict(X_test)
            y_pred_proba = detection_model.predict_proba(X_test)[:, 1]
            
            # Compute metrics
            cm = confusion_matrix(y_test, y_pred)
            tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
            
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0.0
            
            # Compute MTTD (simplified: time to first detection)
            # In practice, this would be computed from time series
            mttd_hours = self._estimate_mttd(y_test, y_pred)
            
            results.append({
                'method': method,
                'sensitivity': sensitivity,
                'specificity': specificity,
                'precision': precision,
                'false_positive_rate': fpr,
                'auc': auc,
                'mttd_hours': mttd_hours,
                'tp': int(tp),
                'fp': int(fp),
                'tn': int(tn),
                'fn': int(fn)
            })
        
        return pd.DataFrame(results)
    
    def _estimate_mttd(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """
        Estimate MTTD from predictions.
        
        Simplified: assumes events occur at regular intervals.
        In practice, would use actual timestamps.
        """
        # Find first true positive
        tp_indices = np.where((y_true == 1) & (y_pred == 1))[0]
        if len(tp_indices) > 0:
            first_detection = tp_indices[0]
            # Assume daily data, convert to hours
            return float(first_detection * 24)
        else:
            # No detection
            return float('inf')
    
    def run_experiment(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Run complete importance sampling experiment.
        
        Args:
            df: Full dataset
            feature_cols: Feature columns
            test_size: Test set fraction
            random_seed: Random seed
        
        Returns:
            Dictionary with experiment results
        """
        np.random.seed(random_seed)
        
        # Split data
        df_train, df_test = train_test_split(
            df,
            test_size=test_size,
            random_state=random_seed,
            stratify=df[self.rare_event_label] if self.rare_event_label in df.columns else None
        )
        
        # Evaluate methods
        results_df = self.evaluate_detection_performance(
            df_train,
            df_test,
            methods=['uniform', 'stratified', 'importance', 'adaptive'],
            feature_cols=feature_cols
        )
        
        # Compute improvements vs baseline
        baseline_sensitivity = results_df[results_df['method'] == 'uniform']['sensitivity'].values[0]
        baseline_mttd = results_df[results_df['method'] == 'uniform']['mttd_hours'].values[0]
        
        results_df['sensitivity_improvement'] = (
            (results_df['sensitivity'] - baseline_sensitivity) / baseline_sensitivity * 100
        )
        results_df['mttd_improvement_pct'] = (
            (baseline_mttd - results_df['mttd_hours']) / baseline_mttd * 100
        )
        
        # Statistical significance (simplified)
        results_df['p_value'] = 0.05  # Placeholder
        results_df['effect_size'] = results_df['sensitivity_improvement'] / 100
        
        return {
            'experiment_id': f"IS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'experiment_timestamp': datetime.utcnow().isoformat(),
            'results': results_df,
            'config': {
                'rare_event_rate': self.rare_event_rate,
                'test_size': test_size,
                'random_seed': random_seed
            }
        }
    
    def save_results(
        self,
        experiment_results: Dict[str, Any],
        output_path: str
    ) -> pd.DataFrame:
        """
        Save experiment results to BigQuery-compatible format.
        
        Args:
            experiment_results: Results from run_experiment
            output_path: Output file path
        
        Returns:
            DataFrame with results
        """
        results_df = experiment_results['results']
        config = experiment_results['config']
        
        # Format for BigQuery
        output_records = []
        for _, row in results_df.iterrows():
            output_records.append({
                'experiment_id': experiment_results['experiment_id'],
                'experiment_timestamp': experiment_results['experiment_timestamp'],
                'sampling_method': row['method'],
                'rare_event_rate': config['rare_event_rate'],
                'sample_size': len(results_df),  # Simplified
                'reweighting_scheme': row['method'],
                'detection_sensitivity': row['sensitivity'],
                'false_positive_rate': row['false_positive_rate'],
                'mttd_hours': row['mttd_hours'],
                'mttd_improvement_pct': row['mttd_improvement_pct'],
                'p_value': row['p_value'],
                'effect_size': row['effect_size'],
                'experiment_config': json.dumps(config)
            })
        
        df_output = pd.DataFrame(output_records)
        df_output.to_csv(output_path, index=False)
        
        return df_output


def main():
    """Example usage."""
    # Generate synthetic data
    np.random.seed(42)
    n_samples = 10000
    
    # Features
    df = pd.DataFrame({
        'trip_duration': np.random.uniform(10, 120, n_samples),
        'total_events': np.random.poisson(2, n_samples),
        'critical_events': np.random.poisson(0.1, n_samples),
        'avg_latency': np.random.uniform(10, 200, n_samples),
        'safety_score': np.random.uniform(50, 100, n_samples)
    })
    
    # Rare events (1% rate)
    rare_event_prob = 0.01
    df['has_rare_event'] = np.random.binomial(1, rare_event_prob, n_samples)
    
    # Add some signal: rare events more likely with high latency
    df.loc[df['avg_latency'] > 150, 'has_rare_event'] = np.random.binomial(
        1, 0.1, df.loc[df['avg_latency'] > 150].shape[0]
    )
    
    # Run experiment
    is_sampler = ImportanceSampling(rare_event_rate=rare_event_prob)
    results = is_sampler.run_experiment(df)
    
    print("\nExperiment Results:")
    print(results['results'])
    
    # Save results
    is_sampler.save_results(results, 'importance_sampling_results.csv')
    print("\nResults saved to importance_sampling_results.csv")


if __name__ == '__main__':
    main()
