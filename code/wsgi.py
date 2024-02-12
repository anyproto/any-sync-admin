from app import app
from app import cfg

if __name__ == "__main__":
    app.run(**cfg['listen'])
