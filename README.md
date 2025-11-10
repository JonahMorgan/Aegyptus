# Aegyptus

An Egyptian hieroglyphics translator and natural language processing toolkit for Middle Egyptian.

## Overview

Aegyptus is a machine learning-based translation system that converts between Egyptian hieroglyphics and German. The project includes:

- **Hieroglyphics Tokenizer**: Custom tokenization for Egyptian hieroglyphic text
- **Data Collection Tools**: Wiktionary parsers for Middle Egyptian entries
- **Translation Models**: Transformer-based models for hieroglyphics ↔ German translation
- **Lexicon Builder**: Tools to construct comprehensive Egyptian dictionaries

## Features

- 🔤 Hieroglyphic text tokenization and processing
- 🌐 Bidirectional translation (Hieroglyphics ↔ German)
- 📚 Automated data collection from Wiktionary
- 🧠 Transformer-based neural translation models
- 📖 Dictionary and lexicon management

## Installation

### Prerequisites

- Python 3.7+
- PyTorch
- transformers
- Other dependencies listed in `requirements.txt`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/JonahMorgan/Aegyptus.git
cd Aegyptus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Tokenizing Hieroglyphic Text

```python
from hieroglyph_tokenizer import HieroglyphTokenizer

tokenizer = HieroglyphTokenizer("path/to/lexicon.json")
tokens = tokenizer.tokenize("your hieroglyphic text here")
```

### Building a Dataset

```python
from dataset_builder import WordSubwordDatasetBuilder

builder = WordSubwordDatasetBuilder("path/to/lexicon.json")
builder.build_dataset("input.jsonl", "output.jsonl", direction="hg2de")
```

### Data Collection

The project includes tools to collect Egyptian language data from Wiktionary:

```bash
cd "Data Collection and Management/Wiktionary"
python egyptian_parser.py
```

## Project Structure

```
Aegyptus/
├── Aegyptus Translator (full vibecoded)/
│   ├── build_lexicon_robust.py      # Lexicon building tools
│   ├── dataset_builder.py           # Dataset creation
│   ├── hieroglyph_tokenizer.py      # Hieroglyphic tokenization
│   ├── german_tokenizer.py          # German text processing
│   ├── grammar_transformer.py       # Grammar transformation
│   └── tools/                       # Utility scripts
├── Data Collection and Management/
│   ├── Wiktionary/                  # Wiktionary data extraction
│   └── Dictionary of Middle Egyptian/
└── README.md
```

## Data Sources

- Middle Egyptian entries from [Wiktionary](https://en.wiktionary.org/)
- Licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Wiktionary community for Egyptian language data
- Wikimedia for WikiHiero hieroglyph images
- The Egyptology and NLP research communities

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This project is under active development. Features and APIs may change.
