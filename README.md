OMSpy/              # корінь репозиторію
│
├── src/                     # ⬅️ єдиний Python-search-path
│   └── omspy/          # «справжній» пакет
│       ├── __init__.py
│       │
│       ├── json_schemas/         # JSON-схеми «Єдине джерело правди» для валідації JSON
│       │   ├── technology/ # Підсхеми обладнання
│       │   │   ├── pv.json       # Правила для будь-якої PV-установки
│       │   ├── scenario/      # Перевірка сценарію системи
│       │   └── profile/
│       │
│       ├── templates/         # дефолтні каталоги (також у пакеті,
│       │   │                 # щоб їх можна було встановити через pip)
│       │   ├── technology/
│       │   ├── scenario/ # Перевірка сценарію системи
│       │   └── profile/
│       │
│       ├── core/            # I/O, валідація, merge-defaults
│       │   ├── json_schema_validator.py
│       │   └── user_project_loader.py
│       │
│       ├── optimizer/       # лише математика
│       │   ├── model_builder.py
│       │   ├──constraints.py 
│       │   ├──profile.py # Функції: lifetime, day_ahead, rolling
│       │   └── solvers/    # Обгортки до реальних або фейкових солверів
│       │       ├──__init__.py
│       │       ├── base.py 
│       │       ├── highs_solver.py
│       │     
│       │
│       └── data/            # (опційно) статичні ресурси, які не входять
│                             # у configs/, напр. іконки чи README шаблони
│
├── tests/                   # PyTest-кейсі, не потрапляють у пакет
│   ├── test_json_schema_validator.py
│   ├──test_ user_project_loader.py
│   ├──test_model_builder.py
│   └── ...
│
├── user_projects/           # ❗ поза src/ — не входить у pip-пакет
│   └── demo_project/
│       ├── instances.json
│       ├── scenario.json
│       └── optimization_profile.json
│       └── data_tables/   # ⬅️ CSV файли тут │
│           ├── prices.csv
│           └── demand.csv
│
├──.gitignore
├──.pre-commit-config
├──LICENSE
├── pyproject.toml           # вказує, що шукати пакети в "src"
└── README.md
└── requirements.txt