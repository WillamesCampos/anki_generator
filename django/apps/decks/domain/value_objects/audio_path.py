"""
Objeto de Valor AudioPath - Representa o caminho para um arquivo de áudio

Características:
- Imutável
- Validado (deve ser um caminho válido)
- Suporta diferentes formatos de áudio
- Pode ser None (opcional)
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass(frozen=True)
class AudioPath:
    """
    Objeto de valor que representa o caminho para um arquivo de áudio.
    
    Características:
    - Imutável (frozen=True)
    - Validado na criação
    - Suporta diferentes formatos
    """
    
    path: str
    
    # Formatos de áudio suportados
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.ogg', '.m4a'}
    
    def __post_init__(self):
        """
        Valida o caminho do áudio após a criação.
        """
        if not self.path or not self.path.strip():
            raise ValueError("Audio path cannot be empty")
        
        # Normaliza o caminho
        normalized_path = self.path.strip()
        
        # Converte para Path para validação
        path_obj = Path(normalized_path)
        
        # Verifica se tem extensão
        if not path_obj.suffix:
            raise ValueError("Audio path must have a file extension")
        
        # Verifica se a extensão é suportada
        if path_obj.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Audio format {path_obj.suffix} is not supported. Supported formats: {self.SUPPORTED_FORMATS}")
        
        # Define o caminho normalizado
        object.__setattr__(self, 'path', str(path_obj))
    
    @property
    def filename(self) -> str:
        """
        Retorna apenas o nome do arquivo.
        """
        return Path(self.path).name
    
    @property
    def directory(self) -> str:
        """
        Retorna o diretório do arquivo.
        """
        return str(Path(self.path).parent)
    
    @property
    def extension(self) -> str:
        """
        Retorna a extensão do arquivo.
        """
        return Path(self.path).suffix.lower()
    
    @property
    def stem(self) -> str:
        """
        Retorna o nome do arquivo sem a extensão.
        """
        return Path(self.path).stem
    
    @property
    def exists(self) -> bool:
        """
        Verifica se o arquivo existe no sistema de arquivos.
        """
        return Path(self.path).exists()
    
    @property
    def size_bytes(self) -> Optional[int]:
        """
        Retorna o tamanho do arquivo em bytes, se existir.
        """
        if self.exists:
            return Path(self.path).stat().st_size
        return None
    
    def is_mp3(self) -> bool:
        """
        Verifica se o arquivo é MP3.
        """
        return self.extension == '.mp3'
    
    def is_wav(self) -> bool:
        """
        Verifica se o arquivo é WAV.
        """
        return self.extension == '.wav'
    
    def is_ogg(self) -> bool:
        """
        Verifica se o arquivo é OGG.
        """
        return self.extension == '.ogg'
    
    def is_m4a(self) -> bool:
        """
        Verifica se o arquivo é M4A.
        """
        return self.extension == '.m4a'
    
    def to_anki_format(self) -> str:
        """
        Converte o caminho para o formato usado pelo Anki.
        
        O Anki espera o caminho no formato: [sound:filename.ext]
        """
        return f"[sound:{self.filename}]"
    
    def to_dict(self) -> dict:
        """
        Converte para dicionário para serialização.
        """
        return {
            "path": self.path,
            "filename": self.filename,
            "directory": self.directory,
            "extension": self.extension,
            "stem": self.stem,
            "exists": self.exists,
            "size_bytes": self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AudioPath':
        """
        Cria um AudioPath a partir de um dicionário.
        """
        return cls(path=data["path"])
    
    @classmethod
    def create_from_filename(cls, filename: str, directory: str = "") -> 'AudioPath':
        """
        Cria um AudioPath a partir de um nome de arquivo e diretório.
        
        Args:
            filename: Nome do arquivo (com extensão)
            directory: Diretório (opcional)
            
        Returns:
            AudioPath criado
        """
        if directory:
            full_path = os.path.join(directory, filename)
        else:
            full_path = filename
        
        return cls(path=full_path)
    
    def __str__(self) -> str:
        return self.path
    
    def __repr__(self) -> str:
        return f"AudioPath('{self.path}')"
    
    def __eq__(self, other) -> bool:
        """
        Comparação baseada no caminho normalizado.
        """
        if not isinstance(other, AudioPath):
            return False
        return self.path == other.path
    
    def __hash__(self) -> int:
        """
        Hash baseado no caminho.
        """
        return hash(self.path)
