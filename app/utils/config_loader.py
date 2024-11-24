import yaml
from pathlib import Path

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        # Spécifiez le chemin depuis la racine du projet
        config_path = Path(__file__).parent.parent.parent / "config/config.yaml"

        # Vérifiez l'existence du fichier et chargez-le
        if not config_path.is_file():
            print(f"Chemin du fichier de configuration : {config_path.resolve()}")
            print("Fichier de configuration non trouvé.")
            self.data = {}
            return

        try:
            with open(config_path, "r") as file:
                self.data = yaml.safe_load(file)
                print("Configuration chargée:", self.data)
        except yaml.YAMLError:
            print("Erreur de lecture du fichier YAML.")
            self.data = {}

# Créez une instance accessible en tant que `config_instance`
config_instance = Config()
