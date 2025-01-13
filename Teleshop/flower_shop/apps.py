from django.apps import AppConfig

class FlowerShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flower_shop'

    def ready(self):
        # Импортируем сигналы
        import flower_shop.signals