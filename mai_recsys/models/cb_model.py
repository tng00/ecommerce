import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity

class CBRecommender:
    MODEL_NAME = 'Content-Based'

    def __init__(self, it_full, embeddings):
        self.it_full = it_full
        self.embeddings = embeddings
        self.neigh = NearestNeighbors(n_neighbors=100, metric='cosine')

    def get_model_name(self):
        return self.MODEL_NAME

    def get_user_embeds(self, user_id):
        a = pd.merge(self.it_full.loc[user_id], self.embeddings, left_on='item_id', right_index=True)
        return a['name_cat'].mean()

    def _get_similar_items_to_user_profile(self, user_id):
        # b = pd.merge(self.it_full.loc[user_id], self.embeddings, left_on='item_id', right_index=True)
        # train = np.array(self.embeddings.drop(b['item_id']).tolist())
        train = np.array(self.embeddings.tolist())
        self.neigh.fit(train)
        a = np.array([self.get_user_embeds(user_id).tolist()])
        distances, indices = self.neigh.kneighbors(a)
        similar_items = [(indices[i], distances[i]) for i in range(len(indices))]
        return similar_items

    def recommend_items(self, user_id, items_to_ignore=[], topn=10):
        similar_items = self._get_similar_items_to_user_profile(user_id)
        similar_items = pd.DataFrame(similar_items, columns=['item_id', 'recStrength']) \
                                    .head(topn)
        #Ignores items the user has already interacted
        similar_items = pd.concat([similar_items[col].explode(ignore_index=True) for col in similar_items], axis='columns')

        recommendations_df = similar_items[~similar_items['item_id'].isin(items_to_ignore)] \
                               .sort_values('recStrength', ascending = False) \
                               .head(topn)

        return recommendations_df
