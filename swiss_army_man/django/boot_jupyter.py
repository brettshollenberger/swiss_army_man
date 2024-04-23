try:
    from . import Bootloader
    class JupyterBootloader(Bootloader):
        def before_boot(self):
            print("Jupe before boot...")
            import os
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
            super().before_boot()
except:
    # Not in Django environment, nbd
    True