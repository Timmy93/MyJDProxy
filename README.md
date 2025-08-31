# MyJDProxy
 A simple REST API server to contact MyJDownloader serevices

## Caratteristiche

- ✅ **Architettura modulare** - Organizzazione pulita del codice con separazione delle responsabilità
- ✅ **API RESTful** - Endpoint chiari e intuitivi
- ✅ **Gestione errori robusta** - Handling completo degli errori con logging
- ✅ **Configurazione esterna** - File TOML per la configurazione
- ✅ **Pronto per produzione** - Server Waitress incluso
- ✅ **Logging avanzato** - Sistema di logging robusto con rotazione
- ✅ **Validazione input** - Controlli di sicurezza su tutti gli input
- ✅ **Health checks** - Monitoraggio dello stato dell'applicazione

## Struttura del Progetto

```
myjdownloader-api/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # Endpoint API Flask
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Gestione configurazione TOML
│   │   └── myjd_client.py     # Client MyJDownloader
│   ├── models/
│   │   ├── __init__.py
│   │   └── download.py        # Modelli dati download
│   └── utils/
│       ├── __init__.py
│       └── exceptions.py      # Eccezioni personalizzate
├── config/
│   └── config.toml           # File di configurazione
├── logs/                     # Directory log (creata automaticamente)
├── requirements.txt          # Dipendenze Python
├── main.py                  # Entry point applicazione
└── README.md
```

## Installazione

1. **Clona il repository**
```bash
git clone <repository-url>
cd myjdownloader-api
```

2. **Crea ambiente virtuale**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows
```

3. **Installa dipendenze**
```bash
pip install -r requirements.txt
```

4. **Configura l'applicazione**
Modifica il file `config/config.toml` con le tue credenziali:

```toml
[MyJD]
username = "your_myjdownloader_email"
password = "your_myjdownloader_password"
appkey = "your_app_key"
deviceid = "your_device_id"

[Downloads]
base_path = "/path/to/downloads"
allowed_categories = ["tv_show", "movie", "other"]
```

## Utilizzo

### Avvio Development Server
```bash
python main.py
# oppure
python main.py --mode development --port 5000
```

### Avvio Production Server
```bash
python main.py --mode production
# oppure
python main.py --mode production --port 8080 --host 0.0.0.0
```

## API Endpoints

### Health Check
```http
GET /api/health
```
Controlla lo stato di connessione con MyJDownloader.

### Connessione
```http
POST /api/connect
```
Stabilisce connessione con MyJDownloader.

```http
POST /api/disconnect  
```
Disconnette da MyJDownloader.

### Download Management

#### Aggiungi Download
```http
POST /api/downloads
Content-Type: application/json

{
  "name": "Nome del pacchetto",
  "links": [
    "http://example.com/file1.zip",
    "http://example.com/file2.zip"
  ],
  "category": "movie",
  "auto_start": true
}
```

#### Lista Download
```http
GET /api/downloads
```
Restituisce tutti i download con stato di avanzamento.

#### Avvia Download
```http
POST /api/downloads/start

# Per avviare download specifici
{
  "package_ids": ["uuid1", "uuid2"]
}

# Per avviare tutti i download
{}
```

#### Pausa Download
```http
POST /api/downloads/pause

# Pausa download specifici o tutti
{
  "package_ids": ["uuid1", "uuid2"]  # opzionale
}
```

### Altri Endpoint

#### LinkGrabber
```http
GET /api/linkgrabber
```
Ottieni pacchetti in LinkGrabber (download in attesa).

#### Configurazione
```http
GET /api/config
```
Visualizza informazioni di configurazione (senza dati sensibili).

## Esempi di Utilizzo

### Python Requests
```python
import requests

# Health check
response = requests.get("http://localhost:5000/api/health")
print(response.json())

# Aggiungi download
download_data = {
    "name": "Serie TV - S01E01",
    "links": ["http://example.com/episode1.mkv"],
    "category": "tv_show",
    "auto_start": True
}

response = requests.post(
    "http://localhost:5000/api/downloads",
    json=download_data
)
print(response.json())

# Lista download
response = requests.get("http://localhost:5000/api/downloads")
downloads = response.json()
for package in downloads['packages']:
    print(f"{package['name']}: {package['progress_percentage']:.1f}%")
```

### cURL
```bash
# Health check
curl http://localhost:5000/api/health

# Aggiungi download
curl -X POST http://localhost:5000/api/downloads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Download",
    "links": ["http://example.com/file.zip"],
    "category": "other"
  }'

# Lista download
curl http://localhost:5000/api/downloads
```

## Configurazione Avanzata

### Logging
I log sono salvati in `logs/myjdownloader_api.log` con rotazione automatica (10MB max, 10 file backup).

### Categorie Download
Le categorie consentite sono configurabili nel file `config.toml`. Ogni categoria crea una sottocartella nel percorso base.

### Sicurezza
- Validazione input su tutti gli endpoint
- Gestione errori robusta
- Non esposizione di credenziali negli endpoint
- Logging sicuro senza informazioni sensibili

## Sviluppo

### Aggiungere Nuovi Endpoint
1. Aggiungi route in `app/api/routes.py`
2. Implementa logica business in `app/core/myjd_client.py`
3. Crea modelli dati in `app/models/` se necessario
4. Aggiungi test e documentazione

### Testing
```bash
# Avvia server in modalità development per testing
python main.py --mode development

# Test health check
curl http://localhost:5000/api/health
```

## Troubleshooting

### Errori Comuni
1. **Connection Error**: Verifica credenziali in `config.toml`
2. **Device Not Found**: Controlla che il `deviceid` sia corretto
3. **Permission Error**: Verifica i permessi sul `base_path`

### Debug
Avvia in modalità development per log dettagliati:
```bash
python main.py --mode development
```

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

## Contributi

I contributi sono benvenuti! Apri una issue o invia una pull request.