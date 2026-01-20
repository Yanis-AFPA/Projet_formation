# 3. Provisionnement de l'Infrastructure (Terraform)

## 3.1. Contexte et Objectifs
Dans le cadre de l'industrialisation du déploiement, nous avons opté pour une approche **Infrastructure as Code (IaC)**. 
L'objectif est de remplacer la création manuelle de machines virtuelles par du code déclaratif, garantissant ainsi :

* **La reproductibilité** : L'environnement peut être recréé à l'identique en quelques minutes en cas de désastre.
* **La documentation vivante** : Le code sert de documentation à jour de l'infrastructure réelle.
* **L'agilité** : L'ajout d'une nouvelle machine se fait par une simple ligne de configuration, sans toucher au code logique.

## 3.2. Architecture de Déploiement

Le provisionnement est piloté depuis l'intérieur du réseau sécurisé, respectant le principe de la "Management Station".

* **Machine de contrôle** : VM Admin (`10.212.213.10`) située dans le LAN.
* **Cible** : Cluster Proxmox VE (Nœud `pve3`).
* **Provider** : `dpg/proxmox` (Version 0.93.0).
* **Sécurité** : Authentification via Token API avec séparation des privilèges.

## 3.3. Structure du Projet

Le projet sépare strictement la logique (le code) des données (l'inventaire). Voici l'organisation des fichiers sur la machine d'administration.

| Fichier | Description |
| :--- | :--- |
| `main.tf` | Contient la logique de création des ressources. |
| `variables.tf` | Définit les structures de données attendues . |
| `provider.tf` | Configuration du plugin Proxmox, de l'URL API et des paramètres de sécurité. |
| `terraform.tfvars` | Fichier contenant la définition unique de chaque VM (CPU, RAM, IP, Tags). |

## 3.4. La "Factory" de VMs (Fichier main.tf)

Pour répondre au besoin de généricité, nous n'avons pas codé les VMs une par une. Nous avons créé une boucle dynamique (`for_each`) qui agit comme une usine : elle lit la liste des machines demandées et les fabrique à la chaîne.

Le code ci-dessous montre :
1.  La sélection du nœud cible (`pve3`) et du template (`debian-template`).
2.  L'activation de l'agent QEMU.
3.  La configuration réseau dynamique.

### Configuration Système (Cloud-Init)

Une partie critique du code concerne l'initialisation de l'OS (`Cloud-Init`). C'est ici que nous injectons :
* L'utilisateur de maintenance `admin1`.
* La clé SSH publique (pour qu'Ansible puisse se connecter ensuite).
* L'adressage IP fixe.

## 3.5. L'Inventaire des Machines (Fichier tfvars)

C'est le seul fichier que l'administrateur doit modifier. Il contient la définition des machines sous forme de dictionnaire. On y définit les ressources (CPU/RAM) et les IPs.

```hcl
variable "vms" {
  description = "Map des VMs à déployer"
  type = map(object({
    id          = number
    target_node = string
    template    = string
    cores       = number
    memory      = number
    disk_size   = number
    ip_cidr     = string
    gateway     = string
    tags        = string
  }))
}
```

## 3.6. Exécution et Résultat

Le déploiement a été réalisé via la commande `terraform apply`. Le plan d'exécution a validé la création des ressources sans erreur.

![alt text](images/image.png)

Côté hyperviseur, les machines sont bien apparues et ont démarré automatiquement :

![alt text](<images/Capture d’écran du 2026-01-14 12-57-20.png>)