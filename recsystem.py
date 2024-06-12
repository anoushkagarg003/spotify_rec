import pandas as pd
from sqlsample import get_connection, execute_query
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
connection=get_connection()

# Define the query
query1 = "SELECT * FROM user_top_songs_1"
query2 = "SELECT * FROM potential_recommendations_1"

# Execute the query and fetch the data into a DataFrame
df_user = pd.read_sql(query1, connection)
df_recs=pd.read_sql(query2, connection)
# Close the connection
connection.close()

# Display the DataFrame


import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# The song vector you want to compare
def similarity_scoring(song_vector, df):
    similarity_scores = cosine_similarity(df, song_vector)
    similarity_scores = similarity_scores.flatten()
    cumulative_similarity_score = np.sum(similarity_scores)
    return similarity_scores, cumulative_similarity_score

# Wrapper function for apply
def compute_similarity_for_row(row, df_user_vector):
    song_vector = row.values.reshape(1, -1)
    similarity_scores, cumulative_similarity_score = similarity_scoring(song_vector, df_user_vector)
    return pd.Series([similarity_scores, cumulative_similarity_score], index=['similarity_scores', 'cumulative_similarity_score'])

# Fetch data

# Remove non-feature columns
df_user_vector = df_user.drop(columns=['id', 'name'])
df_recs_vector = df_recs.drop(columns=['id', 'name'])

# Print data types
'''print(df_recs_vector.dtypes)
print(df_user_vector.dtypes)

# Apply the similarity scoring function to each row
results = df_recs_vector.apply(compute_similarity_for_row, axis=1, df_user_vector=df_user_vector)

# Combine the results with the original df_recs to display results alongside song names
df_results = df_recs[['id', 'name']].join(results)

print(df_results)'''
# Standardize the features
X=df_user_vector
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
# Perform PCA
pca = PCA(n_components=7)
X_pca = pca.fit_transform(X_scaled)

# Calculate the explained variance ratio
explained_variance_ratio=pca.explained_variance_ratio_
print(pca.explained_variance_ratio_)
print("\nNumber of Components:", pca.n_components_)
# Create a 2x1 grid of subplots
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))

# Plot the explained variance ratio in the first subplot
ax1.bar(range(1, len(explained_variance_ratio) + 1), explained_variance_ratio)
ax1.set_xlabel("Principal Component")
ax1.set_ylabel("Explained Variance Ratio")
ax1.set_title("Explained Variance Ratio by Principal Component")
cumulative_explained_variance = np.cumsum(explained_variance_ratio)

# Plot the cumulative explained variance in the second subplot
ax2.plot(
    range(1, len(cumulative_explained_variance) + 1),
    cumulative_explained_variance,
    marker="o",
)
ax2.set_xlabel("Number of Principal Components")
ax2.set_ylabel("Cumulative Explained Variance")
ax2.set_title("Cumulative Explained Variance by Principal Components")

# Display the figure
plt.tight_layout()
plt.show()