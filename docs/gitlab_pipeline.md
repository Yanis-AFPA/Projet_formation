# 🛡️ Documentation Technique : Pipeline CI/CD DevSecOps

Ce document détaille l'architecture, les choix techniques et la configuration du pipeline d'intégration continue (**CI/CD**) pour l'application Python Flask.

Il met en avant la démarche **DevSecOps** (sécurité intégrée) et les optimisations de performance (**DRY**, Caching).

---

## 📋 1. Vue d'ensemble des Stages

Le pipeline est séquentiel. Chaque étape valide des critères précis avant de passer à la suivante.

| Stage | Job | Outil | Rôle & Objectif |
| :--- | :--- | :--- | :--- |
| **Pre-Check** | `check-harbor` | Docker | **Smoke Test** : Vérifie la connectivité au registre Harbor. |
| **Lint** | `lint-ruff` | **Ruff** | **Qualité** : Analyse statique ultra-rapide du code. |
| **Test** | `unit-tests` | **Pytest** | **Fonctionnel** : Tests unitaires anti-régression. |
| **Security** | `sec-bandit` | **Bandit** | **SAST** : Analyse de sécurité du code Python. |
| | `sec-trivy-fs` | **Trivy FS** | **Config** : Audit des fichiers et de l'OS. |
| **Build** | `build-push` | **Kaniko** | **Build** : Construction d'image sécurisée (Daemonless). |
| **Post-Scan** | `final-scan` | **Trivy** | **Audit Final** : Recherche de CVEs sur l'image livrée. |

---

## 🚀 2. Optimisations & Implémentation Technique

Cette section détaille les techniques avancées utilisées et montre le code associé.

### A. Principe DRY (Don't Repeat Yourself) via Templates
Pour éviter la duplication de code et faciliter la maintenance, nous utilisons un **modèle caché** (`.python-base`). Tous les jobs Python (`lint`, `test`, `security`) héritent de cette configuration commune via le mot-clé `extends`.

* **Gain :** Maintenance facilitée (une modification du `before_script` s'applique partout).
* **Technique :** Utilisation du mot-clé `extends`.

**Extrait du `.gitlab-ci.yml` :**
```yaml
# Définition du Template
.python-base:
  image: harbor.grp-ay.lab/dockerhub-proxy/library/python:3.10-slim
  before_script:
    - pip install virtualenv
    - virtualenv venv
    - source venv/bin/activate
    - pip install -r requirements.txt

# Exemple d'utilisation (Héritage)
unit-tests:
  extends: .python-base  # <-- Récupère toute la config ci-dessus
  stage: test
  script:
    - pip install pytest
    - pytest -v
```

### B. Gestion du Cache (Performance)
Pour accélérer le pipeline, les bibliothèques Python (`pip`) sont mises en cache entre les jobs. Cela évite de télécharger les mêmes paquets depuis Internet à chaque étape (gain de temps réseau et CPU).

**Extrait du `.gitlab-ci.yml` :**
```yaml
variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/
```

### C. Build "Daemonless" avec Kaniko
Nous n'utilisons pas l'approche classique "Docker-in-Docker" (DinD) qui nécessite le mode `privileged` (faille de sécurité potentielle).
* **Solution :** Utilisation de **Kaniko**.
* **Avantage :** Le build se fait en espace utilisateur (userspace), sans accès root au démon Docker de l'hôte.
* **SSL :** Injection automatique du certificat CA via les volumes du Runner, garantissant une chaîne de confiance complète.

**Extrait du `.gitlab-ci.yml` :**
```yaml
build-push:
  stage: build
  image: 
    name: martizih/kaniko:v1.26.4-debug
    entrypoint: [""]
  script:
    - echo "🏗️ Config Auth Harbor..."
    - mkdir -p /kaniko/.docker
    # Génération dynamique du fichier d'authentification
    - echo "{\"auths\":{\"$HARBOR_URL\":{\"auth\":\"$(printf "%s:%s" "${HARBOR_USER}" "${HARBOR_PASS}" | base64 | tr -d '\n')\"}}}" > /kaniko/.docker/config.json
    
    - echo "🚀 Construction et Push..."
    # Kaniko utilise le certificat monté dans /kaniko/ssl/certs/harbor-ca.crt
    - /kaniko/executor --context "${CI_PROJECT_DIR}" --dockerfile "${CI_PROJECT_DIR}/Dockerfile" --destination "${IMAGE_TAG}"
```

### D. Gestion des Faux Positifs (Security Tuning)
Les outils de sécurité sont configurés finement pour éviter le bruit inutile :
* **Bandit :** Exclusion explicite du dossier `./venv` (code tiers) et `./test_app.py` (code de test).
* **Dépendances :** Utilisation de versions souples (`>=`) dans `requirements.txt` pour permettre les correctifs de sécurité mineurs automatiques.



**Extrait du `.gitlab-ci.yml` :**
```yaml
sec-bandit-sast:
  extends: .python-base
  stage: security
  allow_failure: true
  script:
    - pip install bandit
    - echo "🕵️ Analyse SAST (Bandit)..."
    # L'option -x permet d'exclure les dossiers/fichiers 
    - bandit -r . -x "./venv,./test_app.py" -f json -o bandit-report.json
  artifacts:
    paths: [bandit-report.json]
    when: always
```


### E. Durcissement  du Dockerfile
L'image finale est optimisée pour la production pour réduire la surface d'attaque :
1.  **OS Récent :** Debian 12 (Bookworm).
2.  **Nettoyage :** Pas de compilateur (`gcc`) installé.
3.  **Moindre Privilège :** L'application tourne avec un utilisateur dédié (`appuser`) et non en `root`.

**Extrait du `Dockerfile` :**
```dockerfile
FROM python:3.10-slim-bookworm

WORKDIR /app

# Installation propre sans cache apt/pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# CRITIQUE : Création d'un utilisateur non-root pour l'exécution
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### F. Stratégie de Proxy Cache (Indépendance & Résilience)
Pour garantir la fiabilité des builds, nous ne dépendons pas directement de Docker Hub (Internet). Nous utilisons **Harbor en mode Proxy Cache**.
Cela permet de contourner les limitations de taux (Rate Limiting) et d'assurer que les images de base restent disponibles même sans Internet.

**Mise en œuvre :**
Toutes les images utilisées dans le pipeline (Python, Trivy, Gitleaks) sont préfixées par l'URL du projet proxy Harbor.

**Comparaison :**
```yaml
# ❌ AVANT : Dépendance directe à Docker Hub (Risque de quota/coupure)
image: python:3.10-slim

# ✅ APRÈS : Utilisation du Proxy Cache
image: harbor.grp-ay.lab/dhi-proxy/library/python:3.10-slim
```

---

## 📥 3. Artefacts & Livrables

Le pipeline génère automatiquement les rapports d'audit suivants, disponibles au téléchargement dans GitLab :

* 📄 **`bandit-report.json`** : Rapport complet des failles potentielles dans le code source Python.
* 📄 **`trivy-report.json`** : Liste des vulnérabilités critiques (CVE) détectées dans l'image Docker finale.