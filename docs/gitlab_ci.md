# Documentation CI/CD : Pipeline Docker (GitLab vers Harbor)

## 1. Vue d'ensemble

L'objectif de ce pipeline est d'automatiser la création et le stockage des conteneurs Docker.
Le Runner GitLab utilise le moteur Docker de la machine hôte (via le socket `/var/run/docker.sock`) pour construire l'image et l'envoyer vers Harbor.

---

## 2. Prérequis sur Harbor

1.  **Projet :** Un projet nommé `demo` a été créé.
2.  **Compte Robot :** Un compte robot a été généré pour l'authentification CI/CD.

> **📸 SCREENSHOT ICI :** Capture d'écran Harbor montrant le projet "demo" et l'onglet "Robot Accounts".

---

## 3. Configuration des Variables (GitLab)

Dans **Settings > CI/CD > Variables**, nous avons défini :

| Clé (Key) | Valeur (Exemple) | Note |
| :--- | :--- | :--- |
| `HARBOR_URL` | `https://harbor.grp-ay.lab` | L'URL complète avec le protocole. |
| `HARBOR_USER` | `robot$gitlab-ci` | Nom du compte robot. |
| `HARBOR_PASS` | `e2d...` (Secret) | Mot de passe masqué. |

> **📸 SCREENSHOT ICI :** Capture de la page des variables GitLab CI/CD.

---

## 4. Le Pipeline (`.gitlab-ci.yml`)

Ce fichier contourne le problème du format d'URL (l'erreur `invalid reference format`) en redéfinissant le domaine sans `https://` localement.

**Points clés :**
* **Pas de `dind` :** On utilise le socket Docker monté par le Runner.
* **Nettoyage URL :** La variable `HARBOR_URL` sert au Login, mais pour le `build -t`, nous utilisons une variable locale `HARBOR_DOMAIN` propre.

```yaml
stages:
  - build-and-push

docker-build:
  image: docker:latest
  stage: build-and-push
  
  variables:
    DOCKER_API_VERSION: "1.41"
    # 👇 Correction critique : On définit le domaine PUR (sans https://)
    # car "docker build -t" ne supporte pas le protocole dans le nom.
    HARBOR_DOMAIN: "harbor.grp-ay.lab"
  
  before_script:
    # Authentification auprès du registre
    - echo "$HARBOR_PASS" | docker login $HARBOR_DOMAIN -u "$HARBOR_USER" --password-stdin
  
  script:
    # Construction de l'image avec le nom de domaine propre
    - docker build -t $HARBOR_DOMAIN/demo/test-image:simple .
    
    # Envoi vers Harbor
    - docker push $HARBOR_DOMAIN/demo/test-image:simple
```

---

## 5. Exécution et Validation

### Côté GitLab
Le job doit afficher **"Job Succeeded"**.
Dans les logs, on vérifie :
1.  `Login Succeeded`
2.  Le téléchargement des layers.
3.  Le message final de réussite.

> **📸 SCREENSHOT ICI :** Capture d'écran du Job GitLab avec la coche verte et le log "Login Succeeded".

### Côté Harbor
Dans le projet `demo`, le dépôt `test-image` doit apparaître avec le tag `simple`.

> **📸 SCREENSHOT ICI :** Capture d'écran de l'interface Harbor montrant l'image reçue.

---

## 6. Problème résolu (Troubleshooting)

### Erreur : `invalid reference format`
* **Symptôme :** Le pipeline échouait lors de la commande `docker build`.
* **Cause :** Nous utilisions `$HARBOR_URL` (qui contient `https://`) pour nommer l'image. Docker interdit le protocole dans le nom du tag.
* **Solution :** Création de la variable locale `HARBOR_DOMAIN: "harbor.grp-ay.lab"` dans le YAML pour taguer l'image correctement, tout en gardant `HARBOR_URL` pour d'autres usages si besoin.