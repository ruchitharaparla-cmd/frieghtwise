"""
Chronological Train/Validation/Test Split Utility for FreightWise Round 2 — Stage 2.
Preserves Round 1 philosophy (143 train, 12 validation, 12 test for 167-observation datasets)
without random shuffling, ensuring zero temporal data leakage.
"""

import pandas as pd
from typing import NamedTuple, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TimeSeriesSplitResult:
    """
    Container for chronological train, validation, and test split partitions.
    """

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame

    @property
    def shapes(self) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        return self.train.shape, self.validation.shape, self.test.shape

    @property
    def lengths(self) -> Tuple[int, int, int]:
        return len(self.train), len(self.validation), len(self.test)

    def verify_no_overlap(self, date_col: str = "date") -> bool:
        """
        Verifies strict temporal separation and date disjointness across partitions.
        """
        if date_col in self.train.columns and date_col in self.validation.columns and date_col in self.test.columns:
            train_dates = set(self.train[date_col])
            val_dates = set(self.validation[date_col])
            test_dates = set(self.test[date_col])

            if train_dates & val_dates or val_dates & test_dates or train_dates & test_dates:
                raise ValueError("Overlapping date detected between split partitions.")

            train_max = pd.to_datetime(self.train[date_col]).max()
            val_min = pd.to_datetime(self.validation[date_col]).min()
            val_max = pd.to_datetime(self.validation[date_col]).max()
            test_min = pd.to_datetime(self.test[date_col]).min()

            if train_max >= val_min:
                raise ValueError(
                    f"Temporal leakage detected: max train date ({train_max}) >= min validation date ({val_min})"
                )

            if val_max >= test_min:
                raise ValueError(
                    f"Temporal leakage detected: max validation date ({val_max}) >= min test date ({test_min})"
                )

        return True


def chronological_train_val_test_split(
    df: pd.DataFrame,
    date_col: str = "date",
    train_size: Optional[int] = 143,
    val_size: int = 12,
    test_size: int = 12,
) -> TimeSeriesSplitResult:
    """
    Splits a time-series DataFrame chronologically into train, validation, and test sets.
    Preserves Round 1 philosophy: train=143, val=12, test=12 for 167 observations.

    Parameters:
        df: Input DataFrame.
        date_col: Column name representing observation dates.
        train_size: Fixed size for training set. If None or dataset differs,
                    train gets all preceding observations before val and test.
        val_size: Number of validation observations (default 12).
        test_size: Number of test observations (default 12).

    Returns:
        TimeSeriesSplitResult containing clean DataFrame copies for train, validation, and test.
    """
    if df.empty:
        raise ValueError("Input DataFrame for splitting cannot be empty.")

    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in DataFrame.")

    # Ensure chronological sorting without mutating original DataFrame
    sorted_df = df.sort_values(by=date_col).copy().reset_index(drop=True)
    n_total = len(sorted_df)

    if val_size <= 0 or test_size <= 0:
        raise ValueError("val_size and test_size must be positive integers.")

    if n_total < val_size + test_size + 1:
        raise ValueError(
            f"Dataset length ({n_total}) is too short for validation ({val_size}) and test ({test_size}) splits."
        )

    # Determine split indices
    if train_size is not None and n_total == (train_size + val_size + test_size):
        # Exact Round 1 143 / 12 / 12 split
        train_end = train_size
        val_end = train_size + val_size
    else:
        # Dynamic tail splitting preserving val_size and test_size at the end
        val_end = n_total - test_size
        train_end = val_end - val_size
        if train_end <= 0:
            raise ValueError(
                f"Insufficient rows ({n_total}) for train partition with val={val_size} and test={test_size}."
            )

    train_df = sorted_df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = sorted_df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = sorted_df.iloc[val_end:].copy().reset_index(drop=True)

    result = TimeSeriesSplitResult(train=train_df, validation=val_df, test=test_df)
    result.verify_no_overlap(date_col=date_col)

    return result
