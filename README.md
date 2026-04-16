# RIP Daemon (COSC 364 Assignment Helper)

Implementasi RIP daemon berbasis Python 3 untuk simulasi beberapa router di satu mesin melalui UDP localhost (`127.0.0.1`).

## Fitur yang diimplementasikan

- Parsing file konfigurasi (`router-id`, `input-ports`, `outputs`, timer).
- Validasi syntax + range value untuk field penting.
- Daemon berbasis event loop `select()` untuk multi-socket input.
- RIP response packet encode/decode (dengan `router-id` di field 16-bit header).
- Periodic unsolicited updates.
- Triggered update **hanya** saat route jadi invalid (metric `16`).
- Timeout + garbage collection untuk route dinamis.
- Split horizon dengan poisoned reverse (packet per-neighbor).
- Tabel routing dicetak rapi, tanpa debug output tambahan.

## Struktur proyek

- `ripd.py`: entrypoint daemon.
- `riplib/config.py`: parser + validator konfigurasi.
- `riplib/packet.py`: format packet RIP.
- `riplib/router.py`: core logic routing daemon.
- `sample_configs/*.conf`: contoh topologi 4 router.
- `tools/demo_harness.py`: script otomatis demo (normal → failure → recovery).
- `tests/*.py`: unit tests.

## Format konfigurasi

Contoh:

```text
router-id 1
input-ports 6101, 6102
outputs 6201-1-2, 6401-5-4
periodic-timer 2
timeout-timer 12
garbage-timer 8
jitter false
```

Keterangan `outputs`:

- `6201-1-2` berarti: kirim ke port input router tetangga `6201`, link metric `1`, neighbor router-id `2`.

## Menjalankan satu router

```bash
python3 ripd.py sample_configs/r1.conf
```

Jalankan 1 terminal per router untuk simulasi jaringan penuh.

## Testing

### 1) Unit test (cepat)

```bash
python3 -m unittest discover -s tests -v
```

### 2) Demo otomatis (start, kill, restart)

```bash
python3 tools/demo_harness.py
```

Hasil output daemon akan disimpan di folder `logs/`:

- `logs/r1.log`
- `logs/r2.log`
- `logs/r3.log`
- `logs/r4.log`

## Skenario manual yang disarankan untuk demo inspeksi

1. Buka 4 terminal dan jalankan:
   - `python3 ripd.py sample_configs/r1.conf`
   - `python3 ripd.py sample_configs/r2.conf`
   - `python3 ripd.py sample_configs/r3.conf`
   - `python3 ripd.py sample_configs/r4.conf`
2. Tunggu konvergensi awal (lihat tabel routing tiap router).
3. Matikan salah satu proses (misal router 2).
4. Verifikasi router lain menandai route terkait menjadi metric `16`, lalu reconverge.
5. Jalankan lagi router yang dimatikan.
6. Verifikasi jaringan konvergen kembali ke state awal.

## Catatan

- Program dirancang untuk dijalankan di Linux/macOS via command line Python 3.
- Semua komunikasi menggunakan UDP localhost (`127.0.0.1`).
- Untuk topologi tugas resmi, sesuaikan file di `sample_configs/` dengan Figure 1 dari soal.
