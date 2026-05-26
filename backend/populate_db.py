import os
import pandas as pd
from app import app
from models import db, Anime

def populate_anime_from_csv(csv_path='../data/anime.csv'):
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        return

    print("Loading CSV...")
    df = pd.read_csv(csv_path)
    
    with app.app_context():
        print("Creating missing tables...")
        db.create_all()
        
        # Check if already populated
        if Anime.query.first():
            print("Anime table already contains data. Skipping population to avoid duplicates.")
            return

        print("Populating Anime table... This might take a minute.")
        # We only insert the first 5000 to save time, or we can insert all 17k
        for index, row in df.iterrows():
            try:
                score = float(row['Score']) if pd.notna(row['Score']) and row['Score'] != 'Unknown' else None
                anime = Anime(
                    mal_id=int(row['MAL_ID']),
                    title=str(row['Name']),
                    score=score,
                    genres=str(row['Genres']) if pd.notna(row['Genres']) else None
                )
                db.session.add(anime)
            except Exception as e:
                pass # skip corrupted rows
                
            if index % 1000 == 0 and index > 0:
                print(f"Inserted {index} records...")
                db.session.commit()
                
        db.session.commit()
        print("Done populating Anime table!")

if __name__ == '__main__':
    populate_anime_from_csv()
