import re
import os
import requests
import sys

def process_md(file_path, api_url, token_id, token_secret, book_id):
    # 1. Définition des dossiers sources
    # On récupère le chemin absolu du dossier contenant le fichier .md
    md_abs_path = os.path.abspath(file_path)
    base_dir = os.path.dirname(md_abs_path)
    fallback_images_dir = "/tmp/bookstack_import_docs/images"
    
    if not os.path.exists(md_abs_path):
        print(f"DEBUG: Fichier MD introuvable : {md_abs_path}", file=sys.stderr)
        return ""

    with open(md_abs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex pour ![alt](chemin)
    img_regex = r'!\[(.*?)\]\((.*?)\)'
    headers = {'Authorization': f'Token {token_id}:{token_secret}'}

    def upload_and_replace(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        
        # Ignorer les URLs distantes
        if img_path.startswith(('http', 'https', 'data:')):
            return match.group(0)

        # 2. Résolution du chemin de l'image
        # Tentative 1 : Chemin relatif au fichier MD (ex: docs/images/image.png)
        full_path = os.path.normpath(os.path.join(base_dir, img_path))
        
        # Tentative 2 : Fallback vers le dossier temporaire si non trouvé
        if not os.path.exists(full_path):
            filename = os.path.basename(img_path)
            full_path = os.path.join(fallback_images_dir, filename)

        print(f"DEBUG: Recherche image -> {full_path}", file=sys.stderr)

        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as img_file:
                    files = {'image': (os.path.basename(full_path), img_file)}
                    data = {
                        'type': 'gallery',
                        'uploaded_to': book_id
                    }
                    
                    response = requests.post(
                        f"{api_url.rstrip('/')}/api/image-gallery",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        new_url = response.json().get('url')
                        print(f"DEBUG: Upload réussi -> {new_url}", file=sys.stderr)
                        return f"![{alt_text}]({new_url})"
                    else:
                        print(f"DEBUG: Erreur API BookStack ({response.status_code}) : {response.text}", file=sys.stderr)
            except Exception as e:
                print(f"DEBUG: Exception lors de l'upload : {str(e)}", file=sys.stderr)
        else:
            print(f"DEBUG: Image non trouvée sur le disque.", file=sys.stderr)
        
        return match.group(0)

    # Remplacement global
    new_content = re.sub(img_regex, upload_and_replace, content)
    return new_content

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("DEBUG: Arguments manquants", file=sys.stderr)
        sys.exit(1)
        
    result = process_md(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    # On écrit le Markdown final sur stdout pour qu'Ansible le récupère dans .stdout
    sys.stdout.write(result)