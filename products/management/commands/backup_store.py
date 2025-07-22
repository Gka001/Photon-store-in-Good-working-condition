import os
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path


class Command(BaseCommand):
    help = "Backs up Product data to a fixture and zips media folder"

    def handle(self, *args, **kwargs):
        # Set paths
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        fixtures_dir = base_dir / 'fixtures'
        backups_dir = base_dir / 'backups'
        media_dir = base_dir / 'media'

        # Ensure folders exist
        fixtures_dir.mkdir(exist_ok=True)
        backups_dir.mkdir(exist_ok=True)

        # Step 1: Dump product data to fixture
        fixture_path = fixtures_dir / 'products_fixture.json'
        self.stdout.write("📦 Dumping product data to fixture...")
        with open(fixture_path, 'w') as f:
            call_command('dumpdata', 'products.Product', indent=4, stdout=f)
        self.stdout.write(f"✅ Product data backed up to {fixture_path}")

        # Step 2: Zip the media folder
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        media_zip_path = backups_dir / f'media_backup_{timestamp}.zip'
        self.stdout.write("🖼️ Zipping media folder...")

        with zipfile.ZipFile(media_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(media_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, media_dir)
                    zipf.write(abs_path, arcname=rel_path)

        self.stdout.write(f"✅ Media folder zipped to {media_zip_path}")
        self.stdout.write("🎉 Backup completed successfully!")
