# Documentation Ansible

## 1. Qu'est-ce qu'Ansible ?

**Ansible** est un outil open-source d'automatisation informatique. Il permet de configurer des systèmes, de déployer des logiciels et d'orchestrer des tâches informatiques avancées de manière simple et prévisible.

Ses principaux avantages sont :
- **Sans agent (Agentless)** : Il n'y a pas besoin d'installer un logiciel client sur les machines cibles. Ansible utilise simplement une connexion SSH (sous Linux) pour s'y connecter et exécuter ses tâches.
- **Idempotent** : Ansible décrit l'état désiré d'un système. L'exécution répétée d'une même tâche ne modifiera pas le système si cet état désiré est déjà atteint.
- **Simple (YAML)** : Les fichiers de configuration (Playbooks) sont écrits en YAML, un format particulièrement lisible pour les administrateurs et DevOps.

## 2. Qu'est-ce qu'un Playbook ?

Un **Playbook** est le fichier principal d'Ansible, écrit en YAML. C'est en quelque sorte le "scénario" qui liste les actions (les tâches) qu'Ansible doit effectuer sur un ensemble de machines préalablement définies dans un inventaire.

Un Playbook est composé d'un ou plusieurs **Plays**. Chaque Play relie un groupe d'hôtes (machines) ou de groupes d'hôtes à certaines tâches ou **rôles**.

### Exemple dans notre projet : Le fichier `playbook.yml` principal

Dans notre projet, le fichier `ansible/playbook.yml` est le chef d'orchestre global. Il définit le déploiement de l'infrastructure de A à Z par étapes séquentielles.

Voici un extrait direct de notre code qui montre de manière claire le fonctionnement d'un "Play" pour le déploiement de Harbor :

```yaml
# ==========================================
# ÉTAPE 5 : Le Registre Harbor
# ==========================================
- name: Déploiement Harbor
  hosts: harbor
  become: true
  tags: harbor
  roles:
    - harbor
```
*Dans cet extrait : Ansible se connecte à la ou les machines appartenant au groupe `harbor` (défini dans l'inventaire `hosts.ini`), élève ses privilèges avec les droits administrateur (`become: true`), et applique à ces machines toutes les logiques contenues dans le rôle `harbor`.*

## 3. Les Rôles Ansible

Les **Rôles (Roles)** permettent de structurer, factoriser et modulariser les Playbooks en arborescences prévisibles. Au lieu d'avoir un fichier `playbook.yml` unique et tentaculaire de plusieurs milliers de lignes, on découpe chaque brique ou technologie logicielle dans son propre rôle.

Un rôle regroupe de manière standardisée par dossiers :
- `tasks/` : Les tâches et manipulations à exécuter.
- `templates/` : Des fichiers de configuration sources utilisant des variables dynamiques (souvent des `.j2`, via le moteur Jinja2).
- `vars/` ou `defaults/` : Des définitions de variables statiques et par défaut.

### L'approche modulaire dans notre projet

Nous avons créé un rôle complet pour chaque composant majeur du projet, dans le dossier racine `ansible/roles/` (ex: `dns`, `nginx`, `docker`, `gitlab`, `harbor`, `k3s`, `database`, etc.).

**Illustration détaillée - Les tâches du Rôle `harbor`**

L'extrait suivant provient de notre fichier `ansible/roles/harbor/tasks/main.yml`. Il illustre parfaitement la manière séquentielle et intelligente (idempotence via conditions `when` ou `creates`) de fonctionner d'Ansible dans un rôle :

```yaml
# 1. VÉRIFICATION : On vérifie si l'installation de Harbor est déjà présente dans /opt
- name: Vérifier si Harbor est déjà installé
  stat:
    path: /opt/harbor
  register: harbor_check

# 2. TÉLÉCHARGEMENT : Conditionné par "when"
- name: Télécharger l'installateur Harbor (Offline)
  get_url:
    url: https://github.com/goharbor/harbor/releases/download/v2.14.2/harbor-offline-installer-v2.14.2.tgz
    dest: /tmp/harbor-offline-installer.tgz
    mode: '0644'
  # On ne télécharge l'archive massive QUE si harbor_check (au-dessus) a renvoyé que le dossier n'existe pas.
  when: not harbor_check.stat.exists

# 3. EXTRACTION
- name: Extraire l'archive
  unarchive:
    src: /tmp/harbor-offline-installer.tgz
    dest: /opt/
    remote_src: yes
    creates: /opt/harbor  # Ne s'exécutera pas si le dossier /opt/harbor existe déjà
```

### Le réutilisabilité des Rôles : le cas de Docker

Un atout majeur est la **réutilisabilité de code**. Nous avons besoin de Docker sur plusieurs VM (GitLab, Harbor, Serveur Proxy, Serveur BDD). 

Afin de ne pas reproduire l'instruction d'installation de Docker dans les rôles de chaque composant, nous avons déporté sa logique d'installation dans le rôle indépendant `docker` (`ansible/roles/docker`). Il nous suffit juste de l'appeler au sein de notre Playbook en amont d'un rôle nécessitant le service.

Voici comment on exploite cela pour la base de données :

```yaml
# ==========================================
# ÉTAPE 9 : La Base de Données Externe
# ==========================================
- name: Déploiement de la Base de Données
  hosts: database
  become: true
  tags: database
  roles:
    - docker   # <-- Indispensable : On réutilise le rôle pour installer Docker d'abord
    - database # <-- Ensuite, on laisse le rôle exécuter la partie Base de Données logicielle pure
```

---

## Résumé du Workflow global Ansible dans ce projet

L'articulation entre ces concepts est limpide :
1. **L'Inventaire** (`ansible/inventory/hosts.ini`) : Cartographie les adresses IP et regroupe nos serveurs par profils (ex: `[gitlab]`, `[harbor]`, `[dns]`).
2. **Le Playbook Principal** (`ansible/playbook.yml`) : Agit comme l'ordonnanceur chronologique du déploiement général.
3. **Les Rôles** (`ansible/roles/`) : Contenants isolés apportant le contexte et la mécanique technique d'installation (les "recettes") pour chaque brique de notre Système d'Information, appelés au bon moment par le Playbook.
