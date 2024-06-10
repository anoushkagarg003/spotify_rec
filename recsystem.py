import pandas as pd
from sqlsample import get_connection, execute_query
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
    print("Similarity Scores:", similarity_scores)
    print("Cumulative Similarity Score:", cumulative_similarity_score)


df_user_vector = df_user.drop(columns=['id','name'])
df_recs_vector = df_recs.drop(columns=['id','name'])
print(df_recs_vector.dtypes, df_user_vector.dtypes)
similarity_scoring(df_recs_vector.iloc[0].values.reshape(1, -1),df_user_vector)