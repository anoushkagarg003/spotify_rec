import pandas as pd
from sqlsample import get_connection, execute_query
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
def get_recommendations():
    
    connection = get_connection()

    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user_top_songs_1;")
        user_top_songs = cursor.fetchall()
        cursor.execute("SELECT * FROM potential_recommendations_2;")
        potential_recommendations = cursor.fetchall()

    
    df_user = pd.DataFrame(user_top_songs)
    df_recs = pd.DataFrame(potential_recommendations)
    df_recs['push_new'] = 1//((datetime.now() - pd.to_datetime(df_recs['release_date'], errors='coerce')).dt.days)
    
    connection.close()
    print(df_user.head())
    print(df_recs.head())
    
    df_recs.rename(columns={'key_value': 'key'}, inplace=True)
    #df_recs = df_recs[~df_recs['id'].isin(df_user['id'])]
    # Remove non-feature columns
    df_user_vector = df_user.drop(columns=['id', 'name'])
    df_recs_vector = df_recs.drop(columns=['id', 'name','release_date', 'push_new'])

    # Standardize the features
    scaler = StandardScaler()
    userdata_scaled = scaler.fit_transform(df_user_vector)
    recdata_scaled = scaler.transform(df_recs_vector)

    # Perform PCA
    pca = PCA(n_components=7)
    userdata_pca = pca.fit_transform(userdata_scaled)
    recdata_pca = pca.transform(recdata_scaled)

    # Convert PCA results to DataFrames
    userdata_pca_df = pd.DataFrame(userdata_pca, columns=['feature1', 'feature2', 'feature3', 'feature4', 'feature5', 'feature6', 'feature7'])
    recdata_pca_df = pd.DataFrame(recdata_pca, columns=['feature1', 'feature2', 'feature3', 'feature4', 'feature5', 'feature6', 'feature7'])
    column_variances = userdata_pca_df.var()
    print(f'COLUMN VARIANCES: {column_variances}')
    # Function to calculate similarity scores
    def similarity_scoring(song_vector, df):
        similarity_scores = cosine_similarity(df, song_vector)
        similarity_scores = similarity_scores.flatten()
        cumulative_similarity_score = np.sum(similarity_scores)
        return similarity_scores, cumulative_similarity_score

    def compute_similarity_for_row(row, df_user_vector):
        song_vector = row.values.reshape(1, -1)
        similarity_scores, cumulative_similarity_score = similarity_scoring(song_vector, df_user_vector)
        return pd.Series([similarity_scores, cumulative_similarity_score], index=['similarity_scores', 'cumulative_similarity_score'])

    results = recdata_pca_df.apply(compute_similarity_for_row, axis=1, df_user_vector=userdata_pca_df)

    # Combine 
    df = df_recs[['id', 'name', 'release_date', 'push_new']].join(results)
    df['cumulative_similarity_score'] = df['cumulative_similarity_score'] + df['push_new'].apply(lambda x: x if not pd.isna(x) else 0)
    df_sorted = df.sort_values(by='cumulative_similarity_score', ascending=False)
    top_10_ids = list(df_sorted.head(10)['id'])
    print(df_sorted.head(10))

    return top_10_ids
get_recommendations()


