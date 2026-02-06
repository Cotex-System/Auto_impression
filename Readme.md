# 🖨️ API Auto-Impression Zebra TLP 2844

## Description

Ce projet contient une **API FastAPI** pour l’impression automatique d’étiquettes sur une **imprimante thermique Zebra TLP 2844**.

- **Transporteurs** :
  - **TNT** → fichiers `.epl` → impression directe en RAW
  - **Chronopost** → fichiers `.pdf` → impression via driver Windows  
- **Authentification** : token Bearer (`Authorization: Bearer <TOKEN>`)

Cette API peut être exécutée en **mode développement** (`main.py`) ou en **service Windows** (`print_service.py`) pour démarrage automatique.

---

## Prérequis

- Windows 10 ou 11
- Python 3.10 ou supérieur
- Anaconda ou venv recommandé
- Imprimante Zebra TLP 2844 installée sur Windows (pour tests réels)

---

## ⚙️ Installation de Python (Pour PC sans Python)

### ✅ Option 1 : Anaconda (recommandé - plus simple)

1. **Télécharger Anaconda** depuis https://www.anaconda.com/download
   - Choisir la version **Windows 64-bit** (ou 32-bit selon votre système)

2. **Installer Anaconda** :
   - Double-cliquer sur le fichier téléchargé (`Anaconda3-*.exe`)
   - Cocher : ✅ **"Add Anaconda3 to my PATH"** (IMPORTANT !)
   - Cliquer "Install"
   - Attendre la fin de l'installation

3. **Vérifier l'installation** :
   - Ouvrir **PowerShell** ou **Command Prompt** (chercher "PowerShell" dans le menu Démarrage)
   - Taper : `python --version`
   - Devrait afficher `Python 3.x.x` (ex: `Python 3.11.5`)

### ✅ Option 2 : Python pur (Python.org)

1. **Télécharger Python** depuis https://www.python.org/downloads/
   - Cliquer sur **"Download Python 3.x"**
   - Choisir **Windows 64-bit** (ou 32-bit selon votre système)

2. **Installer Python** :
   - Double-cliquer sur l'exécutable
   - ⚠️ **COCHER : "Add Python 3.x to PATH"** (TRÈS IMPORTANT !)
   - Cliquer "Install Now"
   - Attendre la fin

3. **Vérifier l'installation** :
   - Ouvrir **PowerShell** ou **Command Prompt**
   - Taper : `python --version`
   - Devrait afficher `Python 3.x.x` (ex: `Python 3.11.5`)

---

## Dépendances Python

Installez les packages nécessaires :

```bash
pip install fastapi uvicorn pywin32 pypdf2
```

- fastapi → framework API

- uvicorn → serveur ASGI pour FastAPI

- pywin32 → accès aux fonctions Windows (impression, service)

- pypdf2 → optionnel, manipulation PDF si nécessaire

## Variable d'environnement
définir le token pour sécuriser l'API
```bash
setx PRINT_API_TOKEN "TON_TOKEN_SUPER_SECRET"
```
ou le définir pour la machine (si lancement automatique) :
```bash
[Environment]::SetEnvironmentVariable("PRINT_API_TOKEN", "MON_TOKEN_SECRET", "Machine")
```
⚠️ Fermez puis rouvrez la console pour que la variable soit disponible dans Python.

Dans le script:
```python
API_TOKEN = os.environ.get("PRINT_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("PRINT_API_TOKEN non défini")
```

---

## 🚀 Lancer l'API en mode développement

1. Activer l'environnement Python :

```bash
conda activate branch-env_py313  # ou ton venv
```

2. Installer les dépendances :

```bash
pip install -r requirements.txt  # ou pip install fastapi uvicorn pywin32 pypdf2
```

3. Lancer le serveur FastAPI :

```bash
python main.py
```

ou avec Uvicorn (rechargement en dev) :

```bash
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```


- **Swagger UI** : http://127.0.0.1:5000/docs
- **Endpoint principal** : `POST /print`

### FormData
- `carrier`: `tnt` ou `chronopost` ou `poste`
- `file`: fichier à imprimer

### Headers
- `Authorization: Bearer <TOKEN>`

---

## 🛠️ Exécuter l'API comme service Windows

1. Installer la dépendance Windows :

```bash
pip install pywin32
```
2. mettre la variable d'env

```bash
[Environment]::SetEnvironmentVariable("PRINT_API_TOKEN", "MON_TOKEN_SECRET", "Machine")
```

3. Installer le service (ouvrir Anaconda/PowerShell en administrateur) :

```powershell
python print_service.py install
python print_service.py start
```

- Arrêter le service :

```powershell
python print_service.py stop
```

- Supprimer le service :

```powershell
python print_service.py remove
```

> Le service démarre automatiquement au démarrage de Windows. Les logs s’affichent dans la console ou peuvent être redirigés vers un fichier.

---

## ✅ Test de l'API (Postman)

- Importer la collection : `Zebra_Print_API.postman_collection.json`
- Variables à définir :
  - `base_url` = `http://127.0.0.1:5000`
  - `token` = `TON_TOKEN_SUPER_SECRET`
- Cas de test :
  - TNT : upload `.epl`
  - Chronopost : upload `.pdf`
  - Sécurité : envoyer sans token → doit renvoyer **401 Unauthorized**

---

## 🐞 Débogage courant

| Problème | Solution |
|---|---|
| `RuntimeError: PRINT_API_TOKEN non défini` | Fermer et rouvrir la console après `setx` ou définir la variable dans l'environnement du service |
| `FileNotFoundError: AcroRd32.exe` | Utiliser `win32api.ShellExecute` ou adapter le chemin vers votre lecteur PDF |
| `pywintypes.error: (31) ShellExecute` | Vérifier que l'imprimante est installée et accessible sur le poste de dev |
| Postman ne se connecte pas | Vérifier que l'API écoute bien sur `127.0.0.1:5000` et les règles du firewall Windows |

---

## 💡 Bonnes pratiques

- Utiliser `127.0.0.1` en développement pour restreindre l'accès
- Pour la production : configurer un firewall, utiliser HTTPS et des tokens forts
- Configurer correctement l'imprimante Zebra : taille d'étiquette adaptée, **203 DPI**, orientation correcte

---

## ✉️ Support

Pour toute question ou bug, ouvrir une issue dans le dépôt avec :
- description du problème
- log d'erreur
- commande utilisée
- capture d'écran si nécessaire

Merci d'utiliser l'API Auto-Impression Zebra ! :wave: