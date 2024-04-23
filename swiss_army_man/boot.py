try:
    from abc import ABC
    class Bootloader(ABC):
        def boot(self):
            print("Booting...")
            from django.apps import apps
            from dotenv import load_dotenv

            if not apps.ready:
                import django
                import os

                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
                django.setup()
            print("After boot...")
            self.after_boot()

        def after_boot(self):
            return True

    Bootloader().boot()
except:
    # nbd...
    True