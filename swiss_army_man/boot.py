try:
    from abc import ABC
    class Bootloader(ABC):
        def before_boot(self):
            print("Before boot...")
            import sys
            import os
            from dotenv import load_dotenv
            from . import project_root

            first_path = sys.path[0]
            if first_path != project_root():
                sys.path.insert(0, project_root())
            current_pythonpath = os.environ.get('PYTHONPATH', '')
            pythonpath_list = current_pythonpath.split(os.pathsep) if current_pythonpath else []
            if not pythonpath_list or pythonpath_list[0] != project_root():
                # Insert the project root at the beginning of the list
                pythonpath_list.insert(0, project_root())

                # Join the list back into a string and set the environment variable
                new_pythonpath = os.pathsep.join(pythonpath_list)
                os.environ['PYTHONPATH'] = new_pythonpath
            if os.path.exists(project_root(".env")):
                load_dotenv(project_root(".env"))

        def boot(self):
            self.before_boot()
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
            print("After boot...")
            return True
except:
    # nbd...
    True