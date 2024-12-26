import numpy as np
import pandas as pd
from utils import event_types, event_type_strength, modify_interactions
from evaluator import ModelEvaluator, EVAL_RANDOM_SAMPLE_NON_INTERACTED_ITEMS
from models.cf_model import CFRecommender
from models.cb_model import CBRecommender
from models.popularity_model import PopularityRecommender

if __name__ == '__main__':
    item_categories = pd.read_csv('data/item_categories.csv')
    interactions = pd.read_csv('data/interactions.csv')
    items = pd.read_csv('data/items_with_price.csv')
    embeddings = pd.read_pickle('data/embeddings.pkl')

    interactions_full_df, interactions_train_df, interactions_test_df = modify_interactions(interactions)
    interactions_full_indexed_df, interactions_train_indexed_df, interactions_test_indexed_df = modify_interactions(interactions, indexing=True)

    # Collaborative Filtering
    cf_recommender_model = CFRecommender(interactions_train_df, items)
    print(cf_recommender_model.recommend_items(0))

    # Community Based
    cb_recommender_model = CBRecommender(interactions_full_indexed_df, embeddings)
    print(cb_recommender_model.recommend_items(0))

    # Popularity Model
    pop_recommender_model = PopularityRecommender(interactions_full_df)
    print(pop_recommender_model.recommend_items(0))
