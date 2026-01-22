"""
Symptom-to-Condition Mapping Database

This file contains mappings of reported symptoms to potential conditions they may indicate.
Used as a knowledge base for the rule-based symptom checker.

IMPORTANT: These mappings are for TRIAGE GUIDANCE ONLY, not for diagnosis.
"""

# Comprehensive symptom-to-condition mapping
# Each symptom maps to a list of conditions it might indicate
SYMPTOM_CONDITIONS_MAP = {
    "fever": ["viral_infection", "bacterial_infection", "covid19", "malaria", "dengue", "typhoid"],
    "cough": ["common_cold", "bronchitis", "covid19", "pneumonia", "asthma"],
    "chest_pain": ["cardiac_risk", "anxiety", "muscular_strain", "pneumonia"],
    "breathing_difficulty": ["cardiac_risk", "asthma", "pneumonia", "severe_anxiety"],
    "shortness_of_breath": ["cardiac_risk", "asthma", "pneumonia", "covid19"],
    "headache": ["migraine", "stress", "viral_infection", "hypertension"],
    "sore_throat": ["common_cold", "strep_throat", "viral_infection"],
    "body_ache": ["viral_infection", "malaria", "covid19", "influenza", "muscular_strain"],
    "fatigue": ["anemia", "viral_infection", "diabetes", "thyroid_disorder", "malaria"],
    "loss_of_taste": ["covid19", "cold", "anosmia"],
    "loss_of_smell": ["covid19", "cold", "sinusitis"],
    "nausea": ["gastroenteritis", "migraine", "pregnancy", "medication_side_effect"],
    "vomiting": ["gastroenteritis", "food_poisoning", "pregnancy", "anxiety"],
    "diarrhea": ["gastroenteritis", "food_poisoning", "IBS", "infection"],
    "abdominal_pain": ["gastroenteritis", "appendicitis", "ulcer", "IBS"],
    "dizziness": ["hypertension", "anemia", "anxiety", "vertigo", "medication_effect"],
    "severe_headache": ["meningitis", "migraine", "hypertension_crisis"],
    "stiff_neck": ["meningitis", "muscle_strain"],
    "rash": ["allergic_reaction", "measles", "chickenpox", "eczema"],
    "joint_pain": ["arthritis", "viral_infection", "dengue", "injury"],
    "muscle_weakness": ["diabetes", "anemia", "neurological_disorder"],
    "persistent_cough": ["tuberculosis", "asthma", "pneumonia", "lung_disease"],
    "blood_in_cough": ["tuberculosis", "pneumonia", "severe_bronchitis"],
    "palpitations": ["cardiac_arrhythmia", "anxiety", "hyperthyroidism"],
    "high_blood_pressure": ["hypertension", "stress", "kidney_disease"],
    "low_blood_pressure": ["dehydration", "anemia", "medication_effect"],
}

# Critical symptoms that indicate HIGH RISK
CRITICAL_SYMPTOMS = {
    "chest_pain": 10,
    "breathing_difficulty": 10,
    "shortness_of_breath": 10,
    "severe_headache": 9,
    "stiff_neck": 9,
    "blood_in_cough": 9,
    "loss_of_consciousness": 10,
    "severe_abdominal_pain": 10,
    "palpitations": 8,
}

# Moderate symptoms that may indicate MEDIUM RISK
MODERATE_SYMPTOMS = {
    "fever": 5,
    "persistent_cough": 5,
    "high_blood_pressure": 5,
    "body_ache": 4,
    "severe_headache": 4,
}

# Common symptoms that typically indicate LOW RISK
COMMON_SYMPTOMS = {
    "cough": 2,
    "sore_throat": 2,
    "headache": 2,
    "nausea": 2,
    "diarrhea": 2,
    "dizziness": 2,
    "fatigue": 1,
}

# Symptom normalization mapping (handle variations)
SYMPTOM_ALIASES = {
    "chest_pain": ["chest pain", "chest ache", "cardiac pain"],
    "breathing_difficulty": ["breathing difficulty", "difficulty breathing", "trouble breathing", "dyspnea"],
    "shortness_of_breath": ["shortness of breath", "breathlessness", "SOB"],
    "body_ache": ["body ache", "body pain", "myalgia"],
    "sore_throat": ["sore throat", "throat pain", "pharyngitis"],
    "loss_of_taste": ["loss of taste", "ageusia"],
    "loss_of_smell": ["loss of smell", "anosmia"],
    "persistent_cough": ["persistent cough", "chronic cough"],
    "blood_in_cough": ["blood in cough", "hemoptysis"],
    "severe_headache": ["severe headache", "migraine", "thunderclap headache"],
    "stiff_neck": ["stiff neck", "neck stiffness", "nuchal rigidity"],
    "abdominal_pain": ["abdominal pain", "stomach pain", "belly pain"],
    "high_blood_pressure": ["high blood pressure", "hypertension", "elevated BP"],
    "low_blood_pressure": ["low blood pressure", "hypotension", "low BP"],
}
