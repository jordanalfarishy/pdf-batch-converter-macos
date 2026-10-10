# PRD — PDF Batch Converter for macOS

## Ringkasan

PDF Batch Converter mengubah kumpulan folder gambar menjadi PDF secara batch di macOS. Satu subfolder menghasilkan satu PDF. Pengguna memilih lokasi sumber, lokasi hasil, dan tingkat kompresi melalui antarmuka desktop sederhana.

## Pengguna dan kebutuhan

Pengguna yang memiliki banyak album, halaman hasil scan, atau kumpulan gambar per folder ingin membuat PDF tanpa membuka dan mengekspor folder satu per satu. Urutan halaman dan keamanan file hasil yang sudah ada adalah kebutuhan utama.

## Tujuan

- Menghasilkan satu PDF per subfolder gambar dengan urutan halaman numerik yang dapat diprediksi.
- Mendukung JPEG, PNG, dan WebP dalam satu folder yang sama.
- Memberi pilihan antara kualitas asli dan tiga tingkat kompresi.
- Menunjukkan progres, hasil per folder, gambar yang dilewati, kegagalan, dan ringkasan akhir.
- Menjaga PDF lama tetap utuh saat nama hasil bertabrakan.

## Alur utama

1. Pengguna memilih folder induk yang berisi subfolder gambar.
2. Pengguna memilih folder output yang berbeda.
3. Pengguna memilih None, Low, Medium, atau High.
4. Pengguna memulai konversi dan memantau Activity.
5. Pengguna membuka PDF dari folder output; bila perlu, pengguna dapat membatalkan batch yang sedang berjalan.

## Persyaratan fungsional

| ID | Persyaratan |
| --- | --- |
| F1 | Setiap subfolder langsung pada folder induk diproses menjadi paling banyak satu PDF. |
| F2 | Gambar JPEG, PNG, dan WebP diurutkan menurut angka dalam nama file sebelum masuk PDF. |
| F3 | File tersembunyi, symlink, subfolder lebih dalam, dan file non-gambar diabaikan. |
| F4 | Gambar yang rusak/tidak terbaca dilewati; folder tanpa gambar terbaca dilaporkan sebagai skipped. |
| F5 | None mempertahankan JPEG/PNG sebagai sumber asli dan mentranskode WebP menjadi PNG lossless. |
| F6 | Low/Medium/High mengubah gambar ke JPEG dengan kualitas dan batas sisi terpanjang sesuai README. Transparansi diratakan di atas latar putih. |
| F7 | Output ditulis sebagai file sementara lalu dipublikasikan setelah PDF selesai; file lama tidak boleh ditimpa. |
| F8 | Jika nama hasil sudah ada atau dua nama folder menjadi sama setelah dibersihkan, nama output diberi sufiks angka. |
| F9 | Pengguna dapat membatalkan batch; tugas yang belum dimulai dan tugas yang mencapai titik pembatalan tidak menghasilkan PDF. |
| F10 | Activity menampilkan progres jumlah folder, hasil per folder, dan jumlah berhasil, dilewati, serta gagal. |

## Persyaratan nonfungsional

- UI tetap responsif selama konversi dan semua pembaruan widget terjadi di thread utama.
- Aplikasi dapat dibuild sebagai bundle macOS arm64 mandiri dari sumber proyek.
- Kegagalan satu folder tidak menghentikan konversi folder lain.
- Nama file output aman untuk sistem file dan dibatasi panjangnya.
- Build lokal tidak memerlukan akun Apple Developer; distribusi publik melalui Gatekeeper memerlukan penandatanganan dan notarization terpisah.

## Kriteria penerimaan

- Folder berisi `1.jpg`, `2.png`, dan `10.webp` menghasilkan PDF tiga halaman dalam urutan itu.
- Gambar rusak di tengah folder tidak menghentikan PDF dari gambar lain dan tercatat sebagai skipped image.
- PDF output yang sudah ada tetap identik setelah batch; hasil baru memakai sufiks nomor.
- Folder kosong dan folder tersembunyi tidak menghasilkan PDF.
- Pembatalan sebelum sebuah folder diproses tidak meninggalkan PDF sementara.
- Bundle `.app` dapat diluncurkan di Mac arm64 tempat build dilakukan dan menampilkan UI lengkap.

## Di luar cakupan versi ini

- Pemrosesan rekursif subfolder lebih dalam.
- Menggabungkan semua subfolder menjadi satu PDF.
- Pengurutan halaman manual dan pratinjau gambar.
- Pengaturan metadata PDF, OCR, dan enkripsi.
- Penandatanganan sertifikat Apple Developer dan notarization.
