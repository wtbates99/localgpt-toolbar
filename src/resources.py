from pathlib import Path
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceManager:
    def __init__(self):
        self.resource_dir = Path(__file__).parent.parent / "resources"
        self.ensure_resources()

    def ensure_resources(self) -> None:
        """Ensure all required resources are available."""
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_icon()

    def _ensure_icon(self) -> None:
        """Ensure the application icon exists."""
        icon_path = self.resource_dir / "icon.png"
        if not icon_path.exists():
            # Create a default icon if none exists
            default_icon = self.resource_dir / "default_icon.png"
            if default_icon.exists():
                shutil.copy(default_icon, icon_path)
            else:
                logger.warning("No default icon found")

    def get_icon_path(self) -> Optional[Path]:
        """Get the path to the application icon."""
        icon_path = self.resource_dir / "icon.png"
        return icon_path if icon_path.exists() else None
