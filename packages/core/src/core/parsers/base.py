"""Base parser protocol and registry for tax document artifacts."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Protocol, Union
import logging

logger = logging.getLogger(__name__)


class ArtifactParser(Protocol):
    """Protocol for parsing tax document artifacts.
    
    All parsers must implement this interface to be registered
    and used by the parser registry.
    """
    
    @abstractmethod
    def supports(self, kind: str, path: Path) -> bool:
        """Check if this parser supports the given artifact kind and file.
        
        Args:
            kind: The artifact kind (e.g., 'prefill', 'ais', 'form16b')
            path: Path to the file to be parsed
            
        Returns:
            True if this parser can handle the artifact, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse the artifact file and return structured data.
        
        Args:
            path: Path to the file to be parsed
            
        Returns:
            Dictionary containing the parsed data with standardized structure
            
        Raises:
            ValueError: If the file cannot be parsed
            FileNotFoundError: If the file doesn't exist
        """
        pass
    
    @property
    @abstractmethod
    def supported_kinds(self) -> List[str]:
        """List of artifact kinds this parser supports."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this parser supports (e.g., ['.json', '.pdf'])."""
        pass


class BaseParser(ABC):
    """Base implementation for artifact parsers.
    
    Provides common functionality and validation for all parsers.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    def supports(self, kind: str, path: Path) -> bool:
        """Default implementation checks kind and file extension."""
        if kind not in self.supported_kinds:
            return False
        
        if not path.exists():
            return False
        
        file_extension = path.suffix.lower()
        return file_extension in self.supported_extensions
    
    def _validate_file(self, path: Path) -> None:
        """Validate that the file exists and is readable."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        try:
            # Try to read the file to ensure it's accessible
            with open(path, 'rb') as f:
                f.read(1)
        except PermissionError:
            raise ValueError(f"File is not readable: {path}")
        except Exception as e:
            raise ValueError(f"Error accessing file {path}: {e}")
    
    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get basic file information."""
        stat = path.stat()
        return {
            "file_name": path.name,
            "file_size": stat.st_size,
            "file_extension": path.suffix.lower(),
            "last_modified": stat.st_mtime,
        }
    
    @abstractmethod
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse the artifact file and return structured data."""
        pass
    
    @property
    @abstractmethod
    def supported_kinds(self) -> List[str]:
        """List of artifact kinds this parser supports."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions this parser supports."""
        pass


class ParserRegistry:
    """Registry for managing artifact parsers.
    
    Provides a centralized way to register parsers and route
    parsing requests to the appropriate parser.
    """
    
    def __init__(self):
        self._parsers: List[ArtifactParser] = []
    
    def register(self, parser: ArtifactParser) -> None:
        """Register a parser with the registry.
        
        Args:
            parser: Parser instance implementing ArtifactParser protocol
        """
        if not hasattr(parser, 'supports') or not hasattr(parser, 'parse'):
            raise ValueError("Parser must implement ArtifactParser protocol")
        
        self._parsers.append(parser)
        logger.info(f"Registered parser: {getattr(parser, 'name', type(parser).__name__)}")
    
    def get_parser(self, kind: str, path: Union[str, Path]) -> Optional[ArtifactParser]:
        """Get the appropriate parser for the given artifact kind and file.
        
        Args:
            kind: The artifact kind (e.g., 'prefill', 'ais', 'form16b')
            path: Path to the file to be parsed
            
        Returns:
            Parser instance if found, None otherwise
        """
        path_obj = Path(path) if isinstance(path, str) else path
        
        for parser in self._parsers:
            if parser.supports(kind, path_obj):
                return parser
        
        return None
    
    def parse(self, kind: str, path: Union[str, Path]) -> Dict[str, Any]:
        """Parse an artifact using the appropriate parser.
        
        Args:
            kind: The artifact kind (e.g., 'prefill', 'ais', 'form16b')
            path: Path to the file to be parsed
            
        Returns:
            Dictionary containing the parsed data
            
        Raises:
            ValueError: If no suitable parser is found or parsing fails
        """
        parser = self.get_parser(kind, path)
        if not parser:
            raise ValueError(f"No parser found for kind '{kind}' and file '{path}'")
        
        try:
            result = parser.parse(Path(path))
            
            # Add metadata about the parsing
            result["_parser_info"] = {
                "parser_name": getattr(parser, 'name', type(parser).__name__),
                "artifact_kind": kind,
                "parsed_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing {kind} file {path}: {e}")
            raise ValueError(f"Failed to parse {kind} file: {e}")
    
    def list_supported_kinds(self) -> List[str]:
        """Get list of all supported artifact kinds."""
        kinds = set()
        for parser in self._parsers:
            kinds.update(parser.supported_kinds)
        return sorted(list(kinds))
    
    def list_parsers(self) -> List[Dict[str, Any]]:
        """Get information about all registered parsers."""
        return [
            {
                "name": getattr(parser, 'name', type(parser).__name__),
                "supported_kinds": parser.supported_kinds,
                "supported_extensions": parser.supported_extensions,
            }
            for parser in self._parsers
        ]