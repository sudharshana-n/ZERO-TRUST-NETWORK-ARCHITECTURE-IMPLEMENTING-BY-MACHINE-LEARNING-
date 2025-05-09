import pandas as pd
from sklearn.preprocessing import LabelEncoder
import json

# Load dataset
df = pd.read_csv("new_login_dataset.csv")

# Extract login_hour from login_time (adjust format if needed)
df['login_hour'] = pd.to_datetime(df['login_time'], format="%H:%M:%S").dt.hour


# Convert device_type to binary
df['is_mobile_device'] = df['device_type'].apply(lambda x: 1 if str(x).lower() == 'mobile' else 0)

# Extract domain
df['domain'] = df['user_id'].apply(lambda x: x.split('@')[1] if '@' in str(x) else 'unknown')

# Encode location and domain
location_encoder = LabelEncoder()
domain_encoder = LabelEncoder()

df['location_encoded'] = location_encoder.fit_transform(df['location'])
df['domain_encoded'] = domain_encoder.fit_transform(df['domain'])

# Save encoders as JSON-serializable dicts
location_mapping = {k: int(v) for k, v in zip(location_encoder.classes_, location_encoder.transform(location_encoder.classes_))}
domain_mapping = {k: int(v) for k, v in zip(domain_encoder.classes_, domain_encoder.transform(domain_encoder.classes_))}

with open("location_mapping.json", "w") as f:
    json.dump(location_mapping, f)

with open("domain_mapping.json", "w") as f:
    json.dump(domain_mapping, f)

# Save preprocessed data
df.to_csv("preprocessed_login_data.csv", index=False)
print("✅ Preprocessing complete.")
