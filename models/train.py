import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

def train_model():
    df = pd.read_csv("../outputs/ESG4_output.csv")

    df["risk_label"] = (df["final_esg_risk_score"] >= 66).astype(int)

    features = ["ESG_Score"]
    X = df[features]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    joblib.dump(model, "risk_model.pkl")
    print("Model Trained & Saved")

if __name__ == "__main__":
    train_model()
