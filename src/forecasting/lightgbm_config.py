"""
LightGBM Model Configuration Module for FreightWise Round 2 — Stage 2.2A.
Defines reproducible, conservative time-series regression hyperparameter contracts for LightGBM.
NOTE: Stage 2.2A provides configuration only — DO NOT train the model yet.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


@dataclass
class LightGBMModelConfig:
    """
    Configuration contract for LightGBM time-series freight forecasting model.
    """

    objective: str = "regression"
    metric: str = "rmse"
    learning_rate: float = 0.05
    n_estimators: int = 100
    num_leaves: int = 31
    max_depth: int = -1
    min_child_samples: int = 20
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42
    verbose: int = -1
    extra_params: Optional[Dict[str, Any]] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validates hyperparameter constraints and ranges.
        """
        if not self.objective:
            raise ValueError("objective cannot be empty.")
        if self.learning_rate <= 0 or self.learning_rate > 1.0:
            raise ValueError(f"learning_rate must be in (0, 1.0], got {self.learning_rate}")
        if self.n_estimators <= 0:
            raise ValueError(f"n_estimators must be positive, got {self.n_estimators}")
        if self.num_leaves <= 1:
            raise ValueError(f"num_leaves must be > 1, got {self.num_leaves}")
        if self.min_child_samples < 1:
            raise ValueError(f"min_child_samples must be >= 1, got {self.min_child_samples}")
        if self.subsample <= 0 or self.subsample > 1.0:
            raise ValueError(f"subsample must be in (0, 1.0], got {self.subsample}")
        if self.colsample_bytree <= 0 or self.colsample_bytree > 1.0:
            raise ValueError(f"colsample_bytree must be in (0, 1.0], got {self.colsample_bytree}")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns complete parameter dictionary ready for model instantiation.
        """
        self.validate()
        params = {
            "objective": self.objective,
            "metric": self.metric,
            "learning_rate": self.learning_rate,
            "n_estimators": self.n_estimators,
            "num_leaves": self.num_leaves,
            "max_depth": self.max_depth,
            "min_child_samples": self.min_child_samples,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "random_state": self.random_state,
            "verbose": self.verbose,
        }
        if self.extra_params:
            params.update(self.extra_params)
        return params

    def get_model_params(self) -> Dict[str, Any]:
        """Alias for to_dict()."""
        return self.to_dict()


def get_default_lightgbm_config() -> LightGBMModelConfig:
    """
    Factory function returning the default conservative LightGBM model configuration.
    """
    config = LightGBMModelConfig()
    config.validate()
    return config
