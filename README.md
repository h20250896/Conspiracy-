# Conspiracy Theory Knowledge Graph Dashboard

An interactive Streamlit dashboard that transforms conspiracy theory narratives into visual knowledge graphs for analysis and exploration.

## Features

- **Multiple Input Methods**: Paste text, upload PDF/DOCX files, or select from pre-made conspiracy theories
- **Automatic Entity Extraction**: Uses NLP to identify people, organizations, places, events, and concepts
- **Interactive Knowledge Graph**: Movable nodes with hover details and physics-based layout
- **Analytics Dashboard**: Graph statistics, centrality measures, and entity type distribution
- **Narrative Synthesis**: AI-generated summary that connects the dots in the conspiracy theory
- **Export Options**: Download graphs as HTML or data as JSON

## Pre-made Conspiracy Theories

- Netaji Subhas Chandra Bose Death Mystery
- Moon Landing Hoax
- JFK Assassination Conspiracy
- 9/11 Controlled Demolition Theory

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download the spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The dashboard will open in your browser. Choose your input method and explore the knowledge graph!

## How It Works

1. **Text Processing**: Input text is analyzed using spaCy for named entity recognition
2. **Graph Construction**: Entities become nodes, relationships are inferred from proximity
3. **Visualization**: PyVis creates an interactive HTML graph with customizable physics
4. **Analysis**: NetworkX calculates centrality measures and graph statistics
5. **Synthesis**: Custom algorithm generates narrative summaries based on graph structure

## Requirements

- Python 3.8+
- Streamlit
- NetworkX
- PyVis
- spaCy with en_core_web_sm model
- PyPDF2
- python-docx
- Matplotlib

## Industry-Ready Features

- Error handling and user feedback
- Responsive design with columns
- Loading spinners for long operations
- Export functionality
- Clean, professional UI
- Scalable architecture for adding more theories