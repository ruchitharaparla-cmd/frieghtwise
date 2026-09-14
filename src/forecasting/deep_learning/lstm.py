from pathlib import Path
import random

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ---------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)


# ---------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------
DATA_PATH = Path("data/processed/freight_model_features.csv")

TARGET = "bulk_carrier_handysize_usd_day"

FEATURES = [
    "freight_lag_1",
    "freight_lag_3",
    "freight_lag_6",
    "freight_lag_12",
    "freight_rolling_mean_3",
    "freight_rolling_mean_6",
    "freight_rolling_mean_12",
    "freight_rolling_std_3",
    "baltic_dry_index_lag_1",
    "baltic_dry_index_lag_3",
    "brent_price_lag_1",
    "brent_price_lag_3",
    "wti_price_lag_1",
    "wti_price_lag_3",
    "dxy_index_lag_1",
    "dxy_index_lag_3",
    "vix_lag_1",
    "vix_lag_3",
    "gpr_index_lag_1",
    "gpr_index_lag_3",
    "thermal_coal_price_lag_1",
    "thermal_coal_price_lag_3",
    "month_num",
    "quarter",
    "month_sin",
    "month_cos",
]

LOOKBACK = 12

MODEL_PATH = Path("ml/forecasting/lstm_round2.keras")
PREDICTION_PATH = Path("ml/evaluation/lstm_predictions.csv")


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
def load_data():
    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(df["date"])

    df = (
        df.sort_values("date")
        .reset_index(drop=True)
    )

    required = ["date", TARGET] + FEATURES

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    df = (
        df[required]
        .dropna()
        .reset_index(drop=True)
    )

    if len(FEATURES) != 26:
        raise ValueError(
            f"Expected 26 features, got {len(FEATURES)}"
        )

    return df


# ---------------------------------------------------------
# Sequence creation
# ---------------------------------------------------------
def make_sequences(X, y, dates, lookback):
    X_seq = []
    y_seq = []
    date_seq = []

    for i in range(lookback, len(X)):
        X_seq.append(
            X[i - lookback:i]
        )

        y_seq.append(y[i])
        date_seq.append(dates.iloc[i])

    return (
        np.asarray(X_seq, dtype=np.float32),
        np.asarray(y_seq, dtype=np.float32),
        pd.Series(date_seq),
    )


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------
def calculate_metrics(y_true, y_pred):

    mae = mean_absolute_error(
        y_true,
        y_pred
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred
        )
    )

    nonzero = np.abs(y_true) > 1e-8

    mape = (
        np.mean(
            np.abs(
                (
                    y_true[nonzero]
                    - y_pred[nonzero]
                )
                / y_true[nonzero]
            )
        )
        * 100
    )

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape),
    }


# ---------------------------------------------------------
# LSTM model
# ---------------------------------------------------------
def build_model(input_shape):

    model = tf.keras.Sequential([
        tf.keras.layers.Input(
            shape=input_shape
        ),

        tf.keras.layers.LSTM(
            64,
            return_sequences=True
        ),

        tf.keras.layers.Dropout(0.2),

        tf.keras.layers.LSTM(32),

        tf.keras.layers.Dropout(0.2),

        tf.keras.layers.Dense(
            16,
            activation="relu"
        ),

        tf.keras.layers.Dense(1),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=0.001
        ),
        loss="mse",
    )

    return model


# ---------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------
def main():

    df = load_data()

    # ---------------------------------------------
    # Chronological split
    # ---------------------------------------------
    train_end = pd.Timestamp(
        "2022-12-01"
    )

    validation_end = pd.Timestamp(
        "2023-12-01"
    )

    train_df = df[
        df["date"] <= train_end
    ].copy()

    validation_df = df[
        (df["date"] > train_end)
        & (df["date"] <= validation_end)
    ].copy()

    test_df = df[
        df["date"] > validation_end
    ].copy()

    print("\nDataset split")
    print(
        "Train:",
        train_df["date"].min(),
        "→",
        train_df["date"].max()
    )

    print(
        "Validation:",
        validation_df["date"].min(),
        "→",
        validation_df["date"].max()
    )

    print(
        "Test:",
        test_df["date"].min(),
        "→",
        test_df["date"].max()
    )

    # ---------------------------------------------
    # Scaling
    # IMPORTANT:
    # Fit ONLY on training data.
    # ---------------------------------------------
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()

    feature_scaler.fit(
        train_df[FEATURES].values
    )

    target_scaler.fit(
        train_df[[TARGET]].values
    )

    X_all = feature_scaler.transform(
        df[FEATURES].values
    )

    y_all = target_scaler.transform(
        df[[TARGET]].values
    ).ravel()

    dates = df["date"]

    # ---------------------------------------------
    # Identify split indices
    # ---------------------------------------------
    train_indices = np.where(
        dates <= train_end
    )[0]

    validation_indices = np.where(
        (dates > train_end)
        & (dates <= validation_end)
    )[0]

    test_indices = np.where(
        dates > validation_end
    )[0]

    # ---------------------------------------------
    # Training sequences
    # ---------------------------------------------
    train_start = train_indices[0]
    train_end_idx = train_indices[-1]

    X_train, y_train, _ = make_sequences(
        X_all[
            train_start:
            train_end_idx + 1
        ],

        y_all[
            train_start:
            train_end_idx + 1
        ],

        dates.iloc[
            train_start:
            train_end_idx + 1
        ],

        LOOKBACK,
    )

    # ---------------------------------------------
    # Validation sequences
    # Include previous 12 months as history.
    # ---------------------------------------------
    validation_start = max(
        0,
        validation_indices[0] - LOOKBACK
    )

    X_val_all, y_val_all, val_dates_all = (
        make_sequences(
            X_all[
                validation_start:
                validation_indices[-1] + 1
            ],

            y_all[
                validation_start:
                validation_indices[-1] + 1
            ],

            dates.iloc[
                validation_start:
                validation_indices[-1] + 1
            ],

            LOOKBACK,
        )
    )

    validation_keep = (
        val_dates_all > train_end
    )

    X_val = X_val_all[
        validation_keep
    ]

    y_val = y_val_all[
        validation_keep
    ]

    val_dates = val_dates_all[
        validation_keep
    ].reset_index(drop=True)

    # ---------------------------------------------
    # Test sequences
    # Include previous 12 months as history.
    # ---------------------------------------------
    test_start = max(
        0,
        test_indices[0] - LOOKBACK
    )

    X_test_all, y_test_all, test_dates_all = (
        make_sequences(
            X_all[
                test_start:
                test_indices[-1] + 1
            ],

            y_all[
                test_start:
                test_indices[-1] + 1
            ],

            dates.iloc[
                test_start:
                test_indices[-1] + 1
            ],

            LOOKBACK,
        )
    )

    test_keep = (
        test_dates_all > validation_end
    )

    X_test = X_test_all[
        test_keep
    ]

    y_test = y_test_all[
        test_keep
    ]

    test_dates = test_dates_all[
        test_keep
    ].reset_index(drop=True)

    print("\nSequence shapes")
    print("Training:", X_train.shape)
    print("Validation:", X_val.shape)
    print("Test:", X_test.shape)

    # ---------------------------------------------
    # Build model
    # ---------------------------------------------
    model = build_model(
        input_shape=(
            LOOKBACK,
            len(FEATURES)
        )
    )

    model.summary()

    # ---------------------------------------------
    # Early stopping
    # ---------------------------------------------
    early_stopping = (
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True,
        )
    )

    # ---------------------------------------------
    # Train
    # ---------------------------------------------
    print("\nTraining LSTM...")

    model.fit(
        X_train,
        y_train,

        validation_data=(
            X_val,
            y_val
        ),

        epochs=100,

        batch_size=16,

        callbacks=[
            early_stopping
        ],

        verbose=1,
    )

    # ---------------------------------------------
    # Validation prediction
    # ---------------------------------------------
    validation_pred_scaled = (
        model.predict(
            X_val,
            verbose=0
        ).ravel()
    )

    validation_true = (
        target_scaler.inverse_transform(
            y_val.reshape(-1, 1)
        ).ravel()
    )

    validation_pred = (
        target_scaler.inverse_transform(
            validation_pred_scaled.reshape(-1, 1)
        ).ravel()
    )

    validation_metrics = calculate_metrics(
        validation_true,
        validation_pred
    )

    print("\nValidation metrics:")
    print(validation_metrics)

    # ---------------------------------------------
    # Test prediction
    # ---------------------------------------------
    test_pred_scaled = (
        model.predict(
            X_test,
            verbose=0
        ).ravel()
    )

    test_true = (
        target_scaler.inverse_transform(
            y_test.reshape(-1, 1)
        ).ravel()
    )

    test_pred = (
        target_scaler.inverse_transform(
            test_pred_scaled.reshape(-1, 1)
        ).ravel()
    )

    test_metrics = calculate_metrics(
        test_true,
        test_pred
    )

    print("\nTest metrics:")
    print(test_metrics)

    # ---------------------------------------------
    # Save model
    # ---------------------------------------------
    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    PREDICTION_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    model.save(MODEL_PATH)

    # ---------------------------------------------
    # Save test predictions
    # ---------------------------------------------
    predictions = pd.DataFrame({
        "date": test_dates,
        "actual": test_true,
        "predicted": test_pred,
    })

    predictions.to_csv(
        PREDICTION_PATH,
        index=False
    )

    print("\nSaved model:")
    print(MODEL_PATH)

    print("\nSaved predictions:")
    print(PREDICTION_PATH)


if __name__ == "__main__":
    main()