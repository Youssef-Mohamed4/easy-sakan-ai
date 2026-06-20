import pandas as pd
import random

# Schema definitions
universities = [
    "Assiut University", "Cairo University", "AUC", "Ain Shams University", 
    "GUC", "Helwan University", "Alexandria University", "Mansoura University", 
    "Tanta University", "Zagazig University", "Minia University", 
    "Benha University", "Fayoum University", "Suez Canal University"
]
amenities_pool = ["WiFi", "AC", "Elevator", "Balcony", "Washing Machine", "Natural Gas"]
listing_modes = ["Bed", "Room", "EntireUnit"]
gender_allowances = ["Male", "Female"]

# Logical Pricing Multipliers
uni_multipliers = {
    "AUC": 2.6, "GUC": 2.3, 
    "Cairo University": 1.5, "Ain Shams University": 1.4, 
    "Alexandria University": 1.5, "Helwan University": 1.1,
    "Mansoura University": 1.1, "Tanta University": 1.0, 
    "Zagazig University": 1.0, "Benha University": 1.0,
    "Suez Canal University": 1.0, "Fayoum University": 0.9,
    "Minia University": 0.9, "Assiut University": 0.9
}

# Value of specific amenities in EGP
amenity_values = {
    "AC": 800, "Elevator": 300, "Washing Machine": 250, 
    "WiFi": 200, "Balcony": 150, "Natural Gas": 100
}

def generate_dataset(num_rows=5000):
    print(f"[*] Generating {num_rows} highly localized Egyptian property listings...")
    data = []

    for _ in range(num_rows):
        nearest_uni = random.choice(universities)
        mode = random.choice(listing_modes)
        
        # 1. Anchor the physical space (Bedrooms first)
        bedrooms = random.randint(1, 4)
        
        # 2. Area logically scales with bedrooms (Assume absolute minimum 25 sqm per room)
        min_area = bedrooms * 25.0
        area_sqm = round(random.uniform(min_area, max(min_area + 40.0, 200.0)), 1)
        
        # 3. Capacity logically scales with bedrooms (1 to 2 students per room in Sakan)
        total_capacity = random.randint(bedrooms, bedrooms * 2)
        
        # 4. Bathrooms scale with capacity
        bathrooms = 2 if total_capacity >= 4 else 1
        
        num_amenities = random.randint(0, len(amenities_pool))
        selected_amenities = random.sample(amenities_pool, num_amenities)

        # Calculate logical pricing based on rules
        base_unit_price = (area_sqm * 40) * uni_multipliers[nearest_uni]
        
        for amenity in selected_amenities:
            base_unit_price += amenity_values[amenity]
            
        # Dynamically divide the price based on the Listing Mode and Capacity
        if mode == "EntireUnit":
            price = base_unit_price
        elif mode == "Room":
            price = base_unit_price / max(1, bedrooms)
        elif mode == "Bed":
            price = base_unit_price / max(1, total_capacity)
        
        # Add random market noise (+/- 12%) to make ML training realistic
        noise = random.uniform(0.88, 1.12)
        final_price = round(price * noise, 2)

        row = {
            "nearest_university": nearest_uni,
            "listing_mode": mode,
            "gender_allowed": random.choice(gender_allowances),
            "area_sqm": area_sqm,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "total_capacity": total_capacity,
            "price": final_price
        }
        
        for amenity in amenities_pool:
            row[f"has_{amenity.replace(' ', '')}"] = 1 if amenity in selected_amenities else 0
            
        data.append(row)

    df = pd.DataFrame(data)
    
    # Save directly to the current directory
    output_filename = "student_housing_train.csv"
    df.to_csv(output_filename, index=False)
    
    print(f"[+] Successfully saved {output_filename} (Shape: {df.shape})")

if __name__ == "__main__":
    generate_dataset()