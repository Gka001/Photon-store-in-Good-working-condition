import os
import glob
import zipfile
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Restore products, orders, and user data from fixtures, and media from the latest backup.'

    def handle(self, *args, **kwargs):
        # ✅ Ensure required folders exist
        os.makedirs('fixtures', exist_ok=True)
        os.makedirs('media', exist_ok=True)

        def restore_model(label, fixture_filename):
            fixture_path = os.path.join('fixtures', fixture_filename)
            if os.path.exists(fixture_path):
                self.stdout.write(f"🔄 Restoring {label} from {fixture_filename}...")
                call_command('loaddata', fixture_path)
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {fixture_filename} not found. Skipping {label}."))

        # ✅ Restore data
        restore_model("Products", 'products_fixture.json')
        restore_model("Orders", 'orders_fixture.json')
        restore_model("Custom Users", 'users_fixture.json')

        # ✅ Restore media from latest backup
        media_backups = sorted(glob.glob('backups/media_backup_*.zip'))
        if media_backups:
            latest_media_backup = media_backups[-1]
            self.stdout.write(f"📦 Restoring media files from {latest_media_backup}...")
            with zipfile.ZipFile(latest_media_backup, 'r') as zip_ref:
                zip_ref.extractall('media')
            self.stdout.write(self.style.SUCCESS("✅ Media files restored successfully."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ No media backup zip found in backups/. Skipping media restore."))

        self.stdout.write(self.style.SUCCESS("✅ Store restore complete."))
