import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-anime-key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # PostgreSQL bağlantı ayarları
    # Lütfen 'SIFRE_BURAYA' kısmını kendi PostgreSQL şifrenizle değiştirin.
    # Kullanıcı adınız farklıysa 'postgres' kısmını da güncelleyin.
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/AnimeDatabase'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
