"""Grava em data/raw os recortes em parquet do HMDA e da NSMO, a partir dos CSV.

Uso, da raiz do projeto, depois de baixar os dois CSV: python -m src.raw_parquet
"""

from src.hmda import save_hmda_parquet
from src.nsmo import save_nsmo_parquet

if __name__ == "__main__":
    hmda_path = save_hmda_parquet()
    print(f"OK: {hmda_path} ({hmda_path.stat().st_size / 1e6:,.1f} MB)")
    nsmo_path = save_nsmo_parquet()
    print(f"OK: {nsmo_path} ({nsmo_path.stat().st_size / 1e6:,.1f} MB)")
