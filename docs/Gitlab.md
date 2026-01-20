# Documentation GitLab CE & CI/CD

## 1. Vue d'ensemble

Cette documentation décrit le déploiement de **GitLab Community Edition (CE)** au sein de l'infrastructure **grp-ay.lab**. Il sert de gestionnaire de code source (SCM) et de plateforme d'intégration continue (CI/CD).

### Architecture
* **Proxy Nginx (.20)** : Gère le terminaison SSL et redirige le trafic HTTP/SSH vers GitLab.
* **Serveur GitLab (.30)** : Héberge l'application monolithique GitLab (Rails, Gitaly, Redis, PostgreSQL) via Docker.
* **GitLab Runner** : Agent qui exécute les pipelines CI/CD (Build, Test, Push).

### Flux de communication
1.  **Web (HTTPS)** : `User -> Nginx (.20) -> GitLab (.30:80)`
2.  **Git (SSH)** : `User -> Nginx (.20) -> GitLab (.30:2222)`
3.  **CI/CD** : `Runner -> GitLab API`

---

## 2. Inventaire Ansible (`inventory/hosts.ini`)

GitLab est installé sur une machine dédiée pour supporter sa charge mémoire importante.

```ini
[proxy]
10.212.213.20

[gitlab]
10.212.213.30

[runners]
# Peut être sur la même machine ou une autre
10.212.213.30 
```

---

## 3. Configuration Technique

### A. Le Conteneur GitLab (`roles/gitlab`)
GitLab est déployé via Docker avec les persistance des données.

* **Image :** `gitlab/gitlab-ce:latest`
* **Ports exposés :**
    * `80` : Interface Web (interne).
    * `443` : HTTPS (souvent géré par Nginx en amont, mais configuré dans le conteneur).
    * `2222` : SSH (mappé vers le port 22 du conteneur pour éviter le conflit avec le SSH de la VM).
* **Volumes :**
    * `/srv/gitlab/config`
    * `/srv/gitlab/logs`
    * `/srv/gitlab/data`

**Configuration Ansible (Extrait) :**
```yaml
env:
  GITLAB_OMNIBUS_CONFIG: |
    external_url '[https://gitlab.grp-ay.lab](https://gitlab.grp-ay.lab)'
    gitlab_rails['gitlab_shell_ssh_port'] = 2222
    nginx['listen_port'] = 80
    nginx['listen_https'] = false
    # Désactivation de l'empaquetage Let's Encrypt (géré par le Proxy externe)
    letsencrypt['enable'] = false
```

### B. Le Proxy Nginx (`roles/nginx`)
Le proxy gère les certificats et la redirection.

**Fichier :** `roles/nginx/templates/gitlab.conf.j2`

```nginx
upstream gitlab_backend {
    server 10.212.213.30:80;
}

server {
    listen 443 ssl;
    server_name gitlab.grp-ay.lab;
    
    # Augmentation de la taille max pour les gros "git push"
    client_max_body_size 250m;

    location / {
        proxy_pass http://gitlab_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 4. Accès et Utilisation

### Interface Web
* **URL :** [https://gitlab.grp-ay.lab](https://gitlab.grp-ay.lab)
* **Compte Admin par défaut :**
    * User : `root`
    * Password : (récupérable via commande).

### Clonage des dépôts
Puisque le port SSH est déporté, les commandes de clone ressemblent à ceci :

* **HTTPS :** `git clone https://gitlab.grp-ay.lab/groupe/projet.git`
* **SSH :** `git clone ssh://git@gitlab.grp-ay.lab:2222/groupe/projet.git`



---

## 5. Intégration Continue (GitLab Runner)

Pour que les pipelines `.gitlab-ci.yml` fonctionnent, un Runner est enregistré.

### Installation
Le Runner est un conteneur Docker séparé qui a accès au socket Docker de l'hôte (`/var/run/docker.sock`) pour lancer des conteneurs "frères" (Docker-outside-of-Docker) lors des builds.

**Configuration `config.toml` du Runner :**
* **Executor :** `docker`
* **Image par défaut :** `docker:latest`
* **Volumes :** `/var/run/docker.sock:/var/run/docker.sock`

### Commandes utiles (Sur la VM Runner)
```bash
# Lister les runners
sudo docker exec -it gitlab-runner gitlab-runner list

# Vérifier le statut
sudo docker exec -it gitlab-runner gitlab-runner verify
```

---

## 6. Maintenance & Dépannage

### Récupérer le mot de passe root initial
Si vous avez perdu le mot de passe défini lors de l'installation :
```bash
# Sur la VM GitLab (.30)
sudo docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password
```
*(Note : Ce fichier disparait 24h après la première installation).*
