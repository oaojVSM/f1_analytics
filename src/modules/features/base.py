from abc import ABC, abstractmethod
import pandas as pd

# ABC = Abstract Base Class (Classe Base Abstrata)
# Significa: "Eu sou só um modelo, não sirvo pra ser usada sozinha."
class BaseFeatureExtractor(ABC):
    
    def __init__(self, raw_data: dict):
        # Pode ser modificado criando um init na classe filho e chamando essa inicialização via super()
        self.raw_data = raw_data

    @abstractmethod
    def execute(self) -> pd.DataFrame:
        # Padronização do método de execução. Aqui eu falo que qualquer classe filho necessitará desse método.
        pass