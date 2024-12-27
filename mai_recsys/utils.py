import pandas as pd
import numpy as np
import math
from sklearn.model_selection import train_test_split

event_types = ['view', 'add_to_cart', 'purchase']

event_type_strength = {
   'view': 1.0,
   'add_to_cart': 3.0,
   'purchase': 2.0
}

class DataGenerator:
    def __init__(self, items: pd.DataFrame):
        self.items = items

    def get_sample(self, sample_size):
        category_id = np.random.randint(84)
        cat_items_num = len(self.items[self.items['item_category_id'] == category_id])
        # Проверка на слишком маленькие категории
        if cat_items_num < sample_size:
            sample_size  = cat_items_num + 2
        items_sample = self.items.loc[self.items['item_category_id'] == category_id].sample(sample_size, replace=True)['item_id']
        events_sample = np.random.choice(event_types, sample_size, p=[0.8, 0.15, 0.05])
        return items_sample, events_sample, sample_size

    def gen_data(self, users_num=100, sample_sizes=[3]):
        interactions = pd.DataFrame(columns=pd.Series(['timestamp', 'item_id', 'user_id', 'event']))
        timestamp = pd.Timestamp('2024-12-01T12')
        row = 0
        for user_id in range(users_num):
            for sample_size in sample_sizes:
                items_sample, events_sample, new_sample_size = self.get_sample(sample_size)
                for j in range(new_sample_size):
                    interactions.loc[row] = [timestamp, items_sample.iloc[j], user_id, events_sample[j]]
                    row += 1
        return interactions

def smooth_user_preference(x):
    return math.log(1+x, 2)

def modify_interactions(interactions, verbose=False, indexing=False):
    interactions['event_strength'] = interactions['event'].apply(lambda x: event_type_strength[x])

    interactions_full_df = interactions \
                        .groupby(['user_id', 'item_id'])['event_strength'].sum() \
                        .apply(smooth_user_preference).reset_index()

    if verbose:
        print('# of unique user/item interactions: %d' % len(interactions_full_df))

    interactions_train_df, interactions_test_df = train_test_split(interactions_full_df,
                                       stratify=interactions_full_df['user_id'],
                                       test_size=0.20,
                                       random_state=42)

    if verbose:
        print('# interactions on Train set: %d' % len(interactions_train_df))
        print('# interactions on Test set: %d' % len(interactions_test_df))

    # indexing by user_id to speed up the searches during evaluation
    if indexing:
        interactions_full_df = interactions_full_df.set_index('user_id')
        interactions_train_df = interactions_train_df.set_index('user_id')
        interactions_test_df = interactions_test_df.set_index('user_id')

    return interactions_full_df, interactions_train_df, interactions_test_df
