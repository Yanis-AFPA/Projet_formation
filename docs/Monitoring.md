# Documentation de la Stack Monitoring (Prometheus, Grafana, Alertmanager)

## 1. Vue d'ensemble de l'architecture

Cette stack permet de surveiller l'état de santé (CPU, RAM, Disque, Up/Down) de toutes les machines virtuelles du laboratoire **grp-ay.lab**.

### Répartition des rôles
* **Proxy (.20)** : Héberge Nginx. Il reçoit les connexions HTTPS des utilisateurs et les transfère à la VM Monitoring.
* **Monitoring (.50)** : Héberge le "cerveau" (Prometheus, Grafana, Alertmanager) dans des conteneurs Docker.
* **Toutes les VMs** : Hébergent "Node Exporter" (l'agent qui envoie les statistiques au serveur).

### Flux des données
1.  **Node Exporter** : Agent installé sur **toutes** les VMs. Il expose les métriques système sur le port `9100`.
2.  **Prometheus** : Serveur central (Time Series Database) situé sur la VM **.50**. Il "scrape" (récupère) les données de tous les agents toutes les 15 secondes.
3.  **Alertmanager** : Situé sur la VM **.50**, il reçoit les alertes de Prometheus (ex: "Instance Down") et gère les notifications.
4.  **Grafana** : Interface visuelle (VM **.50**) pour afficher les graphiques.
5.  **Nginx** : Reverse Proxy (VM **.20**) qui redirige le trafic vers la VM Monitoring.

---

## 2. Inventaire Ansible (`inventory/hosts.ini`)

L'architecture distingue le Proxy (point d'entrée) du Monitoring (traitement).

```ini
# Machine dédiée au monitoring
[monitoring]
10.212.213.50

[all_vms:children]
proxy
gitlab
harbor
bookstack
monitoring
```

---

## 3. Configuration des Composants

### A. Node Exporter (Agent)
* **Rôle :** `roles/node-exporter`
* **Cible :** `[all]` (Toutes les VMs).
* **Mode réseau :** `host` (Obligatoire pour voir le CPU/RAM de l'hôte).

### B. Prometheus (Serveur)
* **Rôle :** `roles/monitoring`
* **Localisation :** VM `.50`.
* **Fichier :** `roles/monitoring/templates/prometheus.yml.j2`
* **Configuration critique :** Le `job_name` doit être **`node`**.

```yaml
scrape_configs:
  - job_name: 'node'  # <--- INDISPENSABLE pour les dashboards Grafana
    static_configs:
      - targets:
        {% for host in groups['all'] %}
        - '{{ hostvars[host]["ansible_host"] }}:9100'
        {% endfor %}
```

### C. Nginx (Reverse Proxy)
* **Rôle :** `roles/nginx`
* **Localisation :** VM `.20`.
* **Fichier :** `roles/nginx/templates/monitoring.conf.j2`
* **Configuration Upstream :** Pointe vers l'IP de la VM Monitoring (`.50`).

```nginx
upstream grafana_backend {
    server 10.212.213.50:3000;
}
upstream prometheus_backend {
    server 10.212.213.50:9090;
}
upstream alertmanager_backend {
    server 10.212.213.50:9093;
}
```

---

## 4. Accès et Utilisation

### URLs
* **Grafana :** `https://grafana.grp-ay.lab`
* **Prometheus :** `https://prometheus.grp-ay.lab`
* **Alertmanager :** `https://alertmanager.grp-ay.lab`


---

## 5. Configuration Post-Installation (Grafana)

À faire manuellement après le déploiement Ansible :

1.  **Connexion :** User `admin` / Password `admin`.
2.  **Ajout Data Sources :**
    * Aller dans **Connections > Data Sources**.
    * **Prometheus :** URL = `http://prometheus:9090` (Nom interne Docker sur la .50).
    * **Alertmanager :** URL = `http://alertmanager:9093`.
3.  **Import Dashboard :**
    * Aller dans **Dashboards > Import**.
    * ID : **1860** (Node Exporter Full).
    * Choisir la source Prometheus.

---

## 6. Dépannage (Troubleshooting)

| Erreur | Cause Probable | Solution |
| :--- | :--- | :--- |
| **Grafana "No Data"** | Le Dashboard cherche le job "node" mais Prometheus a un autre nom. | Modifier `prometheus.yml.j2`, mettre `job_name: 'node'`, relancer Ansible. |
