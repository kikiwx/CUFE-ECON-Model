

import os
from pathlib import Path


BASE_DIR = Path(__file__).parent.absolute()
TEMP_DIR = os.path.join(BASE_DIR, 'temp')


MODEL_PATH = os.environ.get('MODEL_PATH', r"/model")
DEVICE = os.environ.get('DEVICE', 'auto')



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'


    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']


    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}


class ModelConfig:
    DEFAULT_MAX_TOKENS = int(os.environ.get('DEFAULT_MAX_TOKENS', 1024))
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', 0.7))
    MAX_TOKENS_LIMIT = 4096
    TEMPERATURE_MIN = 0.1
    TEMPERATURE_MAX = 2.0

    ENABLE_THINKING = os.environ.get('ENABLE_THINKING', 'True').lower() == 'true'


class ReportConfig:

    REPORT_CLEANUP_HOURS = int(os.environ.get('REPORT_CLEANUP_HOURS', 24))

    MAX_ACTIVE_REPORTS = int(os.environ.get('MAX_ACTIVE_REPORTS', 10))

    POLLING_INTERVAL = int(os.environ.get('POLLING_INTERVAL', 2))

    REPORT_TIMEOUT = int(os.environ.get('REPORT_TIMEOUT', 30))


class LogConfig:
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    MAX_LOG_SIZE = 10 * 1024 * 1024
    BACKUP_COUNT = 5


class SecurityConfig:

    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))

    MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', 4000))
    MAX_TOPIC_LENGTH = int(os.environ.get('MAX_TOPIC_LENGTH', 200))
    MAX_REQUIREMENTS_LENGTH = int(os.environ.get('MAX_REQUIREMENTS_LENGTH', 2000))


class DevelopmentConfig(Config):
    DEBUG = True
    HOST = '127.0.0.1'


class ProductionConfig(Config):
    DEBUG = False

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    TESTING = True
    DEBUG = True

    MODEL_PATH = os.environ.get('TEST_MODEL_PATH', MODEL_PATH)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

def ensure_directories():
    directories = [
        TEMP_DIR,
        Config.UPLOAD_FOLDER,
        os.path.dirname(LogConfig.LOG_FILE)
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def validate_config():
    errors = []

    if not os.path.exists(MODEL_PATH):
        errors.append(f"模型路径不存在: {MODEL_PATH}")

    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        required_vars = ['SECRET_KEY']
        for var in required_vars:
            if not os.environ.get(var):
                errors.append(f"缺少必要的环境变量: {var}")

    if errors:
        raise ValueError("配置验证失败:\n" + "\n".join(errors))


if __name__ == "__main__":
    ensure_directories()
    validate_config()
    print("配置验证通过!")
