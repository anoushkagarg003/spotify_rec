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


