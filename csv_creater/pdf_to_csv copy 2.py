# @File: pdf_to_csv.py
# @Autor: Masato Nobunaga
# @Date: 6/13/25
# @Email: Nobunaga@wayequity.co
# @Last Modified By: Masato Nobunaga
# @Last Modified Date: 6/15/25
import os
import fitz  # PyMuPDF
import pandas as pd
import re

# Folder containing folders of PDF resumes
PDF_FOLDER = "mck/"
OUTPUT_CSV = "resume_summary.csv"

# Multilingual headers (EN, JA, CN, KR, FR)
CONTACT_HEADERS = ["Contact", "連絡先", "联系方式", "연락처", "Coordonnées"]
EXP_HEADERS = ["Experience", "職歴", "工作经历", "경력", "Expérience"]
EDU_HEADERS = ["Education", "学歴", "教育经历", "학력", "Formation"]
COMPANY = "McKinsey & Company"

# retrieves the raw text from the pdfs
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    print(text)

    return text

# driver funciton that extracts all the required info
def extract_info(text):
    lines = text.splitlines()
    # print(lines)
    
    name, linkedin_url, position, work_length, education, degree, grad_year = "", "", "", "", "", "", ""


    name, linkedin_url = oneTwo(text, lines)
    # # Step 1: LinkedIn URL
    # linkedin_start_match = re.search(r"(www.linkedin.com/in[^\s()]+)", text)
    # print("START: ", linkedin_start_match)
    # first_name = ""
    # last_name = ""

    # linkedin_start = ""
    # linkedin_end = ""

    # if linkedin_start_match:
    #     print("---------------------------------------------------------")
    #     linkedin_start = linkedin_start_match.group(1)

    #     first_name = linkedin_start.split('/')[-1]

    #     if first_name and first_name[-1] == '-':
    #         first_name = first_name[:-1]
    #     print("First Name: ", first_name)

    #     # Step 1: Name
    #     for line in lines:
    #         if 'LinkedIn)' in line:
    #             if '-' in line:
    #                 last_name = line.split('-')[:-1][0].strip()
    #                 # print("LAST NAME = " + last_name)
    #                 # print(line)
    #             elif len(line.split(' ')) > 1:
    #                 last_name = line.split(' ')[:-1][0]
    #                 if any(char.isdigit() for char in last_name):
    #                     last_name = ""
    #                 # print(linkedin_end)

    #             linkedin_end = line.split(' ')[0]
    #             if linkedin_end == "(LinkedIn)":
    #                 linkedin_end = ""
    #             # print(type(linkedin_end))
    #             # print("LinkedIn ending: _", linkedin_end)
    #             break
                
        
    #     name = first_name.capitalize() + " " + last_name.capitalize()
        
    #     # cleans up the name by getting rid of spaces at the beginning or end
    #     while name and name[0] == ' ':
    #         name = name[1:]

    #     name = name.strip()
    #     # print("NAME HERE: ", name)
    #     # gets rid of the - that is sometimes in the name
    #     if '-' in name:
    #         name = name.replace('-', ' ')
    #         separated = name.split(' ')
    #         for i in range(len(separated)):
    #             separated[i] = separated[i].capitalize()
    #         # print(separated)
    #         name = separated[0] + ' ' + separated[1]
    #         # print("New Name: ", name)

    #     linked_url = linkedin_start + linkedin_end
    #     print(linked_url)

    # Step 3: Company and Position
    exp_start_idx = None
    for i, line in enumerate(lines):
        if any(h == line.strip() for h in EXP_HEADERS):
            exp_start_idx = i
            break
    
    exp_start_idx = adjust(exp_start_idx, lines)
    # person that worked for many positions at the company
    if any(char.isdigit() for char in lines[exp_start_idx + 2]):
        work_length = lines[exp_start_idx + 2]
        position = lines[exp_start_idx + 3]
    else:
        work_length = lines[exp_start_idx + 3]
        position = lines[exp_start_idx + 2]
       
    print("POSITION AT MCK: ", position)
    print("WORK LENGTH AT MCK: ", work_length)

    # Step 4: Last Education section
    edu_start_idx = None
    for i, line in enumerate(lines):
        if any(h == line.strip() for h in EDU_HEADERS):
            edu_start_idx = i + 1
            break

    if edu_start_idx:
        for j in range(edu_start_idx, len(lines)):
            if lines[j].strip() and not re.search(r"\d", lines[j]):
                education = lines[j].strip()
                degree_idx = j+1
                degree = lines[j+1].strip()

                # in the event the "Page 1 of 2" line is there
                if degree == "":
                    while not degree or "Page" in degree:
                        degree_idx += 1
                        degree = lines[degree_idx].strip()                       
                break

        # degree cleanup
        print("DEGREE: ", degree)
        for index, letter in enumerate(degree):
            # print(degree)
            # print(letter)
            # print(index)
            if letter == '·':
                degree = degree[:index].strip()
                break
                
        print("DEGREE 2.0: ", degree)

        # Step 5: Graduation Year (look backwards from education header)
        details = ""
        for k, line in enumerate(lines[edu_start_idx:]):
            if any(h in line for h in EDU_HEADERS):
                break
            else:   # adds the lines that don't have the next education
                details += line
        
        # details now has all the info about the latest education
        potential_years = re.findall(r"20(1[3-9]|2[0-3])", details)
        grad_year = "20" + max(potential_years, default="")

    return {
        "Name": name,
        "LinkedIn URL": linkedin_url,
        "Company & Position": position,
        "Work Length": work_length,
        "Last Education": education,
        "Degree": degree,
        "Graduation Year": grad_year
    }

def process_folder(folder):
    results = []

    for sub_folder in os.listdir(folder):
        if sub_folder != ".DS_Store":
            sub_folder = folder + sub_folder + "/"
            for filename in os.listdir(sub_folder):
                # print("FILENAME: ", filename)
                if filename.lower().endswith(".pdf"):
                    path = os.path.join(sub_folder, filename)
                    text = extract_text_from_pdf(path)
                    info = extract_info(text)
                    results.append(info)
    
    return results

def save_to_csv(data, path):
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print(f"Data saved to {path}")

# TODO change name
def oneTwo(text, lines):
    first_name = ""
    last_name = ""
    link_start = ""
    link_end = ""

    link_start = re.search(r"(www.linkedin.com/in[^\s()]+)", text)

    if link_start:
        link_start = link_start.group(1)

        # retrieves the initial start of the user's name
        first_name = link_start.split('/')[-1]

        # gets rid of the '-' connecting the first and last name
        if first_name and first_name[-1] == '-':
            first_name = first_name[:-1]

        # formulates the linkedin url
        for line in lines:
            if 'LinkedIn)' in line:
                # if they're multiple instances of their name, there's a
                # random identifier to set it apart
                if '-' in line:
                    last_name = line.split('-')[:-1][0].strip()
                elif len(line.split(' ')) > 1:
                    last_name = line.split(' ')[:-1][0]
                    if any(char.isdigit() for char in last_name):
                        last_name = ""

                # cleans up the link 
                link_end = line.split(' ')[0]
                if link_end == "(LinkedIn)":
                    link_end = ""

                break

        name = first_name.capitalize() + last_name.capitalize()

        # cleans up the name by getting rid of spaces at the beginning or end
        while name and name[0] == ' ':
            name = name[1:]
        name = name.strip()

        # gets rid of the - that is sometimes in the name
        if '-' in name:
            name = name.replace('-', ' ')
            separated = name.split(' ')
            for i in range(len(separated)):
                separated[i] = separated[i].capitalize()
            name = separated[0] + ' ' + separated[1]

    linkedin_url = link_start + link_end
    return name, linkedin_url


def adjust(exp_start_idx, lines):
    if lines[exp_start_idx+1] == " " or lines[exp_start_idx+1] == " ":
        exp_start_idx += 1
        while lines[exp_start_idx] != COMPANY:
            exp_start_idx += 1

        # TODO Not fully fixed: what if the company is different (language?)
            # print("Changing")
    # print("HERE IS WHAT IT IS: ", lines[exp_start_idx])
    return exp_start_idx

if __name__ == "__main__":
    extracted_data = process_folder(PDF_FOLDER)
    save_to_csv(extracted_data, OUTPUT_CSV)