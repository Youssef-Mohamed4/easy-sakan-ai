import pandas as pd
import json
import time
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Load the mock data
df = pd.read_csv("mock_properties.csv")
# Convert the stringified JSON array back into an actual Python list
df['amenities'] = df['amenities'].apply(json.loads)

# 2. Feature Engineering (Turning text/categories into numbers)
# Scale Price and Area so a price of 10000 doesn't overwhelm the math
scaler = MinMaxScaler()
df[['price_scaled', 'area_scaled']] = scaler.fit_transform(df[['price', 'area_sqm']])

# One-Hot Encode the University (creates a binary column for each university)
univ_dummies = pd.get_dummies(df['nearest_university'], prefix='univ')

# Multi-Label Binarize Amenities (creates a 1 or 0 for every possible amenity)
mlb = MultiLabelBinarizer()
amenities_encoded = pd.DataFrame(mlb.fit_transform(df['amenities']), columns=mlb.classes_, index=df.index)

# 3. Build the Feature Matrix & Apply Weights
# This is where you tune the model! Multiply a column to make it more important.
# Here, we make Location (1.5) and Price (2.0) heavily influence the final score.
feature_matrix = pd.concat([
    df[['price_scaled']] * 2.0, 
    df[['area_scaled']] * 0.5,
    univ_dummies * 1.5,
    amenities_encoded * 1.0
], axis=1)

# 4. Compute the Cosine Similarity Matrix
# This calculates the angle between every single apartment vector in milliseconds
similarity_matrix = cosine_similarity(feature_matrix)

# 5. The Recommendation Function
def get_recommendations(target_id, top_n=5):
    # Find the row index of the target property
    idx = df[df['id'] == target_id].index[0]
    
    # Grab the similarity scores for this specific property
    sim_scores = list(enumerate(similarity_matrix[idx]))
    
    # Sort the apartments by their score (highest first), excluding the target itself
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = [score for score in sim_scores if score[0] != idx][:top_n]
    
    # Extract the winning indices and scores
    prop_indices = [i[0] for i in sim_scores]
    scores = [round(score[1], 3) for score in sim_scores]
    
    # Format the results
    results = df.iloc[prop_indices][['id', 'price', 'nearest_university', 'amenities']].copy()
    results['matchScore'] = scores
    return results

target_property_id = 1 

print("================ TARGET PROPERTY ================")
print(df[df['id'] == target_property_id][['id', 'price', 'nearest_university', 'amenities']].to_string(index=False))
print("\n")

print("================ TOP 5 RECOMMENDATIONS ================")
print(get_recommendations(target_property_id).to_string(index=False))

print("\n================ SYSTEM METRICS ================")

# 1. Execution Time (Latency)
# Measures how fast the model returns results (Crucial for API performance)
start_time = time.perf_counter()
_ = get_recommendations(target_id=1, top_n=5)
end_time = time.perf_counter()
latency = end_time - start_time
print(f"1. Execution Time: {latency:.4f} seconds")

# 2. Catalog Coverage
# Measures what percentage of our total inventory ever gets recommended
all_recommended_ids = set()
total_apartments = len(df)

for property_id in df['id']:
    recs = get_recommendations(target_id=property_id, top_n=5)
    all_recommended_ids.update(recs['id'].tolist())

coverage_percent = (len(all_recommended_ids) / total_apartments) * 100
print(f"2. Catalog Coverage: {coverage_percent:.1f}% ({len(all_recommended_ids)}/{total_apartments} unique properties shown)")

# 3. Intra-List Diversity (Price)
# Measures the standard deviation of prices in the top 5 to ensure we aren't showing identical clones
sample_recs = get_recommendations(target_id=1, top_n=5)
price_std = sample_recs['price'].std()
print(f"3. Intra-List Diversity (Price Std Dev for Target 1): ±{price_std:.2f} EGP")