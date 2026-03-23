import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.ingest import ingest_pdf

base_folder = "data"

domains = ["security", "finance", "tech", "general"]

for domain in domains:
    folder = os.path.join(base_folder, domain)

    print(f"\n📂 Processing domain: {domain}")

    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            try:
                print(f"🚀 Ingesting {file}...")
                ingest_pdf(os.path.join(folder, file), domain=domain)
            except Exception as e:
                print(f"❌ Failed on {file}: {e}")

print("\n✅ All domains ingested successfully!")
