# Documentation Service DNS (Bind9)

Cette documentation détaille la configuration et le fonctionnement du service DNS déployé au sein de l'infrastructure `grp-ay.lab`.

## 📌 Vue d'ensemble

Le service DNS assure la résolution de noms pour le réseau interne. Il est hébergé sur une VM dédiée et utilise **Bind9** comme logiciel serveur.

*   **Logiciel** : Bind9
*   **Zone gérée** : `grp-ay.lab`
*   **Adresse IP** : `10.212.213.21` (Variable `dns_ip`)
*   **Déploiement** : Automatisé via Ansible (Rôle `dns`)

## ⚙️ Configuration Serveur

### Structure Ansible
Le rôle Ansible `dns` (`ansible/roles/dns`) est responsable de l'installation et de la configuration :

| Fichier | Description | Chemin cible sur la VM |
| :--- | :--- | :--- |
| `tasks/main.yml` | Installe Bind9, crée le dossier zones, et déploie les configurations. | - |
| `templates/named.conf.options.j2` | Options globales de Bind9 (forwarders, ACLs). | `/etc/bind/named.conf.options` |
| `templates/named.conf.local.j2` | Déclaration de la zone `grp-ay.lab`. | `/etc/bind/named.conf.local` |
| `templates/db.grp-ay.lab.j2` | Fichier de zone contenant les enregistrements DNS. | `/etc/bind/zones/db.grp-ay.lab` |

### Zone `grp-ay.lab`

Le fichier de zone définit les correspondances nom ↔ IP. Voici la logique des enregistrements définis dans le template `db.grp-ay.lab.j2` :

#### Enregistrements Spécifiques (A Records)
| Domaine | Cible | IP (Par défaut) | Description |
| :--- | :--- | :--- | :--- |
| `ns1.grp-ay.lab` | Serveur DNS | `10.212.213.21` | Le serveur de noms lui-même. |
| `srv-gitlab-ay.grp-ay.lab` | VM GitLab | `10.212.213.30` | Accès direct à la VM (utile pour SSH). |
| `srv-harbor.grp-ay.lab` | VM Harbor | `10.212.213.40` | Accès direct à la VM. |

#### Le Wildcard (*) et le Proxy
Une entrée "Wildcard" est configurée pour diriger tout sous-domaine non spécifié vers le **Reverse Proxy**.

*   `*.grp-ay.lab` ➡️ `10.212.213.20` (IP du Proxy Nginx)

Cela signifie que n'importe quel service exposé via Nginx sera automatiquement résolu vers le proxy sans avoir besoin de modifier le DNS à chaque fois.
*   Exemple : `gitlab.grp-ay.lab` -> `10.212.213.20`
*   Exemple : `registry.grp-ay.lab` -> `10.212.213.20`

## 💻 Configuration Client (`client_setup`)

Afin que toutes les machines de l'infrastructure utilisent ce serveur DNS, configuration est automatisée par le rôle **`client_setup`** (appliqué via le groupe `common`).

Ce rôle modifie le fichier `/etc/resolv.conf` sur **tous les nœuds** (sauf le serveur DNS lui-même) pour :
1.  Définir `nameserver` sur l'IP du serveur DNS (`10.212.213.21`).
2.  Ajouter le domaine de recherche `search grp-ay.lab`.

**Extrait de la tâche Ansible (`roles/client_setup/tasks/main.yml`) :**
```yaml
- name: Configurer le DNS client (resolv.conf)
  ansible.builtin.copy:
    dest: /etc/resolv.conf
    content: |
      search grp-ay.lab
      nameserver {{ dns_ip }}
```

Cette configuration garantit que :
*   Toutes les machines peuvent résoudre les noms internes (`ping gitlab`).
*   Les machines utilisent le DNS interne comme source de vérité.
