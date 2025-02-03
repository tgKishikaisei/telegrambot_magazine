from .start_menu import router as start_menu_router
from .catalog import router as catalog_router
from .cart import router as cart_router
from .account import router as account_router
from .search import router as search_router
from .favorites import router as favorites_router
from .review import router as review_router
from .support import router as support_router
from .history import router as history_router

def register_all_handlers(dp):
    dp.include_router(start_menu_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(account_router)
    dp.include_router(search_router)
    dp.include_router(favorites_router)
    dp.include_router(review_router)
    dp.include_router(support_router)
    dp.include_router(history_router)