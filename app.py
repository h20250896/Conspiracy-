import os
import re
import json
import tempfile
from itertools import combinations
from collections import Counter
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

# For file processing (FINAL STABLE VERSION)

import streamlit as st
import spacy

@st.cache_resource
def load_spacy_model():
    try:
        # Try loading full model
        return spacy.load("en_core_web_sm")
    except Exception:
        # Fallback (guaranteed to work)
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        return nlp

nlp = load_spacy_model()

# Other dependencies
try:
    import PyPDF2
    import docx
except ImportError:
    st.error("Missing dependencies. Please install: PyPDF2 and python-docx")
    st.stop()
STYLE = """
<style>
body {
    background: radial-gradient(circle at top left, rgba(63, 120, 255, 0.12), transparent 24%),
                radial-gradient(circle at bottom right, rgba(86, 215, 255, 0.10), transparent 18%),
                linear-gradient(180deg, #08101d 0%, #060b14 100%);
    color: #f4f7fb;
}
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(0deg, rgba(255,255,255,0.02), rgba(255,255,255,0.02) 1px, transparent 2px, transparent 24px),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.02) 1px, transparent 2px, transparent 24px);
    opacity: 0.08;
    pointer-events: none;
    z-index: -1;
}
section.main {
    background: rgba(8, 12, 23, 0.96) !important;
    border-radius: 30px;
    padding: 28px 34px 36px 34px;
    box-shadow: 0 32px 100px rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(7,13,27,0.98), rgba(11,18,39,0.95)) !important;
}
.css-1d391kg {
    background: transparent !important;
}
.board-header {
    position: relative;
    background: linear-gradient(135deg, rgba(10, 17, 35, 0.97), rgba(18, 30, 56, 0.98));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 30px;
    padding: 30px 32px;
    margin-bottom: 28px;
    box-shadow: 0 28px 90px rgba(0,0,0,0.28);
    overflow: hidden;
}
.board-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 18% 20%, rgba(255,255,255,0.06), transparent 24%),
                radial-gradient(circle at 82% 45%, rgba(255,255,255,0.04), transparent 18%);
    opacity: 1;
    pointer-events: none;
}
.board-header::after {
    content: '';
    position: absolute;
    top: 24px;
    right: 24px;
    width: 120px;
    height: 120px;
    background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.02));
    border-radius: 18px;
    transform: rotate(12deg);
    box-shadow: 0 28px 70px rgba(0,0,0,0.25);
}
.board-title {
    font-size: 2.95rem;
    letter-spacing: 0.12em;
    margin-bottom: 12px;
    color: #ffffff;
    font-weight: 900;
}
.board-subtitle {
    color: #ffffff;
    font-size: 1.05rem;
    margin-top: 10px;
    max-width: 760px;
    line-height: 1.7;
}
.board-pill {
    display: inline-flex;
    align-items: center;
    padding: 10px 18px;
    border-radius: 999px;
    margin-right: 10px;
    margin-top: 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.09);
    color: #d9e4ff;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.panel-card {
    position: relative;
    background: rgba(12, 18, 35, 0.96);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 26px;
    padding: 28px;
    box-shadow: 0 26px 78px rgba(0,0,0,0.30);
    margin-bottom: 26px;
}
.panel-card::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 20px;
    width: 42px;
    height: 8px;
    background: rgba(255,255,255,0.08);
    border-radius: 999px;
    transform: rotate(-8deg);
}
.panel-header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 22px;
}
.panel-title {
    font-size: 1.28rem;
    font-weight: 800;
    color: #000000;
    margin-bottom: 6px;
}
.panel-note {
    color: #000000;
    line-height: 1.72;
    max-width: 420px;
}
.metric-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border-radius: 999px;
    padding: 10px 16px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    color: #f4f9ff;
    margin-bottom: 12px;
}
.panel-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}
.stDownloadButton>button, .stButton>button {
    background: linear-gradient(135deg, #5c80ff, #33d1ff) !important;
    color: #ffffff !important;
    border-radius: 999px !important;
    padding: 0.95rem 1.6rem !important;
    font-weight: 800 !important;
    box-shadow: 0 12px 35px rgba(49, 114, 255, 0.25) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
}
.st-download-button {
    width: 100% !important;
}
.note-card {
    background: rgba(14, 24, 44, 0.96);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    margin-bottom: 18px;
}
.note-card:before {
    content: '';
    position: absolute;
    top: 16px;
    left: 16px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #ff7f50;
    box-shadow: 0 0 0 10px rgba(255,127,80,0.12);
}
.note-card h4 {
    margin: 0 0 10px 0;
    color: #f7fbff;
}
.note-card p {
    margin: 0;
    color: rgba(215, 227, 255, 0.82);
    line-height: 1.65;
}
.conclusion-card {
    background: rgba(2, 12, 23, 0.96);
    border: 1px solid rgba(33, 128, 255, 0.22);
    border-radius: 20px;
    padding: 24px;
    margin-top: 18px;
    color: #eef4ff;
}
.conclusion-card h4 {
    margin: 0 0 10px 0;
    color: #ffffff;
    font-size: 1.18rem;
}
.conclusion-card p {
    margin: 0;
    color: #d8e9ff;
    line-height: 1.75;
    font-size: 1rem;
}
.bullet {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 10px;
    background: #33c4ff;
}
.mood-board {
    display: grid;
    grid-template-columns: repeat(3, minmax(180px, 1fr));
    gap: 22px;
    align-items: start;
    margin-bottom: 28px;
    position: relative;
}
.mood-card {
    position: relative;
    min-height: 200px;
    border-radius: 22px;
    background-size: cover;
    background-position: center;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 22px 50px rgba(0,0,0,0.22);
}
.mood-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.10), rgba(0,0,0,0.40));
}
.mood-card-label {
    position: absolute;
    left: 18px;
    bottom: 18px;
    color: #f7fbff;
    font-weight: 800;
    letter-spacing: 0.04em;
    z-index: 2;
    text-shadow: 0 4px 16px rgba(0,0,0,0.35);
}
.pin {
    position: absolute;
    top: 16px;
    left: 16px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: radial-gradient(circle, #ff5151 0%, #b70000 55%);
    box-shadow: 0 0 14px rgba(255,81,81,0.35);
    z-index: 2;
}
.mood-connector {
    position: absolute;
    top: 110px;
    left: 10%;
    right: 10%;
    height: 4px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,85,85,0.85) 24%, rgba(255,85,85,0.85) 76%, transparent 100%);
    border-radius: 999px;
    filter: drop-shadow(0 0 12px rgba(255,85,85,0.35));
}
.stTextArea>div>div>textarea,
.stTextArea>div>div>div>textarea {
    background: rgba(2, 10, 23, 0.92) !important;
    color: #eef4ff !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
.stFileUploader>div,
.stRadio>div {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 18px;
}
</style>
"""

SUPPORTED_ENTITY_TYPES = {'PERSON', 'ORG', 'GPE', 'EVENT', 'LAW', 'WORK_OF_ART', 'NORP', 'FAC', 'PRODUCT'}
ENTITY_TYPE_MAP = {
    'PERSON': 'Person',
    'ORG': 'Organization',
    'GPE': 'Place',
    'EVENT': 'Event',
    'LAW': 'Document',
    'WORK_OF_ART': 'Document',
    'NORP': 'Concept',
    'FAC': 'Place',
    'PRODUCT': 'Concept',
}
TYPE_COLORS = {
    'Person':       '#FF6B6B',
    'Organization': '#5DA7E4',
    'Place':        '#4CCFAC',
    'Event':        '#FFB547',
    'Document':     '#9C8DF4',
    'Concept':      '#E67CD9',
}

# Pre-made conspiracy theory stories
PREMADE_STORIES = {
    "Netaji Subhas Chandra Bose Death Mystery": {
        "text": """
In August 1945, Netaji Subhas Chandra Bose reportedly died in a plane crash in Taihoku, Taiwan.
The British government, through MI6, and the American CIA had been monitoring Netaji's movements
across Southeast Asia for years, fearing his influence on Indian independence.

Following independence in 1947, Prime Minister Jawaharlal Nehru ordered all intelligence files
pertaining to Netaji sealed. The Indian Intelligence Bureau continued surveillance of Netaji's
family members in Kolkata for decades afterward.

In Faizabad, Uttar Pradesh, a mysterious hermit known as Gumnami Baba lived in complete seclusion
from 1975 until his death in 1985. Witnesses including local lawyers, journalists, and former
INA soldiers claimed Gumnami Baba was in fact Netaji living under a false identity.

After Gumnami Baba's death, investigators discovered trunks containing: photographs of Subhas
Chandra Bose, letters addressed to 'Netaji', personal diaries, military maps, and medals
matching those awarded to Bose by the Japanese Imperial Army.

The Mukherjee Commission, established by the Supreme Court of India in 1999, investigated the
crash and concluded in its 2005 report that the plane crash story was fabricated.
""",
        "graph_data": {
            "entities": [
                {"id": "netaji", "label": "Subhas Chandra Bose", "type": "Person", "description": "Indian freedom fighter and INA leader"},
                {"id": "nehru", "label": "Jawaharlal Nehru", "type": "Person", "description": "First Prime Minister of India"},
                {"id": "gumnami", "label": "Gumnami Baba", "type": "Person", "description": "Mysterious hermit in Faizabad (1975-1985)"},
                {"id": "mukherjee_com", "label": "Mukherjee Commission", "type": "Organization", "description": "Supreme Court inquiry (1999-2005)"},
                {"id": "mi6", "label": "MI6", "type": "Organization", "description": "British intelligence agency"},
                {"id": "cia", "label": "CIA", "type": "Organization", "description": "American intelligence agency"},
                {"id": "ib", "label": "Intelligence Bureau", "type": "Organization", "description": "Indian intelligence agency"},
                {"id": "taiwan", "label": "Taihoku, Taiwan", "type": "Place", "description": "Alleged crash site (1945)"},
                {"id": "faizabad", "label": "Faizabad, UP", "type": "Place", "description": "Where Gumnami Baba lived"},
                {"id": "crash", "label": "1945 Plane Crash", "type": "Event", "description": "Official story of Netaji's death"},
                {"id": "sealed_files", "label": "Sealed Intelligence Files", "type": "Document", "description": "Nehru ordered them classified"},
                {"id": "trunks", "label": "Gumnami's Trunks", "type": "Document", "description": "Photos, letters, medals found after death"},
                {"id": "mukherjee_report", "label": "Mukherjee Report 2005", "type": "Document", "description": "Concluded crash was fabricated"},
                {"id": "conspiracy", "label": "Death Conspiracy Theory", "type": "Concept", "description": "Belief that Netaji survived beyond 1945"},
            ],
            "relationships": [
                {"source": "netaji", "target": "crash", "relation": "allegedly died in", "weight": 3},
                {"source": "mi6", "target": "netaji", "relation": "monitored movements of", "weight": 3},
                {"source": "cia", "target": "netaji", "relation": "tracked", "weight": 2},
                {"source": "nehru", "target": "sealed_files", "relation": "ordered sealing of", "weight": 3},
                {"source": "ib", "target": "faizabad", "relation": "conducted surveillance in", "weight": 3},
                {"source": "gumnami", "target": "faizabad", "relation": "lived in seclusion in", "weight": 3},
                {"source": "gumnami", "target": "netaji", "relation": "possibly lived as", "weight": 3},
                {"source": "trunks", "target": "netaji", "relation": "contained belongings of", "weight": 3},
                {"source": "mukherjee_com", "target": "crash", "relation": "investigated", "weight": 3},
                {"source": "mukherjee_report", "target": "crash", "relation": "concluded fabrication of", "weight": 3},
                {"source": "conspiracy", "target": "netaji", "relation": "surrounded death of", "weight": 3},
            ]
        }
    },
    "Moon Landing Hoax": {
        "text": """
The Apollo 11 moon landing in 1969 is widely regarded as one of humanity's greatest achievements.
However, conspiracy theorists claim the entire event was staged by NASA in a Hollywood studio
to win the Space Race against the Soviet Union.

Key claims include: the American flag appearing to wave in the windless lunar environment,
shadows falling in different directions suggesting multiple light sources, and the lack of stars
in the sky despite the absence of atmosphere. Theorists point to anomalies in photographs,
missing telemetry data, and the mysterious death of key witnesses.

NASA has repeatedly debunked these claims with evidence including laser reflectors left on
the moon that are still used today, and third-party tracking of the mission by other countries.
Despite this, the hoax theory persists in popular culture.
""",
        "graph_data": {
            "entities": [
                {"id": "apollo11", "label": "Apollo 11 Mission", "type": "Event", "description": "1969 moon landing"},
                {"id": "nasa", "label": "NASA", "type": "Organization", "description": "U.S. space agency"},
                {"id": "soviet_union", "label": "Soviet Union", "type": "Organization", "description": "Space Race competitor"},
                {"id": "hollywood", "label": "Hollywood Studio", "type": "Place", "description": "Alleged filming location"},
                {"id": "flag", "label": "American Flag", "type": "Concept", "description": "Appeared to wave in vacuum"},
                {"id": "shadows", "label": "Shadows Anomaly", "type": "Concept", "description": "Inconsistent lighting"},
                {"id": "stars", "label": "Missing Stars", "type": "Concept", "description": "No stars visible in photos"},
                {"id": "laser_reflectors", "label": "Laser Reflectors", "type": "Document", "description": "Still used for measurements"},
                {"id": "hoax_theory", "label": "Moon Landing Hoax", "type": "Concept", "description": "Claim that landing was faked"},
            ],
            "relationships": [
                {"source": "nasa", "target": "apollo11", "relation": "conducted", "weight": 3},
                {"source": "apollo11", "target": "hoax_theory", "relation": "subject of", "weight": 3},
                {"source": "hollywood", "target": "apollo11", "relation": "allegedly staged in", "weight": 2},
                {"source": "soviet_union", "target": "apollo11", "relation": "tracked mission of", "weight": 3},
                {"source": "flag", "target": "hoax_theory", "relation": "cited as evidence for", "weight": 2},
                {"source": "shadows", "target": "hoax_theory", "relation": "cited as evidence for", "weight": 2},
                {"source": "stars", "target": "hoax_theory", "relation": "cited as evidence for", "weight": 2},
                {"source": "laser_reflectors", "target": "apollo11", "relation": "prove authenticity of", "weight": 3},
            ]
        }
    },
    "JFK Assassination Conspiracy": {
        "text": """
President John F. Kennedy was assassinated on November 22, 1963, in Dallas, Texas.
The Warren Commission concluded that Lee Harvey Oswald acted alone in shooting Kennedy
from the Texas School Book Depository. However, numerous conspiracy theories suggest
involvement by the CIA, Mafia, military-industrial complex, or even Lyndon B. Johnson.

Key elements include the 'magic bullet' theory, acoustic evidence of additional shots,
the suspicious deaths of witnesses, and Kennedy's policies that threatened powerful interests.
The House Select Committee on Assassinations in 1979 concluded that Kennedy was likely
assassinated as a result of a conspiracy, though they couldn't identify the other gunmen.
""",
        "graph_data": {
            "entities": [
                {"id": "jfk", "label": "John F. Kennedy", "type": "Person", "description": "35th U.S. President"},
                {"id": "oswald", "label": "Lee Harvey Oswald", "type": "Person", "description": "Alleged lone gunman"},
                {"id": "warren_commission", "label": "Warren Commission", "type": "Organization", "description": "Official investigation (1964)"},
                {"id": "cia", "label": "CIA", "type": "Organization", "description": "Intelligence agency"},
                {"id": "mafia", "label": "Mafia", "type": "Organization", "description": "Organized crime"},
                {"id": "lBJ", "label": "Lyndon B. Johnson", "type": "Person", "description": "Vice President, became President"},
                {"id": "dallas", "label": "Dallas, Texas", "type": "Place", "description": "Assassination location"},
                {"id": "magic_bullet", "label": "Magic Bullet Theory", "type": "Concept", "description": "Controversial ballistics"},
                {"id": "acoustic_evidence", "label": "Acoustic Evidence", "type": "Document", "description": "Dictabelt recording analysis"},
                {"id": "house_committee", "label": "House Select Committee", "type": "Organization", "description": "1979 investigation"},
                {"id": "conspiracy", "label": "JFK Assassination Conspiracy", "type": "Concept", "description": "Multiple parties involved"},
            ],
            "relationships": [
                {"source": "oswald", "target": "jfk", "relation": "allegedly assassinated", "weight": 3},
                {"source": "warren_commission", "target": "oswald", "relation": "concluded acted alone", "weight": 3},
                {"source": "cia", "target": "conspiracy", "relation": "possibly involved in", "weight": 2},
                {"source": "mafia", "target": "conspiracy", "relation": "possibly involved in", "weight": 2},
                {"source": "lBJ", "target": "conspiracy", "relation": "possibly involved in", "weight": 2},
                {"source": "magic_bullet", "target": "warren_commission", "relation": "central to findings of", "weight": 3},
                {"source": "acoustic_evidence", "target": "house_committee", "relation": "analyzed by", "weight": 3},
                {"source": "house_committee", "target": "conspiracy", "relation": "concluded existed", "weight": 3},
                {"source": "jfk", "target": "dallas", "relation": "assassinated in", "weight": 3},
            ]
        }
    },
    "9/11 Controlled Demolition Theory": {
        "text": """
The September 11, 2001 terrorist attacks destroyed the World Trade Center towers and damaged
the Pentagon. The official explanation attributes the collapses to fire and structural damage
from the plane impacts. However, conspiracy theorists claim the buildings were brought down
by controlled demolition using explosives planted in advance.

Evidence cited includes the speed of collapse, symmetrical nature of the falls, molten metal
found in the debris, and reports of explosions heard by witnesses. Critics argue that jet fuel
fires couldn't melt steel beams, and point to the rapid construction of Building 7's collapse.
Government reports and structural engineers maintain the official explanation is correct.
""",
        "graph_data": {
            "entities": [
                {"id": "wtc", "label": "World Trade Center", "type": "Place", "description": "Twin Towers destroyed"},
                {"id": "pentagon", "label": "Pentagon", "type": "Place", "description": "Partially damaged"},
                {"id": "al_qaeda", "label": "Al-Qaeda", "type": "Organization", "description": "Terrorist group blamed"},
                {"id": "controlled_demolition", "label": "Controlled Demolition", "type": "Concept", "description": "Method of building destruction"},
                {"id": "jet_fuel", "label": "Jet Fuel Fires", "type": "Concept", "description": "Official cause of collapse"},
                {"id": "molten_metal", "label": "Molten Metal", "type": "Concept", "description": "Found in debris"},
                {"id": "building7", "label": "Building 7", "type": "Place", "description": "Collapsed without direct hit"},
                {"id": "nist_report", "label": "NIST Report", "type": "Document", "description": "Official investigation"},
                {"id": "conspiracy", "label": "9/11 Controlled Demolition", "type": "Concept", "description": "Buildings demolished intentionally"},
            ],
            "relationships": [
                {"source": "al_qaeda", "target": "wtc", "relation": "attacked", "weight": 3},
                {"source": "controlled_demolition", "target": "wtc", "relation": "allegedly destroyed", "weight": 3},
                {"source": "jet_fuel", "target": "wtc", "relation": "officially caused collapse of", "weight": 3},
                {"source": "molten_metal", "target": "controlled_demolition", "relation": "cited as evidence for", "weight": 2},
                {"source": "building7", "target": "controlled_demolition", "relation": "cited as evidence for", "weight": 3},
                {"source": "nist_report", "target": "jet_fuel", "relation": "supports", "weight": 3},
                {"source": "conspiracy", "target": "wtc", "relation": "explains destruction of", "weight": 3},
            ]
        }
    }
}

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def normalize_label(text):
    return re.sub(r"\s+", " ", text.strip())


def extract_entities(text):
    doc = nlp(text)
    entities = []
    label_to_id = {}
    for ent in doc.ents:
        if ent.label_ in SUPPORTED_ENTITY_TYPES:
            label = normalize_label(ent.text)
            if not label:
                continue
            key = label.lower()
            if key in label_to_id:
                continue
            entity_type = ENTITY_TYPE_MAP.get(ent.label_, 'Concept')
            entity_id = f"ent_{len(label_to_id)}"
            label_to_id[key] = entity_id
            entities.append({
                "id": entity_id,
                "label": label,
                "type": entity_type,
                "description": f"Extracted {entity_type.lower()}"
            })
    return entities, label_to_id


def infer_relation(ent1, ent2, sent):
    if ent1.end < ent2.start:
        span = sent[ent1.end:ent2.start]
    else:
        span = sent[ent2.end:ent1.start]

    verbs = [tok.lemma_ for tok in span if tok.pos_ in {"VERB", "AUX"}]
    nouns = [tok.lemma_ for tok in span if tok.pos_ in {"NOUN", "PROPN"}]

    if verbs:
        return " ".join(verbs[:2])
    if nouns:
        return "linked with"
    return "connected to"


def generate_relationships(text, label_to_id):
    doc = nlp(text)
    relationships = []
    seen = set()
    for sent in doc.sents:
        sent_entities = [ent for ent in sent.ents if normalize_label(ent.text).lower() in label_to_id]
        for ent1, ent2 in combinations(sent_entities, 2):
            src = label_to_id[normalize_label(ent1.text).lower()]
            tgt = label_to_id[normalize_label(ent2.text).lower()]
            if src == tgt:
                continue
            relation = infer_relation(ent1, ent2, sent)
            weight = 2 if relation != "connected to" else 1
            edge_key = (src, tgt, relation)
            if edge_key in seen:
                continue
            seen.add(edge_key)
            relationships.append({
                "source": src,
                "target": tgt,
                "relation": relation,
                "weight": weight
            })
    return relationships


def build_graph_data_from_text(text):
    entities, label_to_id = extract_entities(text)
    relationships = generate_relationships(text, label_to_id)
    if not relationships and len(entities) > 1:
        relationships = generate_basic_relationships(entities)
    return {"entities": entities, "relationships": relationships}


def generate_basic_relationships(entities):
    relationships = []
    for i, ent1 in enumerate(entities):
        for j, ent2 in enumerate(entities):
            if i != j and abs(i - j) <= 1:
                relationships.append({
                    "source": ent1["id"],
                    "target": ent2["id"],
                    "relation": "associated with",
                    "weight": 1
                })
    return relationships


def build_nx_graph(graph_data):
    G = nx.DiGraph()
    for entity in graph_data["entities"]:
        G.add_node(
            entity["id"],
            label=entity["label"],
            type=entity["type"],
            description=entity.get("description", "")
        )
    for rel in graph_data["relationships"]:
        if rel["source"] in G and rel["target"] in G:
            G.add_edge(
                rel["source"],
                rel["target"],
                relation=rel["relation"],
                weight=rel.get("weight", 1)
            )
    return G

def create_interactive_graph(G, graph_data):
    net = Network(height="700px", width="100%",
                  directed=True, notebook=False,
                  bgcolor="#0B1320", font_color="#F5F7FB")

    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 5,
        "shadow": { "enabled": true, "size": 16 }
      },
      "edges": {
        "smooth": { "type": "dynamic" },
        "shadow": { "enabled": false },
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.8 } },
        "color": { "inherit": false }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -1600,
          "centralGravity": 0.12,
          "springLength": 250,
          "springConstant": 0.18,
          "damping": 0.55
        },
        "minVelocity": 0.75,
        "solver": "barnesHut",
        "stabilization": { "enabled": true, "iterations": 300 }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true,
        "tooltipDelay": 100,
        "dragNodes": true
      }
    }
    """)

    centrality = nx.degree_centrality(G)
    max_c = max(centrality.values()) if centrality else 1
    entity_lookup = {e["id"]: e for e in graph_data["entities"]}

    for node_id in G.nodes():
        entity = entity_lookup.get(node_id, {})
        label = str(entity.get("label", node_id))
        etype = entity.get("type", "Concept")
        desc = str(entity.get("description", ""))

        color = TYPE_COLORS.get(etype, "#727272")
        degree = G.degree(node_id)
        c_score = centrality.get(node_id, 0)
        node_size = int(28 + 42 * (c_score / max_c))

        tooltip = (
            f"<div style='font-family:Arial, sans-serif; line-height:1.4;'>"
            f"<b>{label}</b><br>"
            f"<i>{etype}</i><br>"
            f"Connections: {degree}<br>"
            f"Centrality: {c_score:.3f}<br>"
            f"<hr style='margin:6px 0; border-color:#4B5C6B'>"
            f"{desc}"
            f"</div>"
        )

        net.add_node(
            node_id,
            label=label,
            title=tooltip,
            color={
                "background": color,
                "border": "#FFFFFF",
                "highlight": {"background": "#FFFFFF", "border": color},
                "hover": {"background": "#FFFFFF", "border": color}
            },
            shape="dot",
            size=node_size,
            font={"color": "#FFFFFF", "size": 14, "face": "Helvetica", "bold": True}
        )

    WEIGHT_COLORS = {1: "#8899AA", 2: "#F5A623", 3: "#FF6B6B"}
    for src, tgt, data in G.edges(data=True):
        weight = data.get("weight", 1)
        relation = str(data.get("relation", ""))
        net.add_edge(
            src, tgt,
            title=relation,
            label=relation if len(relation) < 28 else relation[:26] + "...",
            width=1.5 + weight,
            color={"color": WEIGHT_COLORS.get(weight, "#8899AA"), "opacity": 0.85},
            font={"size": 10, "color": "#FFFFFF", "strokeWidth": 0},
            arrows={"to": {"enabled": True, "scaleFactor": 0.7}}
        )

    return net

def generate_story_summary(G, graph_data):
    summary = []
    summary.append("## Knowledge Graph Analysis Summary\n")
    
    # Basic stats
    summary.append(f"**Graph Statistics:** {G.number_of_nodes()} entities, {G.number_of_edges()} connections\n")
    
    # Top connected entities
    degree_dict = dict(G.degree())
    top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
    summary.append("**Most Connected Entities:**\n")
    id_to_label = {e["id"]: e["label"] for e in graph_data["entities"]}
    for node_id, deg in top_nodes:
        label = id_to_label.get(node_id, node_id)
        summary.append(f"- {label}: {deg} connections\n")
    
    # Critical connections
    critical = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("weight", 1) == 3]
    if critical:
        summary.append("\n**Key Evidence/Strong Connections:**\n")
        for u, v, d in critical:
            src = id_to_label.get(u, u)
            tgt = id_to_label.get(v, v)
            summary.append(f"- {src} → {d['relation']} → {tgt}\n")
    
    # Narrative synthesis
    summary.append("\n**Narrative Synthesis:**\n")
    summary.append("Based on the knowledge graph analysis, the following pattern emerges:\n\n")
    
    # Find central figure
    if top_nodes:
        central_entity = id_to_label.get(top_nodes[0][0], top_nodes[0][0])
        summary.append(f"The story centers around **{central_entity}**, who is connected to {top_nodes[0][1]} other elements.\n\n")
    
    # Analyze clusters
    wcc = list(nx.weakly_connected_components(G))
    if len(wcc) > 1:
        summary.append(f"The narrative contains {len(wcc)} interconnected themes:\n")
        for i, component in enumerate(sorted(wcc, key=len, reverse=True), 1):
            labels = [id_to_label.get(n, n) for n in list(component)[:3]]
            summary.append(f"- Theme {i}: {', '.join(labels)}{'...' if len(component)>3 else ''}\n")
    
    # Strong final takeaway
    if top_nodes:
        takeaways = []
        primary = id_to_label.get(top_nodes[0][0], top_nodes[0][0])
        takeaways.append(f"The story ultimately comes down to **{primary}** being at the center of the conspiracy.")
        if len(top_nodes) > 1:
            secondary = id_to_label.get(top_nodes[1][0], top_nodes[1][0])
            takeaways.append(f"{secondary} is the key secondary actor that connects multiple themes.")
        if critical:
            src = id_to_label.get(critical[0][0], critical[0][0])
            tgt = id_to_label.get(critical[0][1], critical[0][1])
            takeaways.append(f"The strongest narrative thread is: {src} → {critical[0][2]['relation']} → {tgt}.")
        else:
            takeaways.append("The evidence is spread across themes, meaning the final conclusion rests on the strongest central relationships rather than one single link.")
        summary.append("\n**Conclusion:** " + " ".join(takeaways))
    else:
        summary.append("\n**Conclusion:** The story summary is too sparse to produce a confident final takeaway.")
    
    return "".join(summary)


def generate_story_conclusion(G, graph_data):
    id_to_label = {e["id"]: e["label"] for e in graph_data["entities"]}
    degree_dict = dict(G.degree())
    if not degree_dict:
        return "No clear conclusion could be drawn from the current story graph."
    top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
    primary = id_to_label.get(top_nodes[0][0], top_nodes[0][0])
    description = f"This investigation boils down to {primary} being the core figure in the narrative."
    if len(top_nodes) > 1:
        secondary = id_to_label.get(top_nodes[1][0], top_nodes[1][0])
        description += f" {secondary} is the next most influential actor and helps define the key conspiracy thread."
    critical = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("weight", 1) == 3]
    if critical:
        src = id_to_label.get(critical[0][0], critical[0][0])
        tgt = id_to_label.get(critical[0][1], critical[0][1])
        description += f" The most compelling connection is {src} → {critical[0][2]['relation']} → {tgt}, which anchors the final story outcome."
    else:
        description += " The map suggests that the conclusion is built from the interplay between several related entities rather than a single decisive event."
    return description


def render_bar_chart(labels, values, title, color):
    fig, ax = plt.subplots(figsize=(6, 3))
    y_positions = range(len(labels))
    ax.barh(y_positions, values, color=color, alpha=0.88)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_title(title, color="#F5F7FB", fontsize=13, pad=12)
    ax.set_facecolor("#0B1320")
    fig.patch.set_facecolor("#0B1320")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#4B5C6B")
    ax.spines["bottom"].set_color("#4B5C6B")
    ax.xaxis.label.set_color("#F5F7FB")
    ax.yaxis.label.set_color("#F5F7FB")
    ax.tick_params(colors="#A1B3C6")
    return fig


def build_graph_summary(G, graph_data):
    degree_dict = dict(G.degree())
    centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    top_degree = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
    id_to_label = {e["id"]: e["label"] for e in graph_data["entities"]}
    return {
        "top_degree": [(id_to_label.get(node, node), score) for node, score in top_degree],
        "top_centrality": sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_betweenness": [(id_to_label.get(node, node), score) for node, score in betweenness.items() if score > 0][:5],
    }


def main():
    st.set_page_config(
        page_title="Conspiracy Theory Knowledge Graph Dashboard",
        page_icon="🕸️",
        layout="wide"
    )
    st.markdown(STYLE, unsafe_allow_html=True)

    st.sidebar.header("Dashboard Controls")
    st.sidebar.markdown(
        "Upload a story, paste text, or choose a curated case study. The app will construct a premium-quality knowledge graph and analysis dashboard."
    )
    show_raw_data = st.sidebar.checkbox("Show raw graph JSON", value=False)
    show_analytics = st.sidebar.checkbox("Show supplemental analytics", value=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tips for best quality\n- Paste well-formed paragraphs\n- Use named entities clearly\n- For file upload, keep PDFs or Word files simple")

    st.title("🕸️ Conspiracy Intelligence Dashboard")
    st.markdown(
        "A premium knowledge graph workspace for mapping narratives, evidence, and hidden connections in conspiracy stories."
    )

    st.markdown(
        """
        <div class='board-header'>
            <div>
                <div class='board-title'>CONSPIRACY INVESTIGATION BOARD</div>
                <div class='board-subtitle'>Inspect narrative evidence, connect entities, and discover hidden patterns from stories.</div>
            </div>
            <div>
                <span class='board-pill'>Detective Board UI</span>
                <span class='board-pill'>Graph Intelligence</span>
                <span class='board-pill'>Evidence Summary</span>
            </div>
        </div>
        <div class='mood-board'>
            <div class='mood-card mood-card-left' style="background-image: url('https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=800&q=80');">
                <div class='pin'></div>
                <div class='mood-card-label'>Evidence File</div>
            </div>
            <div class='mood-card mood-card-center' style="background-image: url('https://images.unsplash.com/photo-1473187983305-f615310e7daa?auto=format&fit=crop&w=800&q=80');">
                <div class='pin'></div>
                <div class='mood-card-label'>Witness Notes</div>
            </div>
            <div class='mood-card mood-card-right' style="background-image: url('https://images.unsplash.com/photo-1521246722702-2f8c86f0d4f7?auto=format&fit=crop&w=800&q=80');">
                <div class='pin'></div>
                <div class='mood-card-label'>Intel Brief</div>
            </div>
            <div class='mood-connector'></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_method = st.radio("Choose input method:",
                          ["Paste Text", "Upload File", "Select Pre-made Story"])

    story_text = ""
    graph_data = None
    
    if input_method == "Paste Text":
        story_text = st.text_area("Paste your conspiracy theory text here:", height=260)
        if story_text:
            with st.spinner("Analyzing text and generating knowledge graph..."):
                graph_data = build_graph_data_from_text(story_text)
                if not graph_data["entities"]:
                    st.warning("No named entities were found. Please use a more descriptive passage.")
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload PDF or Word document", type=["pdf", "docx"])
        if uploaded_file:
            try:
                if uploaded_file.type == "application/pdf":
                    story_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    story_text = extract_text_from_docx(uploaded_file)
                
                st.success("File processed successfully!")
                st.text_area("Extracted text:", story_text[:1200] + "..." if len(story_text) > 1200 else story_text, height=180)
                
                with st.spinner("Analyzing text and generating knowledge graph..."):
                    graph_data = build_graph_data_from_text(story_text)
                    if not graph_data["entities"]:
                        st.warning("The uploaded file did not produce extractable entities. Try a different document.")
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    elif input_method == "Select Pre-made Story":
        selected_story = st.selectbox("Choose a conspiracy theory:", list(PREMADE_STORIES.keys()))
        if selected_story:
            story_data = PREMADE_STORIES[selected_story]
            story_text = story_data["text"]
            graph_data = story_data["graph_data"]
            st.text_area("Story text:", story_text, height=240)
    
    if graph_data and len(graph_data["entities"]) > 0:
        G = build_nx_graph(graph_data)
        graph_summary = build_graph_summary(G, graph_data)
        type_dist = Counter(G.nodes[n].get("type", "Unknown") for n in G.nodes())

        col1, col2 = st.columns([2, 1], gap="large")
        with col1:
            st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
            st.markdown(
                "<div class='panel-header'><div class='panel-title'>🕸️ Interactive Knowledge Map</div>"
                "<div class='panel-note'>A detective-board style canvas for inspecting entity relationships and evidence flow.</div></div>",
                unsafe_allow_html=True,
            )
            net = create_interactive_graph(G, graph_data)
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            tmp_file.close()
            try:
                net.save_graph(tmp_file.name)
                with open(tmp_file.name, "r", encoding="utf-8") as f:
                    html_content = f.read()
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
            components.html(html_content, height=720)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
            st.markdown(
                "<div class='panel-header'><div class='panel-title'>📊 Graph Intelligence</div>"
                "<div class='panel-note'>Key network insights to identify primary actors and critical evidence nodes.</div></div>",
                unsafe_allow_html=True,
            )
            st.metric("Entities", G.number_of_nodes())
            st.metric("Connections", G.number_of_edges())
            st.metric("Graph Density", f"{nx.density(G):.3f}")

            st.markdown("<div class='note-card'><h4>Top Connected Nodes</h4>", unsafe_allow_html=True)
            for label, score in graph_summary["top_degree"]:
                st.markdown(f"<p><span class='bullet'>•</span> {label}: <b>{score}</b> connections</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if show_analytics:
                st.markdown("<div class='note-card'><h4>Key Bridge Nodes</h4>", unsafe_allow_html=True)
                for label, score in graph_summary["top_betweenness"]:
                    st.markdown(f"<p><span class='bullet'>•</span> {label}: <b>{score:.3f}</b> betweenness</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='note-card'><h4>Entity Type Breakdown</h4>", unsafe_allow_html=True)
            for etype, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"<p><span class='bullet'>•</span> {etype}: <b>{count}</b></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📈 Visual Insights")
        chart_col1, chart_col2 = st.columns(2, gap="large")

        entity_labels = [etype for etype, _ in sorted(type_dist.items(), key=lambda x: x[1], reverse=True)]
        entity_counts = [count for _, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True)]
        if entity_labels:
            fig_type = render_bar_chart(entity_labels, entity_counts, "Entity Type Distribution", "#5DA7E4")
            chart_col1.pyplot(fig_type, clear_figure=True)

        degree_labels = [label for label, _ in graph_summary["top_degree"]]
        degree_scores = [score for _, score in graph_summary["top_degree"]]
        if degree_labels:
            fig_degree = render_bar_chart(degree_labels, degree_scores, "Top Connected Entities", "#FF6B6B")
            chart_col2.pyplot(fig_degree, clear_figure=True)

        st.markdown("---")
        st.subheader("📖 Narrative Intelligence")
        summary = generate_story_summary(G, graph_data)
        st.markdown(summary)

        st.markdown("<div class='conclusion-card'><h4>Final Takeaway</h4><p>" + generate_story_conclusion(G, graph_data) + "</p></div>", unsafe_allow_html=True)

        if show_raw_data:
            with st.expander("Raw Graph JSON"):
                st.json(graph_data)

        st.markdown("---")
        st.subheader("💾 Export")
        download_col1, download_col2 = st.columns(2, gap="large")

        with download_col1:
            html_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            html_file.close()
            try:
                net.save_graph(html_file.name)
                with open(html_file.name, "rb") as f:
                    html_bytes = f.read()
            finally:
                if os.path.exists(html_file.name):
                    os.unlink(html_file.name)
            st.download_button(
                label="Download Interactive HTML",
                data=html_bytes,
                file_name="knowledge_graph.html",
                mime="text/html"
            )

        with download_col2:
            json_data = json.dumps(graph_data, indent=2)
            st.download_button(
                label="Download Graph JSON",
                data=json_data,
                file_name="knowledge_graph.json",
                mime="application/json"
            )
    else:
        st.info("Please provide a story text or select a pre-made story to generate the knowledge graph.")

if __name__ == "__main__":
    main()
