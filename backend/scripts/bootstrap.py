"""Dijalankan otomatis saat container backend start: skema -> dataset -> akun (hanya jika belum ada)."""
from . import import_dataset, seed_users
from .common import LOAD_ORDER, connect


def main() -> None:
    conn = connect()
    import_dataset.ensure_schema(conn)
    if import_dataset.is_loaded(conn):
        print("Dataset sudah terisi.")
    else:
        counts = import_dataset.load_all(conn, who="bootstrap")
        print(f"Dataset dimuat: {sum(counts[t] for t in LOAD_ORDER):,} baris di {len(LOAD_ORDER)} tabel.")
    created = seed_users.seed(conn)
    seed_users.write_credentials(created)


if __name__ == "__main__":
    main()
