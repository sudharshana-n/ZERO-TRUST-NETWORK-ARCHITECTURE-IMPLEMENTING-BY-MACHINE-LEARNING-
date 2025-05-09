import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# Load the preprocessed data
df = pd.read_csv("preprocessed_login_data.csv")

# Select features
features = ['login_hour', 'is_mobile_device', 'location_encoded', 'domain_encoded']
X = df[features]

# Train model
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)

# Save predictions (optional)
df['anomaly'] = model.predict(X)
df['is_anomalous'] = df['anomaly'] == -1
df.to_csv("login_data_with_anomalies.csv", index=False)

# Save model
joblib.dump(model, "anomaly_detection_model.pkl")
print("✅ Anomaly detection model saved.")
