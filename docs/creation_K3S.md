# 📖 Documentation : Infrastructure K3s & Déploiement GitOps

Cette documentation retrace la mise en place d'un cluster Kubernetes léger (**K3s**) piloté par **Ansible**, sécurisé par une **PKI interne**, et automatisé via **ArgoCD**.

---

## 🏗️ 1. Architecture du Cluster
L'infrastructure repose sur une séparation stricte des rôles pour garantir la persistance et la scalabilité :

* **1 Master (Control Plane)** : Gère l'API Kubernetes, l'ordonnancement et l'état du cluster.
* **2 Workers (Nœuds d'exécution)** : Hébergent les pods de l'application (Calendrier).
* **Stockage Externe (NFS)** : Serveur dédié (`10.212.213.70`) pour la persistance des données.
* **Base de Données (PostgreSQL)** : VM externe dédiée (`10.212.213.71`) pour la sécurité des données applicatives.

---

## 🤖 2. Automatisation Ansible
Le déploiement du cluster est entièrement automatisé via des rôles Ansible, permettant une reproductibilité totale.

### Pré-requis système (Leçon apprise)
Pour que le cluster puisse monter les volumes réseaux NFS, chaque nœud (Master et Workers) doit posséder les outils de communication RPC.

- name: Installation des dépendances de stockage
  apt:
    name: 
      - nfs-common
      - open-iscsi
    state: present

### Flux d'installation
1. **Master** : Installation via le script officiel avec l'option `K3S_KUBECONFIG_MODE="644"`.
2. **Token** : Récupération automatique du jeton de sécurité dans `/var/lib/rancher/k3s/server/node-token`.
3. **Workers** : Jointure automatique au cluster en utilisant l'IP du Master et le Token récupéré.

---


## 🐙 3. Déploiement GitOps avec ArgoCD
L'application n'est pas déployée manuellement, mais synchronisée depuis un dépôt **GitLab**.

### Les 3 Fichiers Clés du Déploiement
1. **Stockage (`1-nfs-storage.yaml`)** : Définit le `PersistentVolume` (PV) pointant vers le serveur NFS et le `PersistentVolumeClaim` (PVC) réclamé par l'app.
2. **Application (`2-deployment.yaml`)** : 
    * Image tirée depuis le registre privé **Harbor**.
    * Variables d'environnement Django (ex: `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`).
    * Montage du volume NFS dans le conteneur.
3. **Réseau (`3-ingress-service.yaml`)** : 
    * **Service** : Pont interne redirigeant le port 80 vers le port **8000** (Django).
    * **Ingress** : Définit la route DNS `calendrier.k3s.grp-ay.lab` pour Traefik.

---

## 🛠️ 4. Guide de Résolution des Erreurs

| Erreur rencontrée | Cause identifiée | Solution appliquée |
| :--- | :--- | :--- |
| **Exit Status 32** | Client NFS manquant sur les nœuds K3s. | Ajout de `nfs-common` dans le playbook Ansible. |
| **No such file or directory** | Dossier absent sur le serveur NFS. | Création de `/srv/nfs/k3s_data/calendrier` + `exportfs -arv`. |
| **CrashLoopBackOff** | `DATABASE_URL` manquante ou mal formatée. | Injection de la variable complète dans le Deployment. |
| **Bad Gateway (502)** | Erreur de port entre le Service (80) et le Pod (8000). | Correction du `targetPort: 8000` dans le Service. |
| **Bad Request (400)** | Sécurité Django (Hosts non autorisés). | Ajout de `DJANGO_ALLOWED_HOSTS` avec le domaine final. |

---

## 📈 5. État Actuel
* **Cluster K3s** : Opérationnel (Master + 2 Workers).
* **Base de Données** : Connectée et migrations effectuées.
* **Stockage NFS** : Connecté et persistant.
* **Accès Web** : Fonctionnel sur `http://calendrier.k3s.grp-ay.lab`.
