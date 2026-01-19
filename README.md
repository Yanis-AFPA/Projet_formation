#  Infrastructure & Deployment

Ce dépôt contient le code **Infrastructure as Code (IaC)** réalisé dans le cadre d'un TP . Il permet le déploiement automatisé d'une infrastructure virtualisée sur un cluster Proxmox, destinée à héberger une usine logicielle (GitLab, Harbor) et des applications.

## 👥 Membres du groupe

*   **Ali ASSADRI**
*   **Yanis HAMIDI**

## 🎯 Objectifs

L'objectif est de mettre en œuvre une infrastructure complète et sécurisée permettant :
1.  Le provisionnement automatisé de Machines Virtuelles (Terraform).
2.  La configuration et le déploiement des services (Ansible).
3.  La gestion centralisée des accès et de la sécurité (Reverse Proxy, CA, DNS).

## 🏗 Architecture & Réseau

*   **Réseau LAN** : `10.212.213.0/24`
*   **Nom de domaine** : `grp-ay.lab`
*   **Bridge Proxmox** : `vmbr_ay`

### Plan d'Adressage

| Hostname | IP | Rôle | Description |
| :--- | :--- | :--- | :--- |
| **Proxy** | `10.212.213.20` | Reverse Proxy / CA | Point d'entrée unique (Nginx), Terminaison SSL, Autorité de Certification. |
| **DNS** | `10.212.213.21` | DNS (Bind9) | Résolution de noms interne pour le domaine `.lab`. |
| **GitLab** | `10.212.213.30` | SCM / CI/CD | Forge logicielle et pipelines d'intégration continue. |
| **Harbor** | `10.212.213.40` | Registre Docker | Stockage sécurisé des images conteneurs. |

## 🛠 Déploiement (Infrastructure as Code)

Le projet respecte les principes IaC : tout est versionné et automatisé.

### 1. Provisionnement (Terraform)

Terraform est utilisé pour décrire l'état souhaité de l'infrastructure (VMs, Ressources).
Il déploie les machines virtuelles sur le cluster Proxmox en se basant sur des templates.

**Fichiers clés :**
*   `terraform/main.tf` : Définition des ressources VM.
*   `terraform/variables.tf` : Variables (IPs, Ressources).
*   `terraform/terraform.tfvars` : Secrets (Token API, Clés SSH) - *Non versionné*.

**Commande :**
```bash
cd terraform
terraform init
terraform apply
```

### 2. Configuration (Ansible)

Ansible configure les machines une fois provisionnées. L'organisation est modulaire (Rôles).

**Rôles principaux :**
*   **common / client_setup** : Configuration de base, ajout de la CA racine pour la confiance SSL.
*   **nginx** : Configuration du Reverse Proxy pour exposer les services via FQDN (ex: `gitlab.grp-ay.lab`).
*   **ca** : Gestion de l'Autorité de Certification (PKI) et distribution des certificats.
*   **dns** : Configuration du serveur Bind9 pour la zone `grp-ay.lab`.
*   **docker** : Installation du runtime Docker sur les nœuds applicatifs.

**Commande :**
```bash
cd ansible
ansible-playbook -i inventory/hosts.ini playbook.yml
```

## 🔐 Sécurité & Accès

*   **SSL/TLS** : Tous les services sont exposés en HTTPS via le Reverse Proxy. Une CA interne (gérée par Ansible) signe les certificats.
*   **DNS** : Le serveur DNS interne permet la résolution des noms de domaine au sein du LAN, facilitant la communication entre services sans passer par les IPs.
*   **Isolation** : Les services ne sont pas exposés directement, tout passe par le Reverse Proxy.

---
*Projet réalisé dans le cadre de la formation CDA.*
