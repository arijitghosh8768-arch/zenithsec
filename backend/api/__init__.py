from api.auth.routes import router as auth_router
from api.chatbot.routes import router as chatbot_router
from api.url_scanner.routes import router as url_scanner_router
from api.file_scanner.routes import router as file_scanner_router
from api.learning_hub.routes import router as learning_router
from api.code_vault.routes import router as code_vault_router
from api.portfolio.routes import router as portfolio_router
from api.analytics.routes import router as analytics_router
from api.certificates.routes import router as certificates_router

all_routers = [
    auth_router,
    chatbot_router,
    url_scanner_router,
    file_scanner_router,
    learning_router,
    code_vault_router,
    portfolio_router,
    analytics_router,
    certificates_router,
]
