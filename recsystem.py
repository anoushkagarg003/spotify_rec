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
df_recs.rename(columns={'key_value': 'key'}, inplace=True)
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

# Standardize the features
scaler = StandardScaler()
userdata_scaled = scaler.fit_transform(df_user_vector)
# Perform PCA

pca = PCA(n_components=7)
userdata_pca = pca.fit_transform(userdata_scaled)
recdata_scaled=scaler.transform(df_recs_vector)
recdata_pca=pca.transform(recdata_scaled)
userdata_pca_df = pd.DataFrame(userdata_pca, columns=['feature1', 'feature2', 'feature3', 'feature4', 'feature5', 'feature6', 'feature7'])
recdata_pca_df = pd.DataFrame(recdata_pca, columns=['feature1', 'feature2', 'feature3', 'feature4', 'feature5', 'feature6', 'feature7'])

# Apply the similarity scoring function to each row
results = recdata_pca_df.apply(compute_similarity_for_row, axis=1, df_user_vector=userdata_pca_df)

# Combine the results with the original df_recs to display results alongside song names
df = df_recs[['id', 'name']].join(results)
df_sorted = df.sort_values(by='cumulative_similarity_score', ascending=False)
print(df_sorted.head(10))