import random
import string
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# veritabanı modeli
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(512), nullable=False)
    short_code = db.Column(db.String(6), unique=True, nullable=False)
    visits = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<URL {self.short_code}>'


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        # kodun benzersiz olduğundan emin ol
        if URL.query.filter_by(short_code=code).first() is None:
            return code

# veritabanı tablolarını oluştur
with app.app_context():
    db.create_all()


# routelar
@app.route('/', methods=['GET', 'POST'])
def index():
    
    # ana sayfa (url kısaltma formu ve kısaltılan URL'lerin listesi)
    
    if request.method == 'POST':
        original_url = request.form['url']
        
        # aynı URL daha önce kısaltılmış mı?
        url_entry = URL.query.filter_by(original_url=original_url).first()
        
        if url_entry:
            # kısaltılmışsa mevcut kodu kullan
            short_code = url_entry.short_code
        else:
            # kısaltılmamşısa yeni oluştur
            short_code = generate_short_code()
            new_url = URL(original_url=original_url, short_code=short_code)
            db.session.add(new_url)
            db.session.commit()
        
        short_url = request.url_root + short_code
        return render_template('index.html', short_url=short_url, urls=URL.query.all())

    # tüm kısaltılmış urlleri listele
    return render_template('index.html', urls=URL.query.all())


@app.route('/<short_code>')
def redirect_to_url(short_code):

    url_entry = URL.query.filter_by(short_code=short_code).first()
    
    if url_entry:
        # ziyaret sayısını artır
        url_entry.visits += 1
        db.session.commit()
        
        # orijinal urlye yönlendir

        return redirect(url_entry.original_url)
    else:
        # kısa kod bulunamazsa 404 not found hatası ver
        abort(404)


@app.route('/stats')
def stats():
    #istatistik sayfası (tüm kısaltılan urller ve ziyaret sayıları)

    # ziyaret sayısına göre büyükten küçüğe listele
    urls = URL.query.order_by(URL.visits.desc()).all()
    return render_template('stats.html', urls=urls)


if __name__ == '__main__':
    # debug modu sadece geliştirme aşamasında kullanılmalı
    app.run(debug=True)