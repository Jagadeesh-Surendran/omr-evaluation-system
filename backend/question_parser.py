"""
Question Parser module for extracting questions from PDF documents.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import os
import re
import fitz  # PyMuPDF
import logging
from solver_logging_config import get_logger

logger = get_logger("question_parser")


@dataclass
class QuestionOption:
    """Represents a single answer option."""
    label: str  # A, B, C, D, E
    text: str
    has_image: bool = False
    image_data: Optional[bytes] = None


@dataclass
class Question:
    """Represents an extracted question."""
    number: int
    text: str
    options: List[QuestionOption]
    page_number: int
    has_image: bool = False
    image_data: Optional[bytes] = None
    question_type: Optional[str] = None  # math, logical, factual, visual


@dataclass
class DocumentClassification:
    """Result of document type detection."""
    doc_type: str  # "question_bank" or "answer_key"
    confidence: float  # 0.0 to 1.0
    reasoning: str


class QuestionParser:
    """Extracts questions from PDF documents."""
    
    def __init__(self):
        self.logger = logger
    
    def classify_document(self, pdf_path: str) -> DocumentClassification:
        """
        Analyzes first 3 pages to determine document type.
        Returns classification with confidence score.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        self.logger.info(f"[CLASSIFY] Starting document classification: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            pages_to_analyze = min(3, len(doc))
            
            # Extract text from first 3 pages
            text_content = ""
            for page_num in range(pages_to_analyze):
                page = doc[page_num]
                text_content += page.get_text()
            
            doc.close()
            
            # Pattern detection
            question_patterns = 0
            answer_key_patterns = 0
            
            # Look for question patterns: "Q1.", "Q2.", "1.", "2.", etc.
            question_matches = re.findall(r'(?:Q\d+\.|\d+\.)\s+[A-Z]', text_content)
            question_patterns += len(question_matches)
            
            # Look for option patterns: "A.", "B.", "C.", "D.", "E."
            option_matches = re.findall(r'[A-E]\.\s+\w', text_content)
            question_patterns += len(option_matches) // 3  # Assume at least 3 options per question
            
            # Look for answer key patterns: "1:A", "1-A", "1) A", "Answer: A"
            answer_key_matches = re.findall(
                r'(?:\d+[:)\-]\s*[A-E]|Answer\s*[:=]\s*[A-E]|Correct\s*[:=]\s*[A-E])',
                text_content,
                re.IGNORECASE
            )
            answer_key_patterns += len(answer_key_matches)
            
            # Look for filled bubble indicators (●, ⬤, ⚫)
            filled_bubble_matches = re.findall(r'[●⬤⚫]', text_content)
            answer_key_patterns += len(filled_bubble_matches)
            
            # Determine document type based on pattern counts
            total_patterns = question_patterns + answer_key_patterns
            
            if total_patterns == 0:
                # No clear patterns found
                doc_type = "question_bank"  # Default assumption
                confidence = 0.3
                reasoning = "No clear question or answer key patterns detected. Defaulting to question bank."
            elif answer_key_patterns > question_patterns * 0.5:
                # More answer key patterns than question patterns
                doc_type = "answer_key"
                confidence = min(0.9, 0.5 + (answer_key_patterns / total_patterns))
                reasoning = f"Detected {answer_key_patterns} answer key indicators vs {question_patterns} question indicators."
            else:
                # More question patterns
                doc_type = "question_bank"
                confidence = min(0.9, 0.5 + (question_patterns / total_patterns))
                reasoning = f"Detected {question_patterns} question indicators vs {answer_key_patterns} answer key indicators."
            
            self.logger.info(
                f"[CLASSIFY] Result: {doc_type} (confidence: {confidence:.2f}) - {reasoning}"
            )
            
            return DocumentClassification(
                doc_type=doc_type,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"[CLASSIFY] Error during classification: {e}")
            raise ValueError(f"Document classification failed: {e}")
    
    def extract_questions(self, pdf_path: str) -> List[Question]:
        """
        Extracts all questions from a question bank PDF.
        Returns list of Question objects with metadata.
        Handles multi-page questions and image content.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.logger.info(f"[EXTRACT] Starting question extraction: {pdf_path}")
        
        questions = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Extract questions from this page
                page_questions = self._extract_questions_from_text(text, page_num + 1)
                questions.extend(page_questions)
            
            doc.close()
            
            self.logger.info(f"[EXTRACT] Extracted {len(questions)} questions")
            return questions
            
        except Exception as e:
            self.logger.error(f"[EXTRACT] Error during extraction: {e}")
            raise ValueError(f"Question extraction failed: {e}")
    
    def _extract_questions_from_text(self, text: str, page_number: int) -> List[Question]:
        """Extract questions from page text."""
        questions = []
        
        # Pattern to match questions: Q1. or 1. followed by text
        question_pattern = r'(?:Q)?(\d+)\.\s+(.+?)(?=(?:Q)?\d+\.|$)'
        matches = re.findall(question_pattern, text, re.DOTALL)
        
        for match in matches:
            question_num = int(match[0])
            question_text = match[1].strip()
            
            # Extract options from question text
            options = self._extract_options(question_text)
            
            if options:  # Only add if we found options
                # Remove options from question text
                clean_text = self._remove_options_from_text(question_text)
                
                # Detect question type
                question_type = self._detect_question_type_from_text(clean_text)
                
                question = Question(
                    number=question_num,
                    text=clean_text,
                    options=options,
                    page_number=page_number,
                    has_image=False,  # TODO: Implement image detection
                    image_data=None,
                    question_type=question_type
                )
                questions.append(question)
        
        return questions
    
    def _extract_options(self, text: str) -> List[QuestionOption]:
        """Extract answer options from question text."""
        options = []
        
        # Pattern to match options: A. text, B. text, etc.
        option_pattern = r'([A-E])\.\s+(.+?)(?=[A-E]\.|$)'
        matches = re.findall(option_pattern, text, re.DOTALL)
        
        for match in matches:
            label = match[0]
            option_text = match[1].strip()
            
            option = QuestionOption(
                label=label,
                text=option_text,
                has_image=False,
                image_data=None
            )
            options.append(option)
        
        return options
    
    def _remove_options_from_text(self, text: str) -> str:
        """Remove option text from question text."""
        # Remove everything after the first option
        option_start = re.search(r'[A-E]\.', text)
        if option_start:
            return text[:option_start.start()].strip()
        return text.strip()
    
    def _detect_question_type(self, question: Question) -> str:
        """
        Analyzes question text to determine type.
        Returns: "math", "logical", "factual", or "visual"
        """
        return self._detect_question_type_from_text(question.text)
    
    def _detect_question_type_from_text(self, text: str) -> str:
        """Detect question type from text content."""
        text_lower = text.lower()
        
        # Math keywords
        math_keywords = [
            'calculate', 'compute', 'value', 'sum', 'difference', 'product',
            'quotient', 'equation', 'solve', 'algebra', 'geometry', 'calculus',
            '+', '-', '×', '÷', '=', 'x', 'y'
        ]
        
        # Logical keywords
        logical_keywords = [
            'pattern', 'sequence', 'next', 'follows', 'logic', 'reasoning',
            'deduce', 'infer', 'conclude', 'if', 'then', 'therefore'
        ]
        
        # Count keyword matches
        math_count = sum(1 for keyword in math_keywords if keyword in text_lower)
        logical_count = sum(1 for keyword in logical_keywords if keyword in text_lower)
        
        if math_count > logical_count:
            return "math"
        elif logical_count > 0:
            return "logical"
        else:
            return "factual"
