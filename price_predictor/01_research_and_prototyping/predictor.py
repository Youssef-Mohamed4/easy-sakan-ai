import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

def train():
    print("[*] Loading dataset...")
    # Updated path: reading directly from the current directory
    df = pd.read_csv("student_housing_train.csv")

    # 1. Split Features (X) and Target Price (y)
    X = df.drop(columns=["price"])
    y = df["price"]

    # 2. Define Preprocessing
    categorical_cols = ["nearest_university", "listing_mode", "gender_allowed"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
        ],
        remainder="passthrough"
    )

    # 3. Build the ML Pipeline
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", xgb.XGBRegressor(
            n_estimators=400,       
            learning_rate=0.05,     
            max_depth=6,            
            random_state=42,
            n_jobs=-1               
        ))
    ])

    # 4. Split data to test for overfitting (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 5. Train the Model
    print("[*] Training XGBoost pipeline...")
    pipeline.fit(X_train, y_train)

    # 6. Evaluate Accuracy
    predictions = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print("\n==============================")
    print("      MODEL EVALUATION        ")
    print("==============================")
    print(f"Mean Absolute Error : +/- {mae:.2f} EGP")
    print(f"R-Squared Score     : {r2:.4f}")
    print("==============================\n")

    # 7. Save the artifact directly to the current directory
    print("[*] Saving model artifact for backend deployment...")
    joblib.dump(pipeline, "easysakan_price_predictor.joblib")
    print("[+] Saved as easysakan_price_predictor.joblib")

if __name__ == "__main__":
    train()