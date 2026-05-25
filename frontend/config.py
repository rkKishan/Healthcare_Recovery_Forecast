import os

# Disable Next.js telemetry
os.environ['NEXT_TELEMETRY_DISABLED'] = '1'

# Development server configuration
FRONTEND_PORT = os.getenv('FRONTEND_PORT', 3000)
BACKEND_PORT = os.getenv('BACKEND_PORT', 8000)

# Frontend paths
FRONTEND_ROOT = os.path.dirname(__file__)
FRONTEND_APP = os.path.join(FRONTEND_ROOT, 'app')
FRONTEND_COMPONENTS = os.path.join(FRONTEND_ROOT, 'components')
FRONTEND_LIB = os.path.join(FRONTEND_ROOT, 'lib')

# Configuration
ENVIRONMENT = os.getenv('NODE_ENV', 'development')
DEBUG = ENVIRONMENT == 'development'

# API Configuration
API_BASE_URL = os.getenv('NEXT_PUBLIC_API_BASE_URL', f'http://localhost:{BACKEND_PORT}')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

# Analytics (optional)
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'false').lower() == 'true'

# Feature flags
FEATURES = {
    'real_time_updates': os.getenv('FEATURE_REALTIME', 'false').lower() == 'true',
    'advanced_filtering': os.getenv('FEATURE_FILTERS', 'true').lower() == 'true',
    'pdf_export': os.getenv('FEATURE_PDF_EXPORT', 'true').lower() == 'true',
    'lottie_animations': os.getenv('FEATURE_LOTTIE', 'true').lower() == 'true',
}
