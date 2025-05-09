import pandas as pd
import pymysql

# Load your CSV
df = pd.read_csv("new_login_dataset.csv")

# Define a function to set the password based on the domain
def set_password(user_id):
    if "dataguard.com" in user_id:
        return "test123"
    elif "lumentech.com" in user_id:
        return "qwerty"
    elif "cybernova.com" in user_id:
        return "asdfghjkl"
    else:
        return "default_password"  # You can customize this

# Apply the function to set the password column
df['password'] = df['user_id'].apply(set_password)

# Extract username (you can clean it further if needed)
df['username'] = df['user_id']

# Connect to MySQL
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="sindhu",  # Replace with your MySQL password
    database="login_security"    # Replace with your database name
)

cursor = connection.cursor()

# Insert each row into the users table
for _, row in df.iterrows():
    try:
        cursor.execute(
            "INSERT INTO users (username, password, location) VALUES (%s, %s, %s)",
            (row['username'], row['password'], row['location'])
        )
    except Exception as e:
        print(f"Error inserting {row['username']}: {e}")

# Commit and close
connection.commit()
cursor.close()
connection.close()

print("✅ All user data inserted into the database.")
