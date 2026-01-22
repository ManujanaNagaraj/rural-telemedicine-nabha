"""
AI-based Symptom Checker Module
================================

This module provides decision support for symptom assessment in the Rural Telemedicine Platform.

IMPORTANT: This is NOT a medical diagnosis system. It is a DECISION-SUPPORT TOOL ONLY.
Results should be reviewed by qualified healthcare professionals.

Components:
    - symptoms_data: Symptom-to-condition mappings
    - rule_engine: Rule-based evaluation engine for symptom analysis
"""

from .rule_engine import evaluate_symptoms

__all__ = ['evaluate_symptoms']
