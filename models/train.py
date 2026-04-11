import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def train_model():
    df = pd.read_csv(r"C:\Users\Mahek Bhatia\ESG-Intelligence-Platform\ML\ESG4_output.csv")
    df["risk_label"] = (df["final_esg_risk_score"] >= 66).astype(int)

    # Drop non-feature columns
    # X = df.drop(columns=["risk_label","Firm_ID","Overall_Compliance","alert_level"])
    y = df["risk_label"]
    X=df.select_dtypes(include=["float64", "int64"]).drop(columns=["risk_label"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")

    joblib.dump(model, "risk_model.pkl")

    print("Model trained successfully!")

if __name__ == "__main__":
    train_model()
