"""
User Project Loader для OMSpy
Завантажує конфігурації користувачів та валідує їх
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from .json_schema_validator.technology import validate_technology
from .json_schema_validator.scenario import validate_scenario
from .json_schema_validator.profile import validate_optimization_profile

logger = logging.getLogger(__name__)


class UserProject:
    """Клас для представлення проекту користувача"""

    def __init__(self, project_path: Union[str, Path]):
        self.project_path = Path(project_path)
        self.technologies: Dict[str, Any] = {}
        self.scenario: Dict[str, Any] = {}
        self.profile: Dict[str, Any] = {}
        self.data_tables: Dict[str, pd.DataFrame] = {}
        self._is_loaded = False
        self._is_validated = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def is_validated(self) -> bool:
        return self._is_validated

    def load(self) -> 'UserProject':
        """Завантажує проект з файлової системи"""
        logger.info(f"Loading project from: {self.project_path}")

        if not self.project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {self.project_path}")

        # Завантаження JSON конфігурацій
        self._load_configurations()

        # Завантаження CSV даних
        self._load_data_tables()

        self._is_loaded = True
        logger.info("Project loaded successfully")
        return self

    def _load_configurations(self):
        """Завантажує JSON конфігурації"""
        config_files = {
            'instances.json': 'technologies',
            'base.json': 'scenario',
            'optimization_profile.json': 'profile'
        }

        for filename, attr_name in config_files.items():
            file_path = self.project_path / filename
            if file_path.exists():
                try:
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                    setattr(self, attr_name, data)
                    logger.debug(f"Loaded {filename}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {filename}: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
                    raise
            else:
                logger.warning(f"Configuration file not found: {filename}")

    def _load_data_tables(self):
        """Завантажує CSV файли з data_tables/"""
        data_dir = self.project_path / 'data_tables'
        if not data_dir.exists():
            logger.warning(f"Data tables directory not found: {data_dir}")
            return

        for csv_file in data_dir.glob('*.csv'):
            try:
                df = pd.read_csv(csv_file)
                table_name = csv_file.stem
                self.data_tables[table_name] = df
                logger.debug(f"Loaded data table '{table_name}': {len(df)} rows")
            except Exception as e:
                logger.error(f"Failed to load CSV file {csv_file.name}: {e}")
                continue

    def validate(self, strict: bool = True) -> 'UserProject':
        """Валідує проект використовуючи існуючі валідатори"""
        logger.info("Starting project validation...")
        errors = []

        try:
            # Валідація технологій
            if self.technologies:
                tech_errors = self._validate_technologies(strict=strict)
                errors.extend(tech_errors)

            # Валідація сценарію
            if self.scenario:
                try:
                    validate_scenario(self.scenario)
                    logger.debug("Scenario validation passed")
                except Exception as e:
                    error_msg = f"Scenario validation failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if strict:
                        raise

            # Валідація профілю оптимізації
            if self.profile:
                try:
                    validate_optimization_profile(self.profile)
                    logger.debug("Optimization profile validation passed")
                except Exception as e:
                    error_msg = f"Optimization profile validation failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if strict:
                        raise

            # Перехресна валідація
            cross_errors = self._cross_validate()
            errors.extend(cross_errors)

            if errors and strict:
                raise ValueError(f"Validation failed with {len(errors)} errors")

            self._is_validated = True
            logger.info(f"Project validation completed with {len(errors)} errors")

            if errors:
                logger.warning("Validation errors found:")
                for error in errors:
                    logger.warning(f"  - {error}")

            return self

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    def _validate_technologies(self, strict: bool = True) -> List[str]:
        """Валідує всі технології використовуючи існуючі валідатори"""
        errors = []

        if isinstance(self.technologies, dict):
            for tech_id, tech_config in self.technologies.items():
                try:
                    tech_type = self._determine_technology_type(tech_config)
                    validate_technology(tech_config, tech_type)
                    logger.debug(f"Technology '{tech_id}' ({tech_type}) validation passed")
                except (ValueError, KeyError) as e:
                    error_msg = f"Technology '{tech_id}' validation failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if strict:
                        break
                except Exception as e:
                    error_msg = f"Technology '{tech_id}' unexpected error: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if strict:
                        break

        return errors

    @staticmethod
    def _determine_technology_type(tech_config: Dict[str, Any]) -> str:
        """Отримує тип технології з обов'язкового поля 'type'"""
        tech_type = tech_config.get('type')
        if not tech_type:
            raise ValueError(f"Missing required 'type' field in technology: {tech_config.get('id', 'unknown')}")

        if tech_type not in ['pv', 'bess', 'grid']:
            raise ValueError(f"Invalid technology type '{tech_type}'. Must be one of: pv, bess, grid")

        return tech_type

    def _cross_validate(self) -> List[str]:
        """Перехресна валідація між компонентами"""
        errors = []

        # Перевірка, що технології з сценарію існують
        if self.scenario and self.technologies:
            scenario_techs = self.scenario.get('technologies', [])
            available_techs = set(self.technologies.keys())

            for tech_id in scenario_techs:
                if tech_id not in available_techs:
                    errors.append(f"Scenario references non-existent technology: {tech_id}")

        # Перевірка посилань на CSV файли
        self._validate_data_references(errors)

        return errors

    def _validate_data_references(self, errors: List[str]):
        """Перевіряє, що всі посилання на CSV файли існують"""
        # Перевірка посилань у технологіях
        for tech_id, tech_config in self.technologies.items():
            for field in ['energy_profile', 'tariff_import_profile', 'tariff_export_profile']:
                if field in tech_config:
                    file_ref = tech_config[field]
                    filename = Path(file_ref).stem
                    if filename not in self.data_tables:
                        errors.append(f"Technology '{tech_id}': Referenced file '{filename}' not found")

        # Перевірка посилань у сценарії
        if self.scenario and 'data_files' in self.scenario:
            data_files = self.scenario['data_files']

            # Перевірка load_profile
            if 'load_profile' in data_files:
                filename = Path(data_files['load_profile']).stem
                if filename not in self.data_tables:
                    errors.append(f"Scenario: Load profile '{filename}' not found")

    def get_technology_by_id(self, tech_id: str) -> Optional[Dict[str, Any]]:
        """Отримує технологію за ID"""
        return self.technologies.get(tech_id)

    def get_data_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """Отримує таблицю даних за назвою"""
        return self.data_tables.get(table_name)

    def summary(self) -> Dict[str, Any]:
        """Повертає резюме проекту"""
        tech_types = []
        if isinstance(self.technologies, dict):
            for tech_config in self.technologies.values():
                try:
                    tech_type = self._determine_technology_type(tech_config)
                    tech_types.append(tech_type)
                except (ValueError, KeyError):
                    tech_types.append('unknown')

        return {
            'project_path': str(self.project_path),
            'is_loaded': self.is_loaded,
            'is_validated': self.is_validated,
            'technologies_count': len(self.technologies),
            'technology_types': list(set(tech_types)),
            'has_scenario': bool(self.scenario),
            'has_profile': bool(self.profile),
            'data_tables_count': len(self.data_tables),
            'data_tables': list(self.data_tables.keys())
        }


def load_user_project(project_path: Union[str, Path], validate: bool = True, strict: bool = True) -> UserProject:
    """
    Завантажує проект користувача

    Args:
        project_path: Шлях до директорії проекту
        validate: Чи валідувати проект після завантаження
        strict: Чи зупинятися на першій помилці валідації

    Returns:
        UserProject: Завантажений (та опціонально валідований) проект
    """
    project = UserProject(project_path)
    project.load()

    if validate:
        project.validate(strict=strict)

    return project