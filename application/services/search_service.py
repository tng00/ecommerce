from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.repositories.product_repository import ProductRepository
from app.presentation.schemas.search_schema import QueryParams
from app.application.exceptions import ServiceException


class SearchService:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    async def get_search_results(self, params: QueryParams, db: AsyncSession):
        try:
            products_data = await self.product_repo.fetch_products(params, db)
            categories = await self.product_repo.get_categories(db)
            return {
                "products": products_data["products"],
                "categories": categories,
                "total_products": products_data["total_products"],
            }
        except Exception as e:
            raise ServiceException(f"Error fetching search results: {str(e)}")
