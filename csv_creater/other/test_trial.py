import pdfplumber
import pandas as pd
import re
from pathlib import Path
from dateparser.search import search_dates

import PyPDF2
import nltk
# nltk.download()
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

# Define a function to extract basic resume info
def extract_resume_data(pdf_path):
    data = {
        "Full Name": "",
        "LinkedIn URL": "",
        "Current Role": "",
        "Education": "",
        "Graduation Year": "",
        "Past Companies": "",
        "Summary": "",
    }

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Normalize text
    text = text.replace('\xa0', ' ')
    print(text)
    print("############################################################################")
    
    # Extract full name (first line often)
    dic = {
        "Contact ": "",
        "連絡先 " : "",
        "联系方式 ": "",
        "연락처 ": "",
    }
    def replace_all(text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text
    match_name = re.search(r"(?i)^(.+?)\n", text)
    match_name = replace_all(match_name.group(1).strip(), dic)
    if match_name:
        data["Full Name"] = match_name


    ############################################################################
    # Step 1: Break text into lines
    lines = text.split("\n")

    # Step 2: Collect education blocks
    education_keywords = [
    "university", "college", "school", "degree", "bachelor", "master", "phd",
    "大学", "学部", "修士", "博士"  # Japanese terms: university, faculty, master's, doctoral
    ]
    education_blocks = []
    current_block = []

    for line in lines:
        if any(keyword in line.lower() for keyword in education_keywords):
            current_block.append(line)
        elif current_block:
            education_blocks.append(" ".join(current_block))
            current_block = []

    # Step 3: Extract dates and associate with blocks
    education_info = []

    for block in education_blocks:
        dates = re.findall(r'\(?(\d{4})\s*[-–]\s*(\d{4})\)?', block)
        if dates:
            start_year, end_year = map(int, dates[0])
        else:
            # fallback: look for any year if no range
            year_matches = re.findall(r'\(?(\d{4})\)?', block)
            if year_matches:
                start_year = end_year = int(year_matches[-1])
            else:
                continue
        education_info.append((start_year, end_year, block.strip()))

    # Step 4: Sort by end year
    education_info.sort(key=lambda x: x[1], reverse=True)

    # Step 5: Print the most recent entry
    latest_education = education_info[0] if education_info else None

    ############################################################################

    match_edu = latest_education


    # # Education
    # print(text)
    # print("NEXT PERSON!!!")
    # match_edu = re.findall(r"(Kyoto University|The University of Tokyo|China Agricultural University|東京大学).*?\(\d{4}", text)
    data["Education"] = match_edu






    # Read the PDF in binary mode
    with open(pdf_path, 'rb') as pdf_path:
        pdf_reader = PyPDF2.PdfReader(pdf_path)
        text = ''

        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

    # Parse the extracted text
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()

    # Customize your summary's length
    summary = summarizer(parser.document, sentences_count=10)
    data["Summary"] = summary

    # LinkedIn
    text = str(summary)
    start_str = "www.linkedin.com"
    end_str = "(LinkedIn)"
    start_index = text.find(start_str)
    end_index = text.find(end_str)
    if start_index != -1 and end_index != -1:
        match_linkedin = text[start_index:end_index].strip().replace(" ", "")
        data["LinkedIn URL"] = match_linkedin

    # TODO #
    ############################################################################
    print("TESTING")
    # Define education-related keywords in English and Japanese
    edu_keywords = ["university", "college", "school", "institute", "faculty",
                    "bachelor", "master", "phd", "degree", "graduate", 
                    "大学", "学部", "大学院", "修士", "博士"]

    # Split the text into lines or sentences
    lines = re.split(r'\n|\.|\u3002', text)  # Also splits on Japanese full stop "。"

    # Search for lines with education-related keywords
    university_lines = [line.strip() for line in lines if any(keyword.lower() in line.lower() for keyword in edu_keywords)]

    # (Optional) Filter further to remove false positives or clean up text
    # For now, just print likely university-related lines
    print("Likely university-related text:")
    # print(university_lines)
    # for line in university_lines:
    #     print("-", line)
    
    def extract_university_info(text):
        # Match patterns like: Keio University Bachelor of Commerce - BCom · (April 2010 - March 2014)
        pattern = re.compile(
            r'(?P<university>[\w\s\-’&]+University|大学)\s+(?P<degree>.*?)(?:·|\(|\[)?\s*\(?(?P<start>[A-Za-z]+\s+\d{4})\s*[-–]\s*(?P<end>[A-Za-z]+\s+\d{4})\)?',
            flags=re.UNICODE
        )
        
        matches = pattern.findall(text)
        results = []

        for match in matches:
            university, degree, start, end = match
            results.append({
                "university": university.strip(),
                "degree": degree.strip(),
                "start_date": start.strip(),
                "end_date": end.strip()
            })

        return results

    overall_results = []
    for line in university_lines:
        overall_results.append(extract_university_info(line))
    print(overall_results)
    # exit()

    return data

# Paths to your resumes
# Define the folder path
folder_path = Path("McKinsey1")
pdf_files = [f for f in folder_path.glob("*") if f.is_file()]
# Process and collect data
records = [extract_resume_data(pdf) for pdf in pdf_files]

# Convert to DataFrame and export
df = pd.DataFrame(records)
df.to_csv("talent_mapping_pool.csv", index=False)

print("CSV file 'talent_mapping_pool.csv' generated successfully.")

