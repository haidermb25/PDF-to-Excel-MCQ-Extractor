# PDF-to-Excel MCQ Extractor

## About

PDF-to-Excel MCQ Extractor is a Python Tkinter desktop application that automatically extracts Multiple Choice Questions (MCQs) from PDF documents and converts them into structured Excel spreadsheets. The application parses questions, options, answers, explanations, question types (Radio/Checkbox), and images, making it easy to manage and reuse question banks.

## Features

- Extract MCQs from PDF files
- Parse questions and options automatically
- Detect correct answers
- Extract explanations
- Identify Radio and Checkbox question types
- Support image extraction and references
- Generate structured Excel files
- Split output into batches of 100 MCQs per Excel file
- Simple and user-friendly Tkinter interface

## Technologies Used

- Python
- Tkinter
- OpenPyXL
- Pandas
- Regular Expressions (Regex)
- PDF Processing Libraries

## Output Format

| Column | Description |
|----------|-------------|
| Question | MCQ statement |
| Option A | First option |
| Option B | Second option |
| Option C | Third option |
| Option D | Fourth option |
| Answer | Correct answer |
| Explanation | Answer explanation |
| Question Type | Radio/Checkbox |
| Image | Image reference/path |

## How It Works

1. Select a PDF file.
2. The application reads and parses MCQs.
3. Questions, options, answers, explanations, and images are extracted.
4. Data is organized into a structured format.
5. Excel files are generated automatically.
6. Each Excel file contains up to 100 MCQs.

## Use Cases

- Question Bank Creation
- E-Learning Platforms
- LMS Content Preparation
- Educational Data Migration
- Exam Management Systems

## Author

**Ali Haider**
Software Engineer
AI & Machine Learning Enthusiast
