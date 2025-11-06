import os
import sqlite3
from flask import Flask, request, redirect
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ma_cle_secrete_admin_2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialisation base de données
def init_db():
    conn = sqlite3.connect('annonces.db')
    cursor = conn.cursor()
    
    # Table des annonces
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT NOT NULL,
            prix REAL NOT NULL,
            ville TEXT NOT NULL,
            categorie TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'active'
        )
    ''')
    
    # Table des photos des annonces
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annonces_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annonce_id INTEGER NOT NULL,
            image_data TEXT NOT NULL,
            position INTEGER NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (annonce_id) REFERENCES annonces (id)
        )
    ''')
    
    # Table des bannières publicitaires
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bannieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            image_data TEXT NOT NULL,
            lien TEXT,
            position TEXT NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT NOT NULL,
            statut TEXT DEFAULT 'active',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des administrateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administrateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Ajouter un admin par défaut
    try:
        cursor.execute('INSERT INTO administrateurs (username, password) VALUES (?, ?)', 
                      ('admin', 'admin123'))
    except:
        pass
    
    conn.commit()
    conn.close()

# Réinitialiser la base de données au démarrage
init_db()

# Fonction pour vérifier si l'admin est connecté
def admin_connecte():
    return request.cookies.get('admin_logged') == 'true'

# Fonction pour obtenir les photos d'une annonce
def get_photos_annonce(annonce_id):
    conn = sqlite3.connect('annonces.db')
    photos = conn.execute('''
        SELECT * FROM annonces_photos 
        WHERE annonce_id = ? 
        ORDER BY position
    ''', (annonce_id,)).fetchall()
    conn.close()
    return photos

# Fonction pour obtenir les bannières actives
def get_bannieres_actives(position):
    conn = sqlite3.connect('annonces.db')
    aujourdhui = datetime.now().strftime('%Y-%m-%d')
    
    bannieres = conn.execute('''
        SELECT * FROM bannieres 
        WHERE position = ? AND statut = 'active'
        AND date_debut <= ? AND date_fin >= ?
        ORDER BY date_creation DESC
    ''', (position, aujourdhui, aujourdhui)).fetchall()
    
    conn.close()
    return bannieres

# Générer le HTML des bannières
def generer_bannieres(position):
    bannieres = get_bannieres_actives(position)
    html = ""
    
    for banniere in bannieres:
        if position == "header":
            html += f'''
            <div class="banner-header text-center mb-3">
                <a href="{banniere[3] or '#'}" target="_blank">
                    <img src="data:image/png;base64,{banniere[2]}" 
                         style="max-height: 80px; width: auto;" 
                         class="img-fluid" 
                         alt="{banniere[1]}">
                </a>
            </div>
            '''
        elif position == "sidebar":
            html += f'''
            <div class="banner-sidebar mb-3 text-center">
                <a href="{banniere[3] or '#'}" target="_blank">
                    <img src="data:image/png;base64,{banniere[2]}" 
                         style="max-width: 100%; height: auto;" 
                         class="img-fluid rounded" 
                         alt="{banniere[1]}">
                </a>
            </div>
            '''
    
    return html

# Pied de page personnalisé
def generer_footer():
    return '''
    <footer class="bg-dark text-white mt-5 py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="fas fa-bolt"></i> Rapido.ci</h5>
                    <p class="mb-0">La plateforme de petites annonces la plus rapide de Côte d'Ivoire</p>
                    <p class="mb-0">Trouvez tout ce dont vous avez besoin en un clin d'œil !</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <h5>📞 Contactez-nous</h5>
                    <p class="mb-1">
                        <i class="fas fa-phone"></i> 
                        <a href="tel:+2250508568560" class="text-white text-decoration-none">
                            (+225) 05 08 56 85 60
                        </a>
                    </p>
                    <p class="mb-1">
                        <i class="fab fa-whatsapp"></i> 
                        <a href="https://wa.me/2250508568560" target="_blank" class="text-white text-decoration-none">
                            WhatsApp
                        </a>
                    </p>
                    <div class="mt-3 pt-2 border-top border-secondary">
                        <p class="mb-0 small">
                            <i class="fas fa-code"></i> 
                            <strong>Site créé par Wakanda X</strong>
                        </p>
                        <p class="mb-0 small text-muted">
                            Développement web sur mesure - Solutions digitales innovantes
                        </p>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12 text-center">
                    <p class="mb-0 small text-muted">
                        &copy; 2024 Rapido.ci - Tous droits réservés | 
                        <span class="text-warning">Vendez et achetez en un instant</span>
                    </p>
                </div>
            </div>
        </div>
    </footer>
    '''

# Page de connexion admin
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('annonces.db')
        admin = conn.execute('SELECT * FROM administrateurs WHERE username = ? AND password = ?', 
                           (username, password)).fetchone()
        conn.close()
        
        if admin:
            response = redirect('/admin-dashboard')
            response.set_cookie('admin_logged', 'true', max_age=3600)  # 1 heure
            return response
        else:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Connexion Admin</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <script>
                    alert("Identifiants incorrects !");
                    setTimeout(function() { window.location.href = "/admin-login"; }, 100);
                </script>
            </head>
            <body></body>
            </html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connexion Admin - Rapido.ci</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
            }
            .login-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="login-card p-5">
                        <h2 class="text-center mb-4">🔐 Connexion Admin</h2>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Nom d'utilisateur</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 btn-lg">Se connecter</button>
                        </form>
                        <div class="mt-3 text-center">
                            <small class="text-muted">Identifiants par défaut: admin / admin123</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# Déconnexion admin
@app.route('/admin-logout')
def admin_logout():
    response = redirect('/')
    response.set_cookie('admin_logged', '', expires=0)
    return response

# Dashboard Administrateur
@app.route('/admin-dashboard')
def admin_dashboard():
    if not admin_connecte():
        return redirect('/admin-login')
    
    conn = sqlite3.connect('annonces.db')
    
    # Statistiques
    total_annonces = conn.execute('SELECT COUNT(*) FROM annonces').fetchone()[0]
    
    # Compter les annonces actives (avec gestion d'erreur si colonne statut n'existe pas)
    try:
        annonces_actives = conn.execute('SELECT COUNT(*) FROM annonces WHERE statut = "active"').fetchone()[0]
    except:
        annonces_actives = total_annonces
    
    total_bannieres = conn.execute('SELECT COUNT(*) FROM bannieres').fetchone()[0]
    
    try:
        bannieres_actives = conn.execute('SELECT COUNT(*) FROM bannieres WHERE statut = "active"').fetchone()[0]
    except:
        bannieres_actives = total_bannieres
    
    # Dernières annonces
    annonces = conn.execute('SELECT * FROM annonces ORDER BY date_creation DESC LIMIT 10').fetchall()
    
    # Bannières
    bannieres = conn.execute('SELECT * FROM bannieres ORDER BY date_creation DESC').fetchall()
    
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Admin - Rapido.ci</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background-color: #f8f9fa; padding: 20px; }}
            .stat-card {{ border-radius: 10px; margin-bottom: 20px; }}
            .admin-nav {{ background: #2c3e50; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg admin-nav mb-4">
            <div class="container-fluid">
                <a class="navbar-brand text-white" href="/admin-dashboard">
                    <i class="fas fa-cog"></i> Dashboard Admin - Rapido.ci
                </a>
                <div>
                    <a href="/" class="btn btn-outline-light btn-sm">👀 Voir le site</a>
                    <a href="/admin-logout" class="btn btn-warning btn-sm">🚪 Déconnexion</a>
                </div>
            </div>
        </nav>

        <div class="container">
            <h1 class="mb-4">📊 Tableau de bord Administrateur</h1>
            
            <!-- Statistiques -->
            <div class="row">
                <div class="col-md-3">
                    <div class="card stat-card bg-primary text-white">
                        <div class="card-body">
                            <h4><i class="fas fa-bolt"></i> {total_annonces}</h4>
                            <p>Total Annonces</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card bg-success text-white">
                        <div class="card-body">
                            <h4><i class="fas fa-check-circle"></i> {annonces_actives}</h4>
                            <p>Annonces Actives</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card bg-info text-white">
                        <div class="card-body">
                            <h4><i class="fas fa-ad"></i> {total_bannieres}</h4>
                            <p>Bannières</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card bg-warning text-white">
                        <div class="card-body">
                            <h4><i class="fas fa-chart-line"></i> {bannieres_actives}</h4>
                            <p>Bannières Actives</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <!-- Gestion des annonces -->
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-danger text-white">
                            <h4 class="mb-0"><i class="fas fa-bolt"></i> Gestion des Annonces</h4>
                        </div>
                        <div class="card-body">
                            {"".join([f'''
                            <div class="border-bottom pb-2 mb-2">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6>{annonce[1]}</h6>
                                        <small class="text-muted">
                                            {annonce[3]:.0f} FCFA - {annonce[4]} - {annonce[5]} - 
                                            <span class="badge bg-success">active</span>
                                        </small>
                                        <br>
                                        <small>📅 {annonce[7][:16]}</small>
                                    </div>
                                    <div>
                                        <a href="/annonce/{annonce[0]}" class="btn btn-sm btn-primary">👁️</a>
                                        <a href="/admin-supprimer-annonce/{annonce[0]}" class="btn btn-sm btn-danger" onclick="return confirm('Supprimer cette annonce?')">🗑️</a>
                                    </div>
                                </div>
                            </div>
                            ''' for annonce in annonces]) if annonces else '<p class="text-muted">Aucune annonce.</p>'}
                        </div>
                    </div>
                </div>

                <!-- Gestion des bannières -->
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h4 class="mb-0"><i class="fas fa-ad"></i> Gestion des Bannières</h4>
                        </div>
                        <div class="card-body">
                            <a href="/admin-ajouter-banniere" class="btn btn-success w-100 mb-3">➕ Ajouter une bannière</a>
                            
                            {"".join([f'''
                            <div class="border-bottom pb-2 mb-2">
                                <small><strong>{banniere[1]}</strong></small><br>
                                <small>Position: {banniere[4]} | Statut: <span class="badge bg-success">active</span></small><br>
                                <div class="btn-group btn-group-sm mt-1">
                                    <a href="/admin-supprimer-banniere/{banniere[0]}" class="btn btn-danger" onclick="return confirm('Supprimer cette bannière?')">🗑️</a>
                                </div>
                            </div>
                            ''' for banniere in bannieres]) if bannieres else '<p class="text-muted">Aucune bannière.</p>'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# Ajouter une bannière
@app.route('/admin-ajouter-banniere', methods=['GET', 'POST'])
def admin_ajouter_banniere():
    if not admin_connecte():
        return redirect('/admin-login')
    
    if request.method == 'POST':
        titre = request.form['titre']
        lien = request.form['lien']
        position = request.form['position']
        date_debut = request.form['date_debut']
        date_fin = request.form['date_fin']
        
        # Gestion de l'image (encodage base64)
        image = request.files['image']
        if image:
            image_data = base64.b64encode(image.read()).decode('utf-8')
        else:
            return "Image requise", 400
        
        conn = sqlite3.connect('annonces.db')
        conn.execute('''
            INSERT INTO bannieres (titre, image_data, lien, position, date_debut, date_fin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (titre, image_data, lien, position, date_debut, date_fin))
        conn.commit()
        conn.close()
        
        return redirect('/admin-dashboard')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ajouter Bannière - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <a href="/admin-dashboard" class="btn btn-secondary mb-3">← Retour</a>
            
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h3>➕ Ajouter une bannière publicitaire</h3>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Titre de la bannière</label>
                            <input type="text" class="form-control" name="titre" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Image de la bannière</label>
                            <input type="file" class="form-control" name="image" accept="image/*" required>
                            <small class="form-text text-muted">Format recommandé: 728x90 (header) ou 300x250 (sidebar)</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Lien de destination (optionnel)</label>
                            <input type="url" class="form-control" name="lien" placeholder="https://...">
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Position</label>
                                <select class="form-select" name="position" required>
                                    <option value="header">En-tête (728x90)</option>
                                    <option value="sidebar">Barre latérale (300x250)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Date de début</label>
                                <input type="date" class="form-control" name="date_debut" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Date de fin</label>
                                <input type="date" class="form-control" name="date_fin" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-success btn-lg">✅ Ajouter la bannière</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# Supprimer une annonce (admin)
@app.route('/admin-supprimer-annonce/<int:annonce_id>')
def admin_supprimer_annonce(annonce_id):
    if not admin_connecte():
        return redirect('/admin-login')
    
    conn = sqlite3.connect('annonces.db')
    
    # Supprimer d'abord les photos associées
    conn.execute('DELETE FROM annonces_photos WHERE annonce_id = ?', (annonce_id,))
    
    # Puis supprimer l'annonce
    conn.execute('DELETE FROM annonces WHERE id = ?', (annonce_id,))
    conn.commit()
    conn.close()
    
    return redirect('/admin-dashboard')

# Supprimer une bannière (admin)
@app.route('/admin-supprimer-banniere/<int:banniere_id>')
def admin_supprimer_banniere(banniere_id):
    if not admin_connecte():
        return redirect('/admin-login')
    
    conn = sqlite3.connect('annonces.db')
    conn.execute('DELETE FROM bannieres WHERE id = ?', (banniere_id,))
    conn.commit()
    conn.close()
    
    return redirect('/admin-dashboard')

# Page d'accueil
@app.route('/')
def index():
    conn = sqlite3.connect('annonces.db')
    
    try:
        annonces = conn.execute('''
            SELECT * FROM annonces 
            WHERE statut = 'active' 
            ORDER BY date_creation DESC 
            LIMIT 20
        ''').fetchall()
    except:
        annonces = conn.execute('''
            SELECT * FROM annonces 
            ORDER BY date_creation DESC 
            LIMIT 20
        ''').fetchall()
    
    conn.close()
    
    banniere_header = generer_bannieres("header")
    banniere_sidebar = generer_bannieres("sidebar")
    footer = generer_footer()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rapido.ci - Petites annonces rapides en Côte d'Ivoire</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ 
                padding: 20px; 
                background-color: #f8f9fa;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            .main-content {{
                flex: 1;
            }}
            .card {{ margin-bottom: 20px; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); }}
            .navbar {{ margin-bottom: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }}
            .banner-header {{ background: white; padding: 10px; border-radius: 10px; }}
            .banner-sidebar {{ background: white; padding: 15px; border-radius: 10px; }}
            .admin-badge {{ position: fixed; top: 10px; right: 10px; z-index: 1000; }}
            .annonce-image {{ height: 200px; object-fit: cover; }}
            .carousel-image {{ height: 400px; object-fit: contain; background: #f8f9fa; }}
            .photo-preview {{ max-height: 100px; margin: 5px; border: 1px solid #ddd; }}
            footer a:hover {{ color: #ffc107 !important; }}
            .rapido-brand {{ font-weight: bold; font-size: 1.5rem; }}
        </style>
    </head>
    <body>
        {'''
        <div class="admin-badge">
            <a href="/admin-dashboard" class="btn btn-warning btn-sm">⚙️ Admin</a>
        </div>
        ''' if admin_connecte() else ''}
        
        <nav class="navbar navbar-dark bg-primary rounded">
            <div class="container-fluid">
                <a class="navbar-brand rapido-brand" href="/">
                    <i class="fas fa-bolt"></i> Rapido.ci
                </a>
                <div>
                    <a href="/ajouter" class="btn btn-light">➕ Déposer une annonce</a>
                    <a href="/rechercher" class="btn btn-outline-light">🔍 Rechercher</a>
                    {"<a href='/admin-logout' class='btn btn-outline-warning'>🚪 Déco Admin</a>" if admin_connecte() else ""}
                </div>
            </div>
        </nav>

        {banniere_header}

        <div class="container main-content">
            <div class="row">
                <div class="col-md-9">
                    <h1 class="mb-4"><i class="fas fa-home text-primary"></i> Dernières annonces rapides</h1>
                    
                    {"".join([f'''
                    <div class="card">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    {get_premiere_photo_html(annonce[0])}
                                </div>
                                <div class="col-md-8">
                                    <h5 class="card-title">{annonce[1]}</h5>
                                    <h6 class="card-subtitle mb-2 text-primary">{annonce[3]:.0f} FCFA</h6>
                                    <p class="card-text">{annonce[2][:100]}...</p>
                                    <div class="d-flex justify-content-between text-muted">
                                        <span><i class="fas fa-map-marker-alt"></i> {annonce[4]}</span>
                                        <span><i class="fas fa-tag"></i> {annonce[5]}</span>
                                        <span><i class="fas fa-calendar"></i> {annonce[7][:10]}</span>
                                    </div>
                                    <a href="/annonce/{annonce[0]}" class="btn btn-primary mt-2">Voir détails</a>
                                    {"<a href='/admin-supprimer-annonce/" + str(annonce[0]) + "' class='btn btn-danger btn-sm mt-2' onclick='return confirm(\\\"Supprimer cette annonce?\\\")'>🗑️</a>" if admin_connecte() else ""}
                                </div>
                            </div>
                        </div>
                    </div>
                    ''' for annonce in annonces]) if annonces else '''
                    <div class="text-center py-5">
                        <h3 class="text-muted"><i class="fas fa-inbox"></i> Aucune annonce pour le moment</h3>
                        <p class="text-muted">Soyez le premier à déposer une annonce sur Rapido.ci !</p>
                        <a href="/ajouter" class="btn btn-primary btn-lg">Déposer une annonce</a>
                    </div>
                    '''}
                </div>
                
                <div class="col-md-3">
                    {banniere_sidebar}
                    
                    <div class="card">
                        <div class="card-body">
                            <h5><i class="fas fa-bolt text-warning"></i> Comment ça marche ?</h5>
                            <p>⚡ Déposez votre annonce en 30 secondes</p>
                            <p>📸 Ajoutez jusqu'à 4 photos</p>
                            <p>💬 Vendez rapidement via WhatsApp</p>
                            <a href="/ajouter" class="btn btn-success w-100">Commencer</a>
                        </div>
                    </div>

                    <!-- Section Contact Rapide -->
                    <div class="card mt-3">
                        <div class="card-body">
                            <h5><i class="fas fa-headset"></i> Support Rapido</h5>
                            <p class="small mb-1">Besoin d'aide ? Contactez le support :</p>
                            <p class="mb-1">
                                <i class="fas fa-phone"></i> 
                                <a href="tel:+2250508568560" class="text-decoration-none">05 08 56 85 60</a>
                            </p>
                            <p class="mb-0">
                                <i class="fab fa-whatsapp"></i> 
                                <a href="https://wa.me/2250508568560" target="_blank" class="text-decoration-none">WhatsApp</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {footer}

        <script>
        function previewImage(input, previewId) {{
            const preview = document.getElementById(previewId);
            const file = input.files[0];
            
            if (file) {{
                const reader = new FileReader();
                reader.onload = function(e) {{
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }}
                reader.readAsDataURL(file);
            }} else {{
                preview.style.display = 'none';
            }}
        }}
        </script>
    </body>
    </html>
    """
    return html

def get_premiere_photo_html(annonce_id):
    photos = get_photos_annonce(annonce_id)
    if photos:
        return f'''
        <img src="data:image/png;base64,{photos[0][2]}" 
             class="card-img-top annonce-image" 
             alt="Photo annonce">
        '''
    else:
        return '''
        <div class="card-img-top annonce-image bg-light d-flex align-items-center justify-content-center">
            <i class="fas fa-image fa-3x text-muted"></i>
        </div>
        '''

# Page pour ajouter une annonce avec photos
@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_annonce():
    if request.method == 'POST':
        titre = request.form['titre']
        description = request.form['description']
        prix = float(request.form['prix'])
        ville = request.form['ville']
        categorie = request.form['categorie']
        whatsapp = request.form['whatsapp']
        
        # Insérer l'annonce
        conn = sqlite3.connect('annonces.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO annonces (titre, description, prix, ville, categorie, whatsapp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (titre, description, prix, ville, categorie, whatsapp))
        annonce_id = cursor.lastrowid
        
        # Gérer les photos
        photos_ajoutees = 0
        for i in range(1, 5):
            photo_field = f'photo_{i}'
            if photo_field in request.files and request.files[photo_field].filename:
                file = request.files[photo_field]
                if file and allowed_file(file.filename):
                    image_data = base64.b64encode(file.read()).decode('utf-8')
                    cursor.execute('''
                        INSERT INTO annonces_photos (annonce_id, image_data, position)
                        VALUES (?, ?, ?)
                    ''', (annonce_id, image_data, i))
                    photos_ajoutees += 1
        
        conn.commit()
        conn.close()
        
        return redirect('/')
    
    footer = generer_footer()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Déposer une annonce - Rapido.ci</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ 
                padding: 20px; 
                background-color: #f8f9fa;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            .main-content {{
                flex: 1;
            }}
            .card {{ max-width: 800px; margin: 0 auto; }}
            .photo-preview {{ max-height: 100px; margin: 5px; border: 1px solid #ddd; display: none; }}
            .photo-upload {{ border: 2px dashed #ccc; padding: 20px; text-align: center; margin-bottom: 10px; }}
            .photo-upload:hover {{ border-color: #007bff; }}
        </style>
    </head>
    <body>
        <div class="container main-content">
            <a href="/" class="btn btn-secondary mb-3">← Retour à l'accueil</a>
            
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h2 class="mb-0"><i class="fas fa-bolt"></i> Déposer une nouvelle annonce rapide</h2>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Titre de l'annonce *</label>
                            <input type="text" class="form-control" name="titre" required minlength="5">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description *</label>
                            <textarea class="form-control" name="description" rows="4" required minlength="10"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Prix (FCFA) *</label>
                                <input type="number" class="form-control" name="prix" step="0.01" min="0" required>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Ville *</label>
                                <select class="form-select" name="ville" required>
                                    <option value="">Choisir une ville</option>
                                    <option value="Abidjan">Abidjan</option>
                                    <option value="Bouaké">Bouaké</option>
                                    <option value="Daloa">Daloa</option>
                                    <option value="Korhogo">Korhogo</option>
                                    <option value="San-Pédro">San-Pédro</option>
                                    <option value="Yamoussoukro">Yamoussoukro</option>
                                    <option value="Autre">Autre</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Catégorie *</label>
                            <select class="form-select" name="categorie" required>
                                <option value="">Choisir une catégorie</option>
                                <option value="Immobilier">🏠 Immobilier</option>
                                <option value="Véhicules">🚗 Véhicules</option>
                                <option value="Électronique">📱 Électronique</option>
                                <option value="Maison & Jardin">🏡 Maison & Jardin</option>
                                <option value="Mode & Beauté">👗 Mode & Beauté</option>
                                <option value="Services">🔧 Services</option>
                                <option value="Emploies">💼 Emploies</option>
                                <option value="Autre">📦 Autre</option>
                            </select>
                        </div>

                        <!-- Section Photos -->
                        <div class="mb-4">
                            <label class="form-label">📸 Photos de l'annonce (jusqu'à 4 photos)</label>
                            <small class="form-text text-muted d-block mb-2">
                                La première photo sera utilisée comme image principale
                            </small>
                            
                            <div class="row">
                                <!-- Photo 1 -->
                                <div class="col-md-6 mb-3">
                                    <div class="photo-upload rounded">
                                        <label class="form-label">Photo principale *</label>
                                        <input type="file" class="form-control" name="photo_1" 
                                               accept="image/*" onchange="previewImage(this, 'preview1')" required>
                                        <img id="preview1" class="photo-preview mt-2">
                                    </div>
                                </div>
                                
                                <!-- Photo 2 -->
                                <div class="col-md-6 mb-3">
                                    <div class="photo-upload rounded">
                                        <label class="form-label">Photo 2 (optionnelle)</label>
                                        <input type="file" class="form-control" name="photo_2" 
                                               accept="image/*" onchange="previewImage(this, 'preview2')">
                                        <img id="preview2" class="photo-preview mt-2">
                                    </div>
                                </div>
                                
                                <!-- Photo 3 -->
                                <div class="col-md-6 mb-3">
                                    <div class="photo-upload rounded">
                                        <label class="form-label">Photo 3 (optionnelle)</label>
                                        <input type="file" class="form-control" name="photo_3" 
                                               accept="image/*" onchange="previewImage(this, 'preview3')">
                                        <img id="preview3" class="photo-preview mt-2">
                                    </div>
                                </div>
                                
                                <!-- Photo 4 -->
                                <div class="col-md-6 mb-3">
                                    <div class="photo-upload rounded">
                                        <label class="form-label">Photo 4 (optionnelle)</label>
                                        <input type="file" class="form-control" name="photo_4" 
                                               accept="image/*" onchange="previewImage(this, 'preview4')">
                                        <img id="preview4" class="photo-preview mt-2">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Numéro WhatsApp *</label>
                            <input type="text" class="form-control" name="whatsapp" required placeholder="07 49 58 12 34">
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-lg w-100">⚡ Publier l'annonce rapide</button>
                    </form>
                </div>
            </div>
        </div>

        {footer}

        <script>
        function previewImage(input, previewId) {{
            const preview = document.getElementById(previewId);
            const file = input.files[0];
            
            if (file) {{
                const reader = new FileReader();
                reader.onload = function(e) {{
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }}
                reader.readAsDataURL(file);
            }} else {{
                preview.style.display = 'none';
            }}
        }}
        </script>
    </body>
    </html>
    '''

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Page de détails d'une annonce avec carousel de photos
@app.route('/annonce/<int:annonce_id>')
def voir_annonce(annonce_id):
    conn = sqlite3.connect('annonces.db')
    annonce = conn.execute('SELECT * FROM annonces WHERE id = ?', (annonce_id,)).fetchone()
    photos = get_photos_annonce(annonce_id)
    conn.close()
    
    if not annonce:
        return "Annonce non trouvée", 404
    
    # Générer le carousel de photos
    carousel_html = ""
    if photos:
        carousel_indicators = ""
        carousel_items = ""
        
        for i, photo in enumerate(photos):
            active = "active" if i == 0 else ""
            carousel_indicators += f'''
            <button type="button" data-bs-target="#photoCarousel" data-bs-slide-to="{i}" 
                    class="{active}" aria-current="true" aria-label="Slide {i+1}"></button>
            '''
            
            carousel_items += f'''
            <div class="carousel-item {active}">
                <img src="data:image/png;base64,{photo[2]}" class="d-block w-100 carousel-image" alt="Photo {i+1}">
            </div>
            '''
        
        carousel_html = f'''
        <div id="photoCarousel" class="carousel slide mb-4" data-bs-ride="carousel">
            <div class="carousel-indicators">
                {carousel_indicators}
            </div>
            <div class="carousel-inner rounded">
                {carousel_items}
            </div>
            <button class="carousel-control-prev" type="button" data-bs-target="#photoCarousel" data-bs-slide="prev">
                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Previous</span>
            </button>
            <button class="carousel-control-next" type="button" data-bs-target="#photoCarousel" data-bs-slide="next">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Next</span>
            </button>
        </div>
        '''
    else:
        carousel_html = '''
        <div class="text-center py-5 bg-light rounded mb-4">
            <i class="fas fa-image fa-5x text-muted mb-3"></i>
            <p class="text-muted">Aucune photo disponible pour cette annonce</p>
        </div>
        '''
    
    footer = generer_footer()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{annonce[1]} - Rapido.ci</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ 
                padding: 20px; 
                background-color: #f8f9fa;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            .main-content {{
                flex: 1;
            }}
            .carousel-image {{ height: 400px; object-fit: contain; background: #f8f9fa; }}
        </style>
    </head>
    <body>
        <div class="container main-content">
            <a href="/" class="btn btn-secondary mb-3">← Retour à l'accueil</a>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body">
                            {carousel_html}
                            
                            <h1 class="card-title">{annonce[1]}</h1>
                            <h2 class="text-primary">{annonce[3]:.0f} FCFA</h2>
                            <p class="fs-5">{annonce[2]}</p>
                            
                            <div class="row text-muted">
                                <div class="col-md-6">
                                    <p><strong>🏙️ Ville:</strong> {annonce[4]}</p>
                                    <p><strong>📁 Catégorie:</strong> {annonce[5]}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>📅 Publiée le:</strong> {annonce[7][:10]}</p>
                                    <p><strong>📸 Photos:</strong> {len(photos)}/4</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h3 class="mb-0">📞 Contacter le vendeur</h3>
                        </div>
                        <div class="card-body text-center">
                            <p class="fs-4">📱 {annonce[6]}</p>
                            <a href="https://wa.me/225{annonce[6]}?text=Bonjour, je suis intéressé par votre annonce : {annonce[1]}" 
                               target="_blank" class="btn btn-success btn-lg w-100">
                                💬 Contacter sur WhatsApp
                            </a>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-body text-center">
                            <a href="/ajouter" class="btn btn-primary w-100 mb-2">➕ Déposer une annonce</a>
                            <a href="/rechercher" class="btn btn-outline-secondary w-100">🔍 Voir d'autres annonces</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {footer}
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

# Rechercher avec la nouvelle catégorie "Emploies"
@app.route('/rechercher')
def rechercher():
    recherche = request.args.get('q', '')
    ville = request.args.get('ville', '')
    categorie = request.args.get('categorie', '')
    
    conn = sqlite3.connect('annonces.db')
    
    query = "SELECT * FROM annonces WHERE 1=1"
    params = []
    
    if recherche:
        query += " AND (titre LIKE ? OR description LIKE ?)"
        params.extend([f'%{recherche}%', f'%{recherche}%'])
    
    if ville:
        query += " AND ville = ?"
        params.append(ville)
    
    if categorie:
        query += " AND categorie = ?"
        params.append(categorie)
    
    query += " ORDER BY date_creation DESC"
    
    annonces = conn.execute(query, params).fetchall()
    conn.close()
    
    footer = generer_footer()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rechercher - Rapido.ci</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ 
                padding: 20px; 
                background-color: #f8f9fa;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            .main-content {{
                flex: 1;
            }}
        </style>
    </head>
    <body>
        <div class="container main-content">
            <a href="/" class="btn btn-secondary mb-3">← Retour à l'accueil</a>
            
            <h1 class="mb-4"><i class="fas fa-search text-primary"></i> Rechercher des annonces</h1>
            
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET">
                        <div class="row g-3">
                            <div class="col-md-4">
                                <input type="text" class="form-control" name="q" value="{recherche}" placeholder="🔎 Que recherchez-vous ?">
                            </div>
                            
                            <div class="col-md-3">
                                <select class="form-select" name="ville">
                                    <option value="">Toutes les villes</option>
                                    <option value="Abidjan" {"selected" if ville == "Abidjan" else ""}>Abidjan</option>
                                    <option value="Bouaké" {"selected" if ville == "Bouaké" else ""}>Bouaké</option>
                                    <option value="Daloa" {"selected" if ville == "Daloa" else ""}>Daloa</option>
                                    <option value="Korhogo" {"selected" if ville == "Korhogo" else ""}>Korhogo</option>
                                </select>
                            </div>
                            
                            <div class="col-md-3">
                                <select class="form-select" name="categorie">
                                    <option value="">Toutes les catégories</option>
                                    <option value="Immobilier" {"selected" if categorie == "Immobilier" else ""}>Immobilier</option>
                                    <option value="Véhicules" {"selected" if categorie == "Véhicules" else ""}>Véhicules</option>
                                    <option value="Électronique" {"selected" if categorie == "Électronique" else ""}>Électronique</option>
                                    <option value="Maison & Jardin" {"selected" if categorie == "Maison & Jardin" else ""}>Maison & Jardin</option>
                                    <option value="Mode & Beauté" {"selected" if categorie == "Mode & Beauté" else ""}>Mode & Beauté</option>
                                    <option value="Services" {"selected" if categorie == "Services" else ""}>Services</option>
                                    <option value="Emploies" {"selected" if categorie == "Emploies" else ""}>Emploies</option>
                                    <option value="Autre" {"selected" if categorie == "Autre" else ""}>Autre</option>
                                </select>
                            </div>
                            
                            <div class="col-md-2">
                                <button type="submit" class="btn btn-primary w-100">Rechercher</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            
            <h3>{len(annonces)} annonce(s) trouvée(s)</h3>
            
            {"".join([f'''
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            {get_premiere_photo_html(annonce[0])}
                        </div>
                        <div class="col-md-8">
                            <h5 class="card-title">{annonce[1]}</h5>
                            <h6 class="card-subtitle mb-2 text-primary">{annonce[3]:.0f} FCFA</h6>
                            <p class="card-text">{annonce[2][:100]}...</p>
                            <div class="d-flex justify-content-between text-muted">
                                <span>🏙️ {annonce[4]}</span>
                                <span>📁 {annonce[5]}</span>
                                <span>📅 {annonce[7][:10]}</span>
                            </div>
                            <a href="/annonce/{annonce[0]}" class="btn btn-outline-primary btn-sm mt-2">Voir détails</a>
                        </div>
                    </div>
                </div>
            </div>
            ''' for annonce in annonces]) if annonces else '''
            <div class="text-center py-4">
                <h4 class="text-muted">Aucune annonce trouvée</h4>
                <p class="text-muted">Essayez de modifier vos critères de recherche.</p>
            </div>
            '''}
        </div>

        {footer}
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)