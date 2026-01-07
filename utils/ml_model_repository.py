from __future__ import annotations

import json
import pickle
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger("ml_model_repository")

METADATA_JSON = "metadata.json"
MODEL_PICKLE = "model.pkl"
GITKEEP = ".gitkeep"

DATA_ML_MODELS_DIR = Path(__file__).parent.parent / "data" / "ml_models"


@dataclass
class ModelMetadata:
    entity_id: str
    entity_type: str
    model_type: str
    cv_score: float | None
    cv_metric: str
    feature_names: list[str]
    feature_importance: dict[str, float] | None
    product_type: str | None
    cv: float | None
    trained_at: str
    parameters: dict | None = None


class MLModelRepository(ABC):
    @abstractmethod
    def save_model(
            self,
            entity_id: str,
            entity_type: str,
            trained_model_info: dict,
            cv_metric: str = "mape",
    ) -> str:
        pass

    @abstractmethod
    def get_model(self, entity_id: str, entity_type: str = "model") -> dict | None:
        pass

    @abstractmethod
    def list_models(
            self,
            entity_type: str | None = None,
            model_type: str | None = None,
            limit: int = 100,
    ) -> list[dict]:
        pass

    @abstractmethod
    def delete_model(self, entity_id: str, entity_type: str = "model") -> bool:
        pass

    @abstractmethod
    def delete_all_models(self) -> int:
        pass

    @abstractmethod
    def get_model_count(self, entity_type: str | None = None) -> int:
        pass


class FileMLModelRepository(MLModelRepository):
    def __init__(self, base_dir: Path = DATA_ML_MODELS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_model_dir(self, entity_id: str, entity_type: str) -> Path:
        safe_id = entity_id.replace("/", "_").replace("\\", "_")
        return self.base_dir / entity_type / safe_id

    def save_model(
            self,
            entity_id: str,
            entity_type: str,
            trained_model_info: dict,
            cv_metric: str = "mape",
    ) -> str:
        model_dir = self._get_model_dir(entity_id, entity_type)
        model_dir.mkdir(parents=True, exist_ok=True)

        model_id = str(uuid.uuid4())

        trained_model = trained_model_info.get("trained_model")
        if trained_model is not None:
            with open(model_dir / MODEL_PICKLE, "wb") as f:
                pickle.dump(trained_model, f)  # type: ignore[arg-type]

        metadata = ModelMetadata(
            entity_id=entity_id,
            entity_type=entity_type,
            model_type=trained_model_info.get("model_type", "unknown"),
            cv_score=trained_model_info.get("cv_score"),
            cv_metric=cv_metric,
            feature_names=trained_model_info.get("feature_names", []),
            feature_importance=trained_model_info.get("feature_importance"),
            product_type=trained_model_info.get("product_type"),
            cv=trained_model_info.get("cv"),
            trained_at=trained_model_info.get("trained_at", datetime.now().isoformat()),
            parameters=trained_model_info.get("parameters"),
        )

        with open(model_dir / METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump(asdict(metadata), f, indent=2, default=str)

        logger.info("Saved ML model for %s/%s: %s", entity_type, entity_id, model_id)
        return model_id

    def get_model(self, entity_id: str, entity_type: str = "model") -> dict | None:
        model_dir = self._get_model_dir(entity_id, entity_type)

        metadata_file = model_dir / METADATA_JSON
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            trained_model = None
            model_file = model_dir / MODEL_PICKLE
            if model_file.exists():
                with open(model_file, "rb") as f:
                    trained_model = pickle.load(f)

            return {
                **metadata,
                "trained_model": trained_model,
                "success": True,
            }

        except Exception as e:
            logger.warning("Error loading model for %s/%s: %s", entity_type, entity_id, e)
            return None

    def _get_type_dirs(self, entity_type: str | None) -> list[Path]:
        if not self.base_dir.exists():
            return []

        if entity_type:
            type_dir = self.base_dir / entity_type
            return [type_dir] if type_dir.exists() else []

        return [d for d in self.base_dir.iterdir() if d.is_dir() and d.name != GITKEEP]

    @staticmethod
    def _load_metadata(model_dir: Path) -> dict | None:
        metadata_file = model_dir / METADATA_JSON
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Error reading metadata from %s: %s", model_dir, e)
            return None

    def _collect_models_from_dir(self, type_dir: Path, model_type: str | None) -> list[dict]:
        models = []
        for model_dir in type_dir.iterdir():
            if not model_dir.is_dir():
                continue
            metadata = self._load_metadata(model_dir)
            if metadata is None:
                continue
            if model_type and metadata.get("model_type") != model_type:
                continue
            models.append(metadata)
        return models

    def list_models(
            self,
            entity_type: str | None = None,
            model_type: str | None = None,
            limit: int = 100,
    ) -> list[dict]:
        models = []
        for type_dir in self._get_type_dirs(entity_type):
            models.extend(self._collect_models_from_dir(type_dir, model_type))

        models.sort(key=lambda x: x.get("trained_at", ""), reverse=True)
        return models[:limit]

    def delete_model(self, entity_id: str, entity_type: str = "model") -> bool:
        model_dir = self._get_model_dir(entity_id, entity_type)

        if not model_dir.exists():
            return False

        try:
            import shutil
            shutil.rmtree(model_dir)
            logger.info("Deleted ML model for %s/%s", entity_type, entity_id)
            return True
        except Exception as e:
            logger.warning("Error deleting model for %s/%s: %s", entity_type, entity_id, e)
            return False

    def delete_all_models(self) -> int:
        count = 0

        if not self.base_dir.exists():
            return count

        for type_dir in self.base_dir.iterdir():
            if not type_dir.is_dir() or type_dir.name == GITKEEP:
                continue

            for model_dir in type_dir.iterdir():
                if model_dir.is_dir():
                    try:
                        import shutil
                        shutil.rmtree(model_dir)
                        count += 1
                    except Exception as e:
                        logger.warning("Error deleting %s: %s", model_dir, e)

        logger.info("Deleted %d ML models", count)
        return count

    def get_model_count(self, entity_type: str | None = None) -> int:
        count = 0
        for type_dir in self._get_type_dirs(entity_type):
            for model_dir in type_dir.iterdir():
                if model_dir.is_dir() and (model_dir / METADATA_JSON).exists():
                    count += 1
        return count


def create_ml_model_repository() -> MLModelRepository:
    from dotenv import load_dotenv
    load_dotenv()

    return FileMLModelRepository()
