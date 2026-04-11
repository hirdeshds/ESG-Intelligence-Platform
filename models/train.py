import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def train_enhanced_model():
    try:
        df = pd.read_csv(r"..\ML\ESG4_output.csv")
    except FileNotFoundError:
        return

    df["risk_label"] = (df["final_esg_risk_score"] >= 66).astype(int)

    X = df.select_dtypes(include=["float64", "int64"]).drop(columns=["risk_label", "final_esg_risk_score"], errors='ignore')
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances})
    print(feature_importance_df.sort_values(by='Importance', ascending=False).head(5))

    joblib.dump(model, "risk_model.pkl")

if __name__ == "__main__":
    train_enhanced_model()