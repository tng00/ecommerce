import pandas as pd
import numpy as np

class PopularityRecommender:
    MODEL_NAME = 'Popularity'

    def __init__(self, it_full):
        self.popularity_df = self.get_popularity_df(it_full)

    def get_model_name(self):
        return self.MODEL_NAME

    def get_popularity_df(self, it_full):
        popularity_df = it_full.groupby('item_id')['event_strength'].sum().sort_values(ascending=False).reset_index()
        return popularity_df

    def recommend_items(self, user_id, items_to_ignore=[], topn=10):
        # Recommend the more popular items that the user hasn't seen yet.
        recommendations_df = self.popularity_df[~self.popularity_df['item_id'].isin(items_to_ignore)] \
                               .sort_values('event_strength', ascending = False) \
                               .head(topn)

        return recommendations_df
