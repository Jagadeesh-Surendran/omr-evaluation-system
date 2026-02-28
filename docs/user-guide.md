# AI Question Solver User Guide

## Introduction

The AI Question Solver automatically generates answer keys from question bank PDFs using artificial intelligence. This guide will help you understand how to use the system effectively, interpret confidence scores, review AI-generated answers, and export answer keys for use in OMR evaluation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Question Banks](#uploading-question-banks)
3. [Understanding the Processing](#understanding-the-processing)
4. [Reviewing AI-Generated Answers](#reviewing-ai-generated-answers)
5. [Understanding Confidence Scores](#understanding-confidence-scores)
6. [Validation Flags and Issues](#validation-flags-and-issues)
7. [Correcting Answers](#correcting-answers)
8. [Managing Sessions](#managing-sessions)
9. [Approving Answer Keys](#approving-answer-keys)
10. [Exporting Answer Keys](#exporting-answer-keys)
11. [Using Answer Keys for OMR Evaluation](#using-answer-keys-for-omr-evaluation)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before using the AI Question Solver, ensure:

1. You have an active account with appropriate permissions
2. Your question bank is in PDF format
3. The PDF contains clear, readable questions with multiple-choice options (A-E)
4. Questions are numbered sequentially

### System Requirements

- **Supported PDF Types**: Digital PDFs, scanned PDFs, or mixed
- **Question Format**: Multiple-choice with 3-5 options (A, B, C, D, E)
- **Maximum Questions**: Up to 500 questions per session
- **File Size**: Up to 50 MB per PDF

---

## Uploading Question Banks

### Step 1: Access the Upload Interface

1. Navigate to the AI Question Solver section
2. Click the "Upload Question Bank" button
3. Select your PDF file from your computer

### Step 2: Document Classification

After upload, the system automatically analyzes your PDF to determine if it contains:
- **Question Bank**: Questions with options but no answers
- **Answer Key**: A document with answers already marked

**High Confidence Classification** (≥ 0.7):
- The system automatically proceeds with the detected type
- You'll see a message like: "Document classified as Question Bank (95% confidence)"

**Low Confidence Classification** (< 0.7):
- The system asks you to manually confirm the document type
- Select "Question Bank" if your PDF contains questions to be solved
- Select "Answer Key" if your PDF already has answers (the system will extract them instead)

### Step 3: Question Extraction

Once classification is complete, the system extracts all questions from your PDF:
- Question numbers and text
- All answer options (A-E)
- Images or diagrams associated with questions
- Page references

You'll see a progress indicator showing extraction status.

---

## Understanding the Processing

### Processing Stages

1. **Document Classification** (5-10 seconds)
   - Analyzes PDF structure
   - Determines document type

2. **Question Extraction** (30-60 seconds for 100 questions)
   - Converts PDF pages to images
   - Extracts question text and options
   - Detects images and diagrams

3. **AI Solving** (30-50 minutes for 100 questions)
   - Each question is analyzed by an AI model
   - AI selects the correct answer
   - AI provides an explanation
   - Confidence score is calculated

4. **Validation** (1-2 seconds)
   - Checks answer consistency
   - Flags low-confidence answers
   - Detects potential issues

### Real-Time Progress

During processing, you'll see:
- **Current Question**: Which question is being processed
- **Progress Bar**: Visual indicator of completion percentage
- **Time Estimates**: Elapsed time and estimated remaining time
- **Processing Rate**: Questions per minute
- **Average Confidence**: Overall confidence across solved questions

### Processing Speed

- **Text-Only Questions**: ~2 questions per minute
- **Questions with Images**: ~1 question per minute
- **100 Question Bank**: ~30-50 minutes total
- **500 Question Bank**: ~2.5-4 hours total

---

## Reviewing AI-Generated Answers

### Question List View

After processing completes, you'll see a list of all questions with:

**Question Information**:
- Question number
- Question text (truncated)
- Question type icon (📐 math, 🧩 logical, 📚 factual, 🖼️ visual)

**Answer Information**:
- Selected answer option (A, B, C, D, or E)
- Confidence score with color coding
- Status badges (✓ Solved, ⚠️ Low Confidence, ❌ Unsolvable, ✏️ Manually Verified)

**Visual Indicators**:
- 🟢 Green: High confidence (0.8-1.0)
- 🟡 Yellow: Medium confidence (0.6-0.79)
- 🔴 Red: Low confidence (0.0-0.59)
- ⚠️ Warning icon: Flagged for review
- ✏️ Pencil icon: Manually corrected

### Question Detail View

Click any question to see full details:

**Question Section**:
- Complete question text with formatting
- All answer options (A-E)
- Question images or diagrams (if present)
- Page number reference

**Answer Section**:
- AI-selected answer highlighted
- Detailed explanation from AI
- Confidence score with breakdown
- Processing time

**Validation Section**:
- Any validation issues detected
- Uncertainty indicators in explanation
- Consistency checks with other questions

---

## Understanding Confidence Scores

### What is a Confidence Score?

A confidence score (0.0 to 1.0) indicates how certain the AI is about its answer. The score is calculated based on:

1. **Explanation Quality**: Detailed, specific explanations = higher confidence
2. **Uncertainty Indicators**: Phrases like "possibly" or "might be" = lower confidence
3. **Processing Time**: Very fast or very slow = lower confidence
4. **Model Certainty**: AI's internal confidence assessment

### Confidence Categories

| Score Range | Category | Color | Meaning |
|-------------|----------|-------|---------|
| 0.8 - 1.0 | High | 🟢 Green | AI is very confident; likely correct |
| 0.6 - 0.79 | Medium | 🟡 Yellow | AI is moderately confident; review recommended |
| 0.0 - 0.59 | Low | 🔴 Red | AI is uncertain; manual review required |

### Interpreting Confidence Scores

**High Confidence (0.8-1.0)**:
- The AI provided a clear, detailed explanation
- No uncertainty phrases detected
- Answer is likely correct
- Quick review recommended

**Medium Confidence (0.6-0.79)**:
- The AI has some uncertainty
- Explanation may lack detail
- Review the question and explanation
- Verify the answer is reasonable

**Low Confidence (0.0-0.59)**:
- The AI is uncertain about the answer
- Explanation may contain uncertainty phrases
- **Manual review is mandatory**
- Consider the question complexity or ambiguity

### Example Confidence Scores

**High Confidence Example** (0.95):
```
Question: What is 2 + 2?
Answer: B (4)
Explanation: "2 + 2 equals 4, which is option B. This is a basic arithmetic operation."
```

**Medium Confidence Example** (0.72):
```
Question: Which country has the largest population?
Answer: C (China)
Explanation: "China has historically had the largest population, though India is close."
```

**Low Confidence Example** (0.45):
```
Question: What is the best programming language?
Answer: A (Python)
Explanation: "This is subjective, but Python is possibly the most popular for beginners."
```

---

## Validation Flags and Issues

### Types of Validation Issues

The system automatically flags questions with potential problems:

**1. Low Confidence** (🔴 Red Flag)
- Confidence score below 0.6
- **Action Required**: Manual review mandatory

**2. Uncertainty Detected** (⚠️ Warning)
- Explanation contains phrases like "possibly", "might be", "unclear", "not sure"
- **Action Required**: Verify the answer

**3. Explanation Mismatch** (⚠️ Warning)
- Explanation discusses a different option than selected
- **Action Required**: Check for AI confusion

**4. Duplicate Question Inconsistency** (⚠️ Warning)
- Same question appears multiple times with different answers
- **Action Required**: Verify which answer is correct

**5. Invalid Option** (🔴 Critical)
- Selected option doesn't exist in the question
- **Action Required**: Report as bug; manually select correct answer

**6. Unsolvable** (❌ Error)
- AI could not determine an answer
- **Action Required**: Manually provide the answer

**7. Timeout** (⏱️ Error)
- Processing exceeded 30 seconds
- **Action Required**: Retry or manually provide answer

**8. Parse Failed** (❌ Error)
- Question could not be extracted from PDF
- **Action Required**: Check PDF quality; manually add question

### Validation Report

The validation report summarizes all issues:
- Total questions processed
- Number of flagged questions
- List of all validation issues with severity
- Average confidence score

**Severity Levels**:
- **Critical**: Must be fixed before approval
- **Warning**: Should be reviewed
- **Info**: Informational only

---

## Correcting Answers

### When to Correct Answers

Correct an answer when:
- Confidence score is low (< 0.6)
- Validation flags indicate an issue
- You know the AI answer is incorrect
- Explanation doesn't match the selected answer

### How to Correct an Answer

1. **Open Question Detail View**: Click the question in the list
2. **Review Current Answer**: Check the AI-selected option and explanation
3. **Select New Answer**: Choose the correct option from the dropdown or radio buttons
4. **Add Reason (Optional)**: Explain why you're correcting the answer
5. **Save Correction**: Click "Save" or "Update Answer"

### After Correction

Once corrected:
- Answer is marked as "Manually Verified" with ✏️ icon
- Confidence score is set to 1.0 (maximum)
- Original AI answer is preserved for reference
- Correction is tracked in the session history
- Export formats will indicate the answer was modified

### Adding Notes

You can add notes to any question:
1. Click "Add Note" in the question detail view
2. Enter your comment or observation
3. Notes are saved with the session
4. Notes appear in exports and reports

**Example Notes**:
- "Question wording is ambiguous"
- "Image quality is poor; difficult to read"
- "Verified answer with subject matter expert"

---

## Managing Sessions

### Session Controls

**Pause Session**:
- Click "Pause" to temporarily stop processing
- All progress is automatically saved
- Resume anytime to continue from where you left off
- Useful for long sessions or when you need a break

**Resume Session**:
- Click "Resume" to continue a paused session
- Processing continues from the next unprocessed question
- All previous results are preserved

**Cancel Session**:
- Click "Cancel" to stop processing permanently
- Partial results are discarded (not saved)
- Use when you uploaded the wrong file or want to start over
- **Warning**: This action cannot be undone

### Session Status

| Status | Description | Available Actions |
|--------|-------------|-------------------|
| Pending | Session created, not yet started | Start, Cancel |
| Processing | AI is actively solving questions | Pause, Cancel |
| Paused | Processing temporarily stopped | Resume, Cancel |
| Completed | All questions processed | Review, Approve, Export |
| Cancelled | Session terminated by user | None (view only) |
| Error | Critical error occurred | View error log, Retry |

### Viewing Previous Sessions

Access your session history:
1. Navigate to "Session History" or "My Sessions"
2. View list of all past sessions with:
   - Session ID
   - PDF filename
   - Date and time
   - Status
   - Number of questions
   - Average confidence
3. Click any session to view details or export results

---

## Approving Answer Keys

### Approval Requirements

Before approving an answer key:

✅ **All flagged questions must be reviewed**
- Low confidence questions verified
- Validation warnings addressed
- Unsolvable questions manually answered

✅ **Administrator privileges required**
- Only users with admin role can approve
- Approval is logged with user ID and timestamp

✅ **Session must be completed**
- All questions processed
- No errors or timeouts pending

### Approval Process

1. **Review Flagged Questions**: Address all validation issues
2. **Verify Statistics**: Check average confidence and correction count
3. **Click "Approve Answer Key"**: Button appears when requirements met
4. **Confirm Approval**: Review summary and confirm
5. **Add Comments (Optional)**: Document approval decision

### After Approval

Once approved:
- Answer key is marked as **immutable** (cannot be modified)
- Approval metadata is recorded (who, when, comments)
- Answer key is ready for use in OMR evaluation
- Any future changes create a new version

### Approval Metadata

Approved answer keys include:
- Approved by: User ID of approver
- Approved at: Timestamp of approval
- Comments: Approval notes
- Version: Version number if multiple approvals

---

## Exporting Answer Keys

### Export Formats

The system supports three export formats:

**1. JSON Format** (for OMR system integration)
- Machine-readable format
- Compatible with existing OMR evaluation
- Includes metadata and unsolvable list

**2. CSV Format** (for spreadsheet analysis)
- Human-readable tabular format
- Columns: question_number, correct_answer, confidence, explanation, modified
- Open in Excel, Google Sheets, or any spreadsheet software

**3. PDF Report** (for printing and archiving)
- Visual report with all questions and answers
- Answers highlighted in the original question format
- Includes confidence scores and flags
- Suitable for printing and distribution

### How to Export

1. **Navigate to Export Section**: In the session detail view
2. **Select Format**: Choose JSON, CSV, or PDF
3. **Click Export**: Download begins automatically
4. **Save File**: Choose location on your computer

### Export Contents

**JSON Export**:
```json
{
  "answer_key": {
    "0": 1,  // Question 1 → Answer B (0-based index)
    "1": 0,  // Question 2 → Answer A
    "2": 3   // Question 3 → Answer D
  },
  "metadata": {
    "total_questions": 100,
    "solved_count": 95,
    "unsolvable_count": 3,
    "manual_corrections": 2,
    "average_confidence": 0.82,
    "approved": true
  },
  "unsolvable": [23, 67, 89],
  "low_confidence": [15, 42, 78]
}
```

**CSV Export**:
```
question_number,correct_answer,confidence,explanation,modified
1,B,0.95,"2 + 2 equals 4",false
2,A,0.88,"Capital of France is Paris",false
15,C,1.00,"Corrected by user",true
```

**PDF Report**:
- Cover page with metadata
- Each question on separate page or section
- Correct answer highlighted
- Confidence scores displayed
- Flags and notes included

### Manual Correction Indicators

All export formats indicate which answers were manually corrected:
- **JSON**: Tracked in metadata
- **CSV**: "modified" column shows true/false
- **PDF**: ✏️ icon next to corrected answers

---

## Using Answer Keys for OMR Evaluation

### Direct Integration

Use the generated answer key directly for OMR evaluation:

1. **Complete and Approve**: Ensure answer key is approved
2. **Navigate to OMR Evaluation**: Go to the evaluation section
3. **Select "Use AI-Generated Answer Key"**: Choose your session
4. **Upload Student Responses**: Upload the student answer sheet PDF
5. **Start Evaluation**: System uses your answer key automatically

### Manual Integration

Alternatively, export and upload manually:

1. **Export as JSON**: Download the JSON format
2. **Navigate to OMR Evaluation**: Go to the evaluation section
3. **Upload Answer Key**: Upload the JSON file
4. **Upload Student Responses**: Upload student answer sheets
5. **Start Evaluation**: System processes as normal

### Verification

Before using for actual evaluation:
- Test with a sample student response
- Verify answer key format is correct
- Check that all questions are mapped properly
- Confirm unsolvable questions are handled correctly

---

## Best Practices

### Before Upload

✅ **Prepare Your PDF**:
- Ensure questions are clearly numbered
- Verify all options are visible and readable
- Check that images are clear and not pixelated
- Remove any password protection

✅ **Check PDF Quality**:
- Digital PDFs work best
- Scanned PDFs should be high resolution (300 DPI minimum)
- Avoid handwritten questions (OCR may fail)

### During Processing

✅ **Monitor Progress**:
- Keep the browser tab open during processing
- Check progress updates periodically
- Note any questions with errors or timeouts

✅ **Use Pause for Long Sessions**:
- Pause if you need to close your browser
- Resume later from the same point
- Progress is automatically saved every 10 questions

### During Review

✅ **Prioritize Flagged Questions**:
- Review all low-confidence answers first
- Address validation warnings
- Verify unsolvable questions manually

✅ **Use Filters Effectively**:
- Filter by "Low Confidence" to see priority items
- Filter by "Flagged" to see validation issues
- Filter by "Unsolvable" to see questions needing manual answers

✅ **Add Notes for Context**:
- Document why you corrected an answer
- Note any ambiguous questions
- Record issues for future question bank improvements

### Before Approval

✅ **Final Checks**:
- All flagged questions reviewed
- Average confidence is acceptable (> 0.7 recommended)
- Manual corrections are documented
- Statistics look reasonable

✅ **Verify Critical Questions**:
- Spot-check high-value questions
- Verify questions on difficult topics
- Double-check questions with images

### After Approval

✅ **Export and Backup**:
- Export in all formats for redundancy
- Store exports in a secure location
- Keep PDF report for archival purposes

✅ **Test Before Use**:
- Test with sample student responses
- Verify OMR integration works correctly
- Confirm all questions are evaluated properly

---

## Troubleshooting

### Common Issues

**Issue: PDF Upload Fails**
- **Cause**: File is too large, corrupted, or password-protected
- **Solution**: 
  - Check file size (max 50 MB)
  - Try opening PDF in a reader to verify it's not corrupted
  - Remove password protection
  - Try re-saving the PDF

**Issue: Low Classification Confidence**
- **Cause**: Document structure is ambiguous
- **Solution**: 
  - Manually select "Question Bank" when prompted
  - Ensure your PDF has clear question numbers and options
  - Check that there are no answer indicators in the document

**Issue: Question Extraction Incomplete**
- **Cause**: Poor PDF quality, unusual formatting, or OCR failure
- **Solution**: 
  - Check the error log for specific pages that failed
  - Verify PDF quality and readability
  - Manually add missing questions after processing

**Issue: Many Low Confidence Answers**
- **Cause**: Questions are ambiguous, complex, or outside AI's knowledge
- **Solution**: 
  - Review and correct low-confidence answers manually
  - Consider if questions are clearly worded
  - Check if questions require specialized domain knowledge

**Issue: AI Selects Wrong Answers**
- **Cause**: Question ambiguity, AI limitations, or incorrect options
- **Solution**: 
  - Manually correct the answers
  - Add notes explaining the correct reasoning
  - Consider revising ambiguous questions in future

**Issue: Processing is Very Slow**
- **Cause**: High server load, complex questions, or many images
- **Solution**: 
  - Be patient; processing takes time (2 questions/minute average)
  - Use pause/resume if you need to close your browser
  - Check system status for any service issues

**Issue: Session Stuck or Frozen**
- **Cause**: Network issue, server error, or timeout
- **Solution**: 
  - Refresh the page and check session status
  - Session state is saved every 10 questions
  - Resume from last checkpoint if needed
  - Contact support if issue persists

**Issue: Cannot Approve Answer Key**
- **Cause**: Flagged questions not reviewed or insufficient privileges
- **Solution**: 
  - Review all flagged questions first
  - Ensure you have administrator role
  - Check that session is completed (not paused or processing)

**Issue: Export Fails**
- **Cause**: Session not completed, server error, or large file size
- **Solution**: 
  - Ensure session is completed
  - Try different export format
  - Check browser console for errors
  - Contact support if issue persists

### Getting Help

**Documentation**:
- API Documentation: `/docs/api/ai-question-solver-api.md`
- Troubleshooting Guide: `/docs/troubleshooting.md`
- Deployment Guide: `/docs/deployment.md`

**Support Channels**:
- Email: support@example.com
- GitHub Issues: [repository-url]/issues
- User Forum: [forum-url]

**Reporting Bugs**:
When reporting issues, include:
- Session ID
- PDF filename (if applicable)
- Steps to reproduce
- Error messages or screenshots
- Browser and operating system

---

## Glossary

- **Answer Key**: A mapping of question numbers to correct answer options
- **Confidence Score**: A value (0.0-1.0) indicating AI certainty in an answer
- **Flagged Question**: A question marked for review due to low confidence or validation issues
- **Manual Correction**: A user-provided answer that overrides the AI answer
- **Question Bank**: A PDF containing questions without answers
- **Session**: A complete processing cycle from upload to export
- **Solver**: The AI component that analyzes and answers questions
- **Unsolvable**: A question the AI cannot answer with reasonable confidence
- **Validation**: Automated checks for answer consistency and quality

---

## Appendix: Question Type Icons

| Icon | Type | Description |
|------|------|-------------|
| 📐 | Math | Mathematical questions (arithmetic, algebra, geometry, calculus) |
| 🧩 | Logical | Logical reasoning (patterns, sequences, deductions) |
| 📚 | Factual | General knowledge and factual questions |
| 🖼️ | Visual | Questions with images, diagrams, or charts |

---

**Last Updated**: January 2024  
**Version**: 1.0
