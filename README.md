# PDF Batch Converter for macOS

Aplikasi desktop untuk membuat satu PDF dari setiap subfolder gambar. Gambar dalam tiap subfolder diurutkan secara numerik berdasarkan nama file. Format yang didukung: JPEG, PNG, dan WebP.

![Ikon PDF Batch Converter](assets/app_icon.png)

## Cara pakai

1. Pilih **Input folder** yang berisi subfolder gambar.
2. Pilih **Save PDFs to** sebagai lokasi hasil yang berbeda dari folder input.
3. Pilih tingkat kompresi lalu klik **Convert folders**.

Contoh: gambar dalam `Input/Album A/` menghasilkan `Output/Album A.pdf`. Aplikasi membaca gambar di tingkat teratas setiap subfolder. Subfolder yang lebih dalam, file tersembunyi, symlink, dan file non-gambar diabaikan.

| Pilihan | Hasil |
| --- | --- |
| None | JPEG/PNG dipakai langsung; WebP menjadi PNG lossless. |
| Low | JPEG 85%, sisi terpanjang maksimal 3000 px. |
| Medium | JPEG 65%, sisi terpanjang maksimal 2000 px. |
| High | JPEG 40%, sisi terpanjang maksimal 1200 px. |

Gambar rusak dilewati dan jumlahnya muncul di Activity. Folder tanpa gambar yang dapat dibaca dilewati. PDF dengan nama yang sudah ada tidak ditimpa; hasil baru mendapat nomor, misalnya `Album (2).pdf`. Tombol **Cancel** menghentikan tugas yang belum selesai saat proses mencapai titik pembatalan berikutnya.

## Menjalankan dari sumber

Butuh macOS dan Python 3.14 untuk lingkungan yang sama dengan build teruji.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pdfconverter.py
```

## Build aplikasi macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-build.txt
python build_app.py
```

Hasilnya ada di `dist/PDF Batch Converter.app`. Ikon sumber ada di `assets/app_icon.png`; file `.icns` untuk bundle dibuat saat build. Build lokal ini untuk arsitektur Mac yang menjalankan perintah build. Bundle ditandatangani secara ad hoc oleh PyInstaller, tetapi belum memakai sertifikat Apple Developer atau notarization untuk distribusi umum.

## Tes

```bash
python -m unittest discover -s tests -v
```

Tes mencakup gambar campuran, urutan numerik, gambar rusak, benturan nama output, folder tersembunyi/symlink, dan pembatalan.

## Dokumen produk

Kebutuhan produk dan kriteria penerimaan tercatat di [PRD.md](PRD.md).
