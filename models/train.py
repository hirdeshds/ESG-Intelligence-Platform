import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

def train_model():
    df = pd.read_csv(r"C:\Users\Mahek Bhatia\Desktop\ESG-Monitoring-System\outputs\agent4_final_output.csv")

    df["risk_label"] = (df["final_esg_risk_score"] >= 66).astype(int)

    # Drop non-feature columns
    X = df.drop(columns=["risk_label"])
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    joblib.dump(model, "risk_model.pkl")

    print("Model trained successfully!")

if __name__ == "__main__":
    train_model()
