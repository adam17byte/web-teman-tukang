from flask import (
    Flask, render_template, redirect, url_for,
    request, session, flash, get_flashed_messages,
)
import mysql.connector 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahasia-teman-tukang-yang-kuat'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="capstone_web"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Email tidak terdaftar!", "danger")
            return redirect(url_for('login'))
        
        elif user['password'] != password:
            flash("Password salah!", "danger")
            return redirect(url_for('login'))
        
        else:
            session['user_id']    = user['id_user']
            session['user_email'] = user['email']
            session['user_role']  = user['role']
            flash("Login berhasil!", "success")
            return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']

        if len(password) < 6 or len(password) > 8:
            flash("Password harus 6-8 karakter!", "danger")
            return redirect(url_for('register'))
        
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'customer')",
            (username, email, password)
        )
        db.commit()

        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/riwayat-pesanan')
def riwayat_pesanan():
    if 'user_id' not in session:  
        flash("Anda harus login untuk melihat riwayat pesanan.", "warning")
        return redirect(url_for('login'))
    
    simulated_orders = {
        101: {'layanan': 'Perbaikan Pipa Bocor', 'tukang': 'Ahmad Imam', 'tanggal': '15/10/2025', 'status': 'Menunggu'},
        102: {'layanan': 'Pemasangan Keramik', 'tukang': 'Ibu Rina', 'tanggal': '01/11/2025', 'status': 'Selesai'},
    }

    return render_template(
        'riwayat_pesanan.html',
        orders=simulated_orders,
        active_page='riwayat_pesanan'
    )

@app.route('/ulasan/<int:order_id>', methods=['GET', 'POST'])
def tulis_ulasan(order_id):
    if request.method == 'POST':
        return redirect(url_for('riwayat_pesanan'))
    
    return render_template('tulis_ulasan.html', order_id=order_id)

@app.route('/deteksi', methods=['GET', 'POST'])
def deteksi():
    get_flashed_messages()

    if 'user_id' not in session:
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
    simulated_tukang = [
        {"id": 1, "nama": "Budi Santoso", "keahlian": "Pengecatan & Plafon",
         "rating": 4.8, "jumlah_review": 12, "pengalaman": "10 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
        {"id": 2, "nama": "Siti Aminah", "keahlian": "Listrik & Instalasi",
         "rating": 4.5, "jumlah_review": 8, "pengalaman": "7 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
        {"id": 3, "nama": "Agus Wijaya", "keahlian": "Pemasangan Keramik",
         "rating": 4.7, "jumlah_review": 10, "pengalaman": "5 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
    ]
    
    return render_template("rekomendasi.html", tukangs=simulated_tukang)

@app.route("/lihat-tukang/<int:tukang_id>")
def lihat_tukang(tukang_id):
    simulated_tukang = [
        {"id": 1, "nama": "Budi Santoso", "keahlian": "Pengecatan & Plafon",
         "rating": 4.8, "jumlah_review": 12, "pengalaman": "10 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
        {"id": 2, "nama": "Siti Aminah", "keahlian": "Listrik & Instalasi",
         "rating": 4.5, "jumlah_review": 8, "pengalaman": "7 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
        {"id": 3, "nama": "Agus Wijaya", "keahlian": "Pemasangan Keramik",
         "rating": 4.7, "jumlah_review": 10, "pengalaman": "5 tahun pengalaman",
         "foto": "https://placehold.co/150x150"},
    ]
    tukang = next((t for t in simulated_tukang if t["id"] == tukang_id), None)
    
    if not tukang:
        flash("Tukang tidak ditemukan.", "warning")
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
