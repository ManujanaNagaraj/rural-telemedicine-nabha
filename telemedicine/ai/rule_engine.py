"""
Rule-Based Symptom Evaluation Engine

This module provides the core logic for evaluating reported symptoms and
generating risk assessments and next-step recommendations.

DISCLAIMER: This engine is a DECISION-SUPPORT TOOL ONLY. 
It does NOT diagnose medical conditions. All assessments should be reviewed
by qualified healthcare professionals.
"""

from typing import Dict, List, Tuple
from .symptoms_data import (
    SYMPTOM_CONDITIONS_MAP,
    CRITICAL_SYMPTOMS,
    MODERATE_SYMPTOMS,
    COMMON_SYMPTOMS,
    SYMPTOM_ALIASES,
)


def normalize_symptom(symptom: str) -> str:
    """
    Normalize symptom string by converting to lowercase, removing extra spaces,
    and replacing spaces with underscores. Handles aliases.
    
    Args:
        symptom (str): Raw symptom input
        
    Returns:
        str: Normalized symptom key
    """
    if not symptom:
        return ""
    
    # Clean input
    cleaned = symptom.strip().lower().replace(" ", "_")
    
    # Check if it's already a valid symptom key
    if cleaned in SYMPTOM_CONDITIONS_MAP:
        return cleaned
    
    # Check aliases
    for canonical_key, aliases in SYMPTOM_ALIASES.items():
        for alias in aliases:
            if alias.lower().replace(" ", "_") == cleaned:
                return canonical_key
    
    return cleaned


def calculate_risk_score(symptoms: List[str]) -> int:
    """
    Calculate overall risk score based on symptom severity.
    
    Args:
        symptoms (List[str]): List of normalized symptom keys
        
    Returns:
        int: Risk score (0-100)
    """
    if not symptoms:
        return 0
    
    score = 0
    
    for symptom in symptoms:
        if symptom in CRITICAL_SYMPTOMS:
            score += CRITICAL_SYMPTOMS[symptom] * 8
        elif symptom in MODERATE_SYMPTOMS:
            score += MODERATE_SYMPTOMS[symptom] * 4
        elif symptom in COMMON_SYMPTOMS:
            score += COMMON_SYMPTOMS[symptom] * 2
        else:
            # Unknown symptoms get minimal score
            score += 1
    
    # Boost score if multiple critical symptoms
    critical_count = sum(1 for s in symptoms if s in CRITICAL_SYMPTOMS)
    if critical_count >= 2:
        score += critical_count * 15
    
    # Cap at 100
    return min(score, 100)


def determine_risk_level(score: int) -> str:
    """
    Convert risk score to risk level.
    
    Args:
        score (int): Risk score (0-100)
        
    Returns:
        str: Risk level (LOW / MEDIUM / HIGH)
    """
    if score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    else:
        return "LOW"


def match_conditions(symptoms: List[str]) -> Dict[str, int]:
    """
    Match reported symptoms to potential conditions and count occurrences.
    
    Args:
        symptoms (List[str]): List of normalized symptom keys
        
    Returns:
        Dict[str, int]: Conditions with match frequency count
    """
    condition_matches = {}
    
    for symptom in symptoms:
        if symptom in SYMPTOM_CONDITIONS_MAP:
            for condition in SYMPTOM_CONDITIONS_MAP[symptom]:
                condition_matches[condition] = condition_matches.get(condition, 0) + 1
    
    return condition_matches


def get_advisory_message(risk_level: str, matched_conditions: Dict[str, int]) -> str:
    """
    Generate advisory message based on risk level and conditions.
    
    Args:
        risk_level (str): Risk level (LOW / MEDIUM / HIGH)
        matched_conditions (Dict[str, int]): Matched conditions
        
    Returns:
        str: Advisory message for the user
    """
    messages = {
        "HIGH": (
            "⚠️ HIGH RISK: Your symptoms suggest a potentially serious condition requiring URGENT medical attention. "
            "Please seek immediate care at a healthcare facility or emergency room. Do NOT delay seeking professional help."
        ),
        "MEDIUM": (
            "⚠️ MEDIUM RISK: Your symptoms require professional medical evaluation. "
            "Please schedule an appointment with a healthcare provider soon. If symptoms worsen, seek urgent care."
        ),
        "LOW": (
            "✓ LOW RISK: Your symptoms appear mild. Monitor your condition closely. "
            "Seek care if symptoms persist or worsen. Consider consulting a healthcare provider if symptoms continue beyond a few days."
        ),
    }
    
    return messages.get(risk_level, "Please consult a healthcare provider for proper evaluation.")


def evaluate_symptoms(symptoms: List[str]) -> Dict:
    """
    Main function to evaluate a list of reported symptoms.
    
    This function:
    1. Normalizes and validates symptom input
    2. Matches symptoms to potential conditions
    3. Calculates risk score and determines risk level
    4. Generates advisory messages
    
    IMPORTANT: This is a DECISION-SUPPORT TOOL ONLY. Results do NOT constitute
    a medical diagnosis. All findings should be reviewed by qualified healthcare professionals.
    
    Args:
        symptoms (List[str]): List of symptom strings (e.g., ["fever", "cough"])
        
    Returns:
        Dict with keys:
            - status (str): "success" or "error"
            - matched_conditions (List[str]): Conditions that match reported symptoms
            - risk_level (str): Risk assessment (LOW / MEDIUM / HIGH)
            - risk_score (int): Numerical risk score (0-100)
            - advisory_message (str): Guidance for next steps
            - unknown_symptoms (List[str]): Symptoms that couldn't be matched
            - confidence (str): Confidence in assessment (LOW / MEDIUM / HIGH)
    
    Raises:
        ValueError: If symptoms list is empty or None
    """
    
    # Input validation
    if not symptoms:
        return {
            "status": "error",
            "error_code": "EMPTY_SYMPTOMS",
            "message": "No symptoms provided. Please report at least one symptom for evaluation.",
            "matched_conditions": [],
            "risk_level": None,
            "risk_score": 0,
            "advisory_message": None,
            "unknown_symptoms": [],
            "confidence": "NONE",
        }
    
    # Normalize symptoms
    normalized_symptoms = []
    unknown_symptoms = []
    
    for symptom in symptoms:
        if not isinstance(symptom, str):
            unknown_symptoms.append(str(symptom))
            continue
        
        normalized = normalize_symptom(symptom)
        
        # Check if symptom is recognized
        if normalized in SYMPTOM_CONDITIONS_MAP or normalized in CRITICAL_SYMPTOMS or normalized in MODERATE_SYMPTOMS or normalized in COMMON_SYMPTOMS:
            normalized_symptoms.append(normalized)
        else:
            unknown_symptoms.append(symptom)
    
    # If all symptoms are unknown, return error
    if not normalized_symptoms:
        return {
            "status": "error",
            "error_code": "NO_RECOGNIZED_SYMPTOMS",
            "message": f"None of the provided symptoms were recognized: {symptoms}. Please report recognized symptoms.",
            "matched_conditions": [],
            "risk_level": None,
            "risk_score": 0,
            "advisory_message": None,
            "unknown_symptoms": unknown_symptoms,
            "confidence": "NONE",
        }
    
    # Calculate risk score
    risk_score = calculate_risk_score(normalized_symptoms)
    risk_level = determine_risk_level(risk_score)
    
    # Match conditions
    condition_matches = match_conditions(normalized_symptoms)
    
    # Sort conditions by match frequency
    matched_conditions = sorted(
        condition_matches.items(),
        key=lambda x: x[1],
        reverse=True
    )
    matched_conditions_list = [cond for cond, _ in matched_conditions[:5]]  # Top 5 conditions
    
    # Generate advisory message
    advisory_message = get_advisory_message(risk_level, condition_matches)
    
    # Determine confidence level
    if len(matched_conditions) > 0 and len(normalized_symptoms) >= 2:
        confidence = "HIGH"
    elif len(normalized_symptoms) >= 1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "status": "success",
        "matched_conditions": matched_conditions_list,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "advisory_message": advisory_message,
        "unknown_symptoms": unknown_symptoms,
        "confidence": confidence,
        "disclaimer": "This assessment is a DECISION-SUPPORT TOOL ONLY and does NOT constitute medical diagnosis. Please consult qualified healthcare professionals for proper medical evaluation.",
    }
