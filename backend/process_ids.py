"""
this cript extract TMDB ids from the MovieLens 25M dataset. Filters out missing values and exports clean csv

"""
import pandas as pd 
def extract_ids(input_file: str, output_file: str):
    tmdb_ids_df=pd.read_csv(input_file)
    tmdb_ids_df.dropna(inplace=True)
    tmdb_ids_df=tmdb_ids_df[['tmdbId']].astype(int)
    tmdb_ids_df.to_csv(output_file,index=False)
    tmdb_ids_df.head()

if __name__ == "__main__":
    extract_ids("links.csv","tmdb_ids.csv")
