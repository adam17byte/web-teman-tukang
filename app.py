from flask import (
    Flask, render_template, redirect, url_for,
    request, session, flash, get_flashed_messages
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahasia-teman-tukang-yang-kuat'

SIMULATED_ORDERS = {
    101: {'layanan': 'Perbaikan Pipa Bocor', 'tukang': 'Ahmad Imam', 'tanggal': '15/10/2025', 'status': 'Menunggu'},
    102: {'layanan': 'Pemasangan Keramik', 'tukang': 'Ibu Rina', 'tanggal': '01/11/2025', 'status': 'Selesai'},
}

SIMULATED_TUKANG = [
    {"id": 1, "nama": "Budi Santoso", "keahlian": "Pengecatan & Plafon",
     "rating": 4.8, "jumlah_review": 12, "pengalaman": "10 tahun pengalaman", "foto":"https://placehold.co/150x150"},
    {"id": 2, "nama": "Siti Aminah", "keahlian": "Listrik & Instalasi",
     "rating": 4.5, "jumlah_review": 8, "pengalaman": "7 tahun pengalaman", "foto":"https://placehold.co/150x150"},
    {"id": 3, "nama": "Agus Wijaya", "keahlian": "Pemasangan Keramik",
     "rating": 4.7, "jumlah_review": 10, "pengalaman": "5 tahun pengalaman", "foto":"https://placehold.co/150x150"},
]

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user' in session else redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('email')
        flash("Login berhasil!")
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session['username'] = request.form.get('username')
        session['email'] = request.form.get('email')
        flash("Registrasi berhasil! Silakan login.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Anda harus login untuk mengakses dashboard.")
        return redirect(url_for('login'))
    
    return render_template(
        'dashboard.html', 
        user=session.get('user'), 
        active_page='dashboard'
    )

@app.route('/riwayat-pesanan')
def riwayat_pesanan():
    if 'user' not in session:
        flash("Anda harus login untuk melihat riwayat pesanan.")
        return redirect(url_for('login'))
    
    return render_template(
        'riwayat_pesanan.html',
        orders=SIMULATED_ORDERS,
        active_page='riwayat_pesanan'
    )

@app.route('/ulasan/<int:order_id>', methods=['GET', 'POST'])
def tulis_ulasan(order_id):
    if request.method == 'POST':
        flash("Ulasan berhasil dikirim!")
        return redirect(url_for('riwayat_pesanan'))

    return render_template('tulis_ulasan.html', order_id=order_id)

@app.route('/deteksi', methods=['GET', 'POST'])
def deteksi():
    get_flashed_messages()

    if 'user' not in session:
        flash("Anda harus login untuk menggunakan fitur deteksi.")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files.get('file')
        
        if not file or file.filename == '':
            flash('Tidak ada file yang dipilih.')
            return redirect(request.url)

        flash('File berhasil diupload.')
        return redirect(url_for('deteksi_hasil'))
    
    return render_template(
        'deteksi.html',
        active_page='deteksi'
    )

@app.route('/deteksi-hasil')
def deteksi_hasil():
    if 'user' not in session:
        flash("Anda harus login untuk melihat hasil deteksi.")
        return redirect(url_for('login'))
    
    hasil = {
        'gambar_rusak': 'https://placehold.co/600x400/808080/FFFFFF?text=Dinding+Retak',
        'analisis': (
            'Ditemukan kerusakan struktural berupa retakan lebar, kemungkinan akibat '
            'pergerakan tanah atau beban berlebih. Perlu evaluasi fondasi.'
        ),
        'faktor': (
            'Terjadi karena fondasi penurunan tidak merata dan kelembaban tinggi di area retak.'
        )
    }
    
    return render_template(
        'deteksi_hasil.html',
        hasil=hasil,
        active_page='deteksi'
    )

@app.route("/rekomendasi")
def rekomendasi():
    return render_template("rekomendasi.html", tukangs=SIMULATED_TUKANG)

@app.route("/lihat-tukang/<int:tukang_id>")
def lihat_tukang(tukang_id):
    tukang = next((t for t in SIMULATED_TUKANG if t["id"] == tukang_id), None)
    
    if not tukang:
        flash("Tukang tidak ditemukan.")
        return redirect(url_for("rekomendasi"))
    
    return render_template("lihat_tukang.html", tukang=tukang)

@app.route("/chat")
def chat():
    tukang = {
        "nama": "Tukang Contoh",
        "telepon": "081234567890",
    }
    return render_template("chat.html", tukang=tukang)

@app.route("/profil_user")
def profil_user():
    customer = {
        "nama": "Andi Pratama",
        "telepon": "081234567890",
        "alamat": "Jl. Merdeka No. 10, Semarang"
    }
    return render_template("profil_user.html", customer=customer)

@app.route("/profil_edit", methods=["GET", "POST"])
def profil_edit():
    if request.method == "POST":
        flash("Profil berhasil diperbarui!")
        return redirect(url_for("profil_edit"))

    return render_template("profil_edit.html", active_page="profil_edit")

@app.route("/notifikasi")
def notifikasi():
    notifications = [
        {
            "pesan": "Tukang Budi membalas pesan Anda",
            "detail": "“Baik, saya bisa datang besok pagi.”",
            "tanggal": "08/11/2025"
        },
        {
            "pesan": "Pesanan Anda telah dikirim ke Tukang Siti Aminah",
            "detail": "Layanan: Instalasi Listrik Rumah",
            "tanggal": "07/11/2025"
        },
        {
            "pesan": "Tukang Agus mengirim pesan baru",
            "detail": "“Apakah warna keramiknya putih polos?”",
            "tanggal": "06/11/2025"
        }
    ]
    return render_template("notifikasi.html", notifications=notifications, active_page="notifikasi")

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah logout.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
