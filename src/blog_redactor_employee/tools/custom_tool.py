from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import paramiko


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        return "this is an example of a tool output, ignore it and move along."

# 1. On définit le schéma des arguments que l'agent doit fournir
class SFTPUploadToolInput(BaseModel):
    """Input schema pour le SFTP Upload Tool."""
    local_file_path: str = Field(..., description="Le chemin local du fichier HTML généré (ex: 'temp_article.html').")
    remote_file_name: str = Field(..., description="Le nom final du fichier sur le serveur (ex: 'mon-article.html').")

# 2. On crée la classe de l'outil
class SFTPUploadTool(BaseTool):
    name: str = "SFTP Upload Tool"
    description: str = (
        "Utile pour uploader un fichier HTML local directement sur le serveur SFTP du blog. "
        "À utiliser uniquement quand l'article est entièrement rédigé et validé."
    )
    args_schema: Type[BaseModel] = SFTPUploadToolInput

    def _run(self, local_file_path: str, remote_file_name: str) -> str:
        # Récupération des variables d'environnement
        host = os.getenv("SFTP_HOST")
        port = int(os.getenv("SFTP_PORT", 22))
        username = os.getenv("SFTP_USERNAME")
        password = os.getenv("SFTP_PASSWORD")
        remote_directory = os.getenv("SFTP_REMOTE_DIR", "/public/blog")

        if not all([host, username, password]):
            return "Erreur : Les identifiants SFTP ne sont pas configurés dans l'environnement."

        if not os.path.exists(local_file_path):
            return f"Erreur : Le fichier local '{local_file_path}' n'existe pas."

        ssh_client = None
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
            
            sftp = ssh_client.open_sftp()
            
            try:
                sftp.chdir(remote_directory)
            except IOError:
                return f"Erreur : Le répertoire distant '{remote_directory}' est introuvable."

            sftp.put(local_file_path, remote_file_name)
            sftp.close()
            
            return f"Succès : L'article a été uploadé avec succès sous le nom '{remote_file_name}'."

        except Exception as e:
            return f"Échec de l'upload SFTP. Erreur : {str(e)}"
            
        finally:
            if ssh_client:
                ssh_client.close()


class WriteFileInput(BaseModel):
    """Input schema pour le Write File Tool."""
    file_path: str = Field(..., description="Le nom ou le chemin du fichier à créer (ex: 'mon-article.html').")
    content: str = Field(..., description="Le contenu textuel ou HTML complet à écrire dans le fichier.")

class WriteFileTool(BaseTool):
    name: str = "Write File Tool"
    description: str = (
        "Utile pour créer un fichier local sur le disque et y écrire du contenu (HTML ou Markdown). "
        "À utiliser impérativement AVANT d'uploader le fichier via SFTP."
    )
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(self, file_path: str, content: str) -> str:
        try:
            file_path = os.path.basename(file_path)
            
            # Si l'agent envoie du texte brut ou oublie la structure HTML de base,
            # on s'assure qu'il y a au moins le Head avec l'encodage UTF-8 configuré.
            if "<html" not in content.lower():
                html_structure = f"""<!DOCTYPE html>
                    <html lang="fr">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
                        <link rel="stylesheet" href="../styles.css">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                        <title>Article de Blog</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1000px; margin: 40px auto; padding: 0 20px; color: #333; }}
                            h1 {{ color: #111; }}
                            h2 {{ color: #222; margin-top: 30px; }}
                            h3 {{ color: #444; }}
                            p {{ margin-bottom: 20px; text-align: justify; }}
                        </style>
                    </head>
                    <body>
                        <div class='container'>
                        {content}
                        </div>
                    </body>
                    </html>"""
                content = html_structure
            
            # Force l'écriture en UTF-8 pur
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return f"Succès : Le fichier '{file_path}' a été créé localement avec succès en UTF-8."
        except Exception as e:
            return f"Erreur lors de la création du fichier : {str(e)}"