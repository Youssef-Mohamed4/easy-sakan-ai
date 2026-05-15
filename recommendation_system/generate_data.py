import pandas as pd
import random
import json

# Using the exact data from your API specs
universities = ["Cairo University", "AUC", "Ain Shams University", "GUC", "Helwan University"]
amenities_pool = ["WiFi", "AC", "Elevator", "Security", "Parking", "Balcony", "Washing Machine", "Natural Gas"]

data = []
for i in range(1, 101):
    data.append({
        "id": i,
        "title": f"Apartment {i}",
        "price": random.randint(2500, 10000),
        "nearest_university": random.choice(universities),
        "bedrooms": random.randint(1, 3),
        "area_sqm": random.randint(50, 150),
        # Simulating the JSON array from your DB
        "amenities": json.dumps(random.sample(amenities_pool, k=random.randint(2, 5)))
    })

df = pd.DataFrame(data)
df.to_csv("mock_properties.csv", index=False)
print("Created mock_properties.csv with 100 listings.")