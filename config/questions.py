'''
Author:     Tom Arc
LinkedIn:   https://www.linkedin.com/in/tom-arc

Copyright (C) 2024 Tom Arc


'''


###################################################### APPLICATION INPUTS ######################################################


# >>>>>>>>>>> Easy Apply Questions & Inputs <<<<<<<<<<<

# Give an relative path of your default resume to be uploaded. If file in not found, will continue using your previously uploaded resume in LinkedIn.
default_resume_path = "all resumes/default/Tom_Arc_CV.pdf"      # (In Development)

# What do you want to answer for questions that ask about years of experience you have, this is different from current_experience? 
years_of_experience = "2"          # A number in quotes Eg: "0","1","2","3","4", etc.

# Do you need visa sponsorship now or in future?
require_visa = "Yes"               # "Yes" or "No"

# What is the link to your portfolio website, leave it empty as "", if you want to leave this question unanswered
website = "https://github.com/arctom"                        # "www.example.bio" or "" and so on....

# Please provide the link to your LinkedIn profile.
linkedIn = "https://www.linkedin.com/in/tom-arc/"       # "https://www.linkedin.com/in/example" or "" and so on...

# What is the status of your citizenship? # If left empty as "", tool will not answer the question. However, note that some companies make it compulsory to be answered
# Valid options are: "U.S. Citizen/Permanent Resident", "Non-citizen allowed to work for any employer", "Non-citizen allowed to work for current employer", "Non-citizen seeking work authorization", "Canadian Citizen/Permanent Resident" or "Other"
us_citizenship = "Non-citizen seeking work authorization"



## SOME ANNOYING QUESTIONS BY COMPANIES 🫠 ##

# What to enter in your desired salary question (American and European), What is your expected CTC (South Asian and others)?, only enter in numbers as some companies only allow numbers,
desired_salary = 80000          # 80000, 90000, 100000 or 120000 and so on... Do NOT use quotes
'''
Note: If question has the word "lakhs" in it (Example: What is your expected CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
And if asked in months, then it will divide by 12 and answer. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
'''

# What is your current CTC? Some companies make it compulsory to be answered in numbers...
current_ctc = 55000           # 800000, 900000, 1000000 or 1200000 and so on... Do NOT use quotes
'''
Note: If question has the word "lakhs" in it (Example: What is your current CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
# And if asked in months, then it will divide by 12 and answer. Examples:
# * 2400000 will be answered as "200000"
# * 850000 will be answered as "70833"
'''

# (In Development) # Currency of salaries you mentioned. Companies that allow string inputs will add this tag to the end of numbers. Eg: 
# currency = "INR"                 # "USD", "INR", "EUR", etc.

# What is your notice period in days?
notice_period = 30                   # Any number >= 0 without quotes. Eg: 0, 7, 15, 30, 45, etc.
'''
Note: If question has 'month' or 'week' in it (Example: What is your notice period in months), 
then it will divide by 30 or 7 and answer respectively. Examples:
* For notice_period = 66:
  - "66" OR "2" if asked in months OR "9" if asked in weeks
* For notice_period = 15:"
  - "15" OR "0" if asked in months OR "2" if asked in weeks
* For notice_period = 0:
  - "0" OR "0" if asked in months OR "0" if asked in weeks
'''

# Your LinkedIn headline in quotes Eg: "Software Engineer @ Google, Masters in Computer Science", "Recent Grad Student @ MIT, Computer Science"
linkedin_headline = "Machine Learning Engineer Expert | Artifical Intelligence Specialist | Development Leader" # "Headline" or "" to leave this question unanswered

# Your summary in quotes, use \n to add line breaks
linkedin_summary = "Machine Learning Engineer and Data Scientist with a strong academic background in Data Science and Mathematics from Tecnológico de Monterrey. Based in Chihuahua, México, I bring experience in building machine learning models, data-driven solutions, and scalable software applications. My technical abilities span cloud computing, advanced analytics, and AI-powered solutions for business applications. Throughout my career, I've had the privilege of leading cross-functional teams and delivering projects using technologies such as Python, TensorFlow, FastAPI, React, SQL Server, IBM Watson X, AWS, and GCP. At NDS Cognitive Labs, I directed a team to create a generative AI chatbot using RAG technology, enhancing customer service by automating 30% of retraining tasks. Some key highlights of my experience include: Leading a 6-person team to design SaaS platforms for trend analysis and interactive data visualization. Developing a virtual sales assistant that boosted conversion rates by 5% for a major insurance company. Building real-time data dashboards for leadership teams, streamlining decision-making processes. I am fluent in English, Spanish, and French, collaborating with global teams and clients. My leadership skills, paired with good project management and effective communication, allow me to drive projects from concept to deployment. Technical skills: Python, TensorFlow, NLP, RAG, AWS, GCP, MongoDB, SQL, Power BI, FastAPI, React, Kubernetes, Docker, Agile/Scrum methodologies. I’m seeking new challenges where I can apply my skills in machine learning, AI, cloud computing, and data analysis to deliver impactful solutions. Let's connect to discuss how we can drive innovation and success together."
'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Your cover letter in quotes, use \n to add line breaks (This question makes sense though)
cover_letter = """Dear Hiring Manager, I am writing to express my strong interest in the position. As a passionate and experienced professional in the field of AI and machine learning, I am thrilled at the opportunity to contribute to your cutting-edge projects and help solve complex problems for your clients. With over two years of experience as a Machine Learning Engineer at NDS Cognitive Labs, I have developed a robust skill set that aligns perfectly with your requirements. My expertise in Python, TensorFlow, and scikit-learn has enabled me to design and implement various machine learning models, including predictive AI systems and generative AI chatbots. For instance, I recently led a team in creating an AI-powered virtual sales assistant using RAG technology, which increased conversion rates by 5%. This project showcased my ability to analyze complex datasets, optimize algorithms, and deliver tangible business results. My experience extends to collaborating with cross-functional teams, a key aspect of the role you've described. I've successfully directed teams of 4-6 people in developing M-SaaS platforms and implementing advanced NLP techniques, demonstrating my strong communication and leadership skills. Moreover, my background in data science and mathematics, coupled with my continuous learning approach (evidenced by my certifications in MongoDB, GCP, and Kubernetes), positions me to stay at the forefront of machine learning advancements and contribute innovative solutions to your projects. Thank you for considering my application. I look forward to the possibility of speaking with you further about this exciting opportunity. Sincerely, Tom Arc, arctomb@gmail.com, +52 (625) 589 8930"""
'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Name of your most recent employer
recent_employer = "NDS Cognitive Labs" # "", "Lala Company", "Google", "Snowflake", "Databricks"

# Example question: "On a scale of 1-10 how much experience do you have building web or mobile applications? 1 being very little or only in school, 10 being that you have built and launched applications to real users"
confidence_level = "8"             # Any number between "1" to "10" including 1 and 10, put it in quotes ""
##



# >>>>>>>>>>> RELATED SETTINGS <<<<<<<<<<<

## Allow Manual Inputs
# Should the tool pause before every submit application during easy apply to let you check the information?
pause_before_submit = True         # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''

# Should the tool pause if it needs help in answering questions during easy apply?
# Note: If set as False will answer randomly...
pause_at_failed_question = True    # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''
##

# Do you want to overwrite previous answers?
overwrite_previous_answers = False # True or False
