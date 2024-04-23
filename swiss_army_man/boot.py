try:
    class Bootloader():
        @staticmethod
        def boot():
            print("Booting...")
            from django.apps import apps
            from dotenv import load_dotenv

            if not apps.ready:
                import django
                import os

                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
                django.setup()
            Bootloader.after_boot()

        @staticmethod
        def after_boot():
            print("oh no it's the old me")
            return True

    Bootloader.boot()
except:
    # nbd...
    True