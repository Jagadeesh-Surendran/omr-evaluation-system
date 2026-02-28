#!/usr/bin/env python3
"""Create a realistic test question paper with answer key"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_realistic_question_paper():
    """Create a realistic question paper image with clear answer key"""
    
    # Create larger white image
    img = Image.new('RGB', (1200, 1600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a better font
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        heading_font = ImageFont.truetype("arial.ttf", 28)
        text_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Add title
    draw.text((400, 50), "SAMPLE QUESTION PAPER", fill='black', font=title_font)
    draw.text((450, 100), "SET A", fill='black', font=heading_font)
    
    # Add a line
    draw.line([(100, 150), (1100, 150)], fill='black', width=2)
    
    # Add answer key section
    draw.text((100, 180), "ANSWER KEY - SET A", fill='black', font=heading_font)
    draw.line([(100, 220), (1100, 220)], fill='black', width=1)
    
    # Add answer key in clear format
    answers = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A',
        6: 'B', 7: 'C', 8: 'D', 9: 'A', 10: 'B',
        11: 'C', 12: 'D', 13: 'A', 14: 'B', 15: 'C',
        16: 'D', 17: 'A', 18: 'B', 19: 'C', 20: 'D'
    }
    
    y = 260
    x_left = 150
    x_right = 650
    
    for i, (q_num, answer) in enumerate(answers.items()):
        if i < 10:
            # Left column
            text = f"{q_num}. {answer}"
            draw.text((x_left, y + (i * 40)), text, fill='black', font=text_font)
        else:
            # Right column
            text = f"{q_num}. {answer}"
            draw.text((x_right, y + ((i-10) * 40)), text, fill='black', font=text_font)
    
    # Add some sample questions below
    y_questions = 700
    draw.text((100, y_questions), "QUESTIONS:", fill='black', font=heading_font)
    
    sample_questions = [
        "1. What is the capital of France?",
        "   A) London  B) Paris  C) Berlin  D) Madrid",
        "",
        "2. Which planet is known as the Red Planet?",
        "   A) Venus  B) Mars  C) Jupiter  D) Saturn",
        "",
        "3. What is 2 + 2?",
        "   A) 3  B) 4  C) 5  D) 6",
    ]
    
    y_q = y_questions + 50
    for line in sample_questions:
        draw.text((120, y_q), line, fill='black', font=text_font)
        y_q += 35
    
    # Save
    output_path = 'realistic_question_paper.jpg'
    img.save(output_path, quality=95)
    print(f"Created: {output_path}")
    return output_path

if __name__ == "__main__":
    create_realistic_question_paper()
