# Primeiro arquivo a ser executado do projeto, é de onde vamos obter nossos dados

import kagglehub
import shutil
from pathlib import Path


def download_f1_dataset(dataset_id="rohanrao/formula-1-world-championship-1950-2020"):
    """
    Faz o download do dataset da F1 usando kagglehub e salva em data/raw.
    """
    print(f"Baixando dataset '{dataset_id}' do Kaggle...")
    dataset_path = kagglehub.dataset_download(dataset_id)

    print(f"Dataset baixado para: {dataset_path}")

    # Define o destino final na pasta data/raw
    raw_data_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # Copia todos os arquivos para data/raw
    for item in Path(dataset_path).iterdir():
        dest = raw_data_dir / item.name
        if item.is_file():
            shutil.copy(item, dest)
        elif item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)

    print(f"Arquivos salvos em: {raw_data_dir}")
    return raw_data_dir


if __name__ == "__main__":
    download_f1_dataset()
