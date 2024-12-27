import numpy as np
import pandas as pd
from mai_recsys.utils import event_types, event_type_strength, modify_interactions
from mai_recsys.evaluator import ModelEvaluator, EVAL_RANDOM_SAMPLE_NON_INTERACTED_ITEMS
from mai_recsys.models.cf_model import CFRecommender
from mai_recsys.models.cb_model import CBRecommender
from mai_recsys.models.popularity_model import PopularityRecommender
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
import asyncio

# Создание асинхронного движка и сессии
engine = create_async_engine('postgresql+asyncpg://ecommerce:mypass@localhost:5432/ecommerce', echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def fetch_data(session, query):
    result = await session.execute(text(query))
    return result.fetchall()

async def load_data_from_db():
    async with async_session_maker() as session:
        async with session.begin():
            # Загрузка данных из таблиц базы данных
            item_categories_query = 'SELECT name as item_category_name, id as item_category_id FROM categories'
            interactions_query = 'SELECT product_id as item_id, user_id, event_type as event FROM user_events'
            items_query = 'SELECT name as item_name, id as item_id, category_id as item_category_id FROM products'

            item_categories = await fetch_data(session, item_categories_query)
            interactions = await fetch_data(session, interactions_query)
            items = await fetch_data(session, items_query)
            
            # Преобразование данных в DataFrame
            item_categories = pd.DataFrame(item_categories, columns=['item_category_name', 'item_category_id'])
            interactions = pd.DataFrame(interactions, columns=['item_id', 'user_id', 'event'])
            items = pd.DataFrame(items, columns=['item_name', 'item_id', 'item_category_id'])

            # Фильтрация interactions
            interactions = interactions[interactions['event'].isin(event_types)]

            # Загрузка embeddings
            # embeddings = pd.read_pickle('data/embeddings.pkl')
           
            return item_categories, interactions, items#, embeddings

async def mlic(id):
    item_categories, interactions, items = await load_data_from_db()

    interactions_full_df, interactions_train_df, interactions_test_df = modify_interactions(interactions)
    interactions_full_indexed_df, interactions_train_indexed_df, interactions_test_indexed_df = modify_interactions(interactions, indexing=True)
    async with async_session_maker() as session:
        async with session.begin():
            have_any_interactions_query = text('SELECT count(user_id) FROM user_events where user_id=:id')
            result = await session.execute(have_any_interactions_query, {"id": id})
            res=result.fetchone()[0]
            
    if(res>0):
     # Collaborative Filtering
        cf_recommender_model = CFRecommender(interactions_train_df, items)
        return cf_recommender_model.recommend_items(id)['item_id'].tolist()
    else:
    # # Content Based
    # cb_recommender_model = CBRecommender(interactions_full_indexed_df, embeddings)
    # print(cb_recommender_model.recommend_items(1))

    # Popularity Model
        pop_recommender_model = PopularityRecommender(interactions_full_df)
        return pop_recommender_model.recommend_items(id)['item_id'].tolist()


