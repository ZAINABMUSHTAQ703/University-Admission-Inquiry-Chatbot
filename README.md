# University Admission Inquiry Chatbot

## Overview
It is a university admission inquiry chatbot designed to handle frequently asked questions related to the admission process. It helps students by providing instant responses about admission requirements, deadlines, programs offered, fee structure, and other related queries.  

This project was developed as part of my **Final Year Project (FYP)** to automate the admission inquiry system and reduce the workload of university staff.  

---
## Project Timeline
- **Start Date:** Sep 2024  
- **End Date:** May 2025  
- **Duration:** 8 months  
- **Role:** Group Leader  

## Features
- ✅ Provides admission-related FAQs (eligibility, deadlines, fee structure, programs, etc.)
- ✅ Handles general university queries (contact info, departments, facilities)
- ✅ User-friendly and conversational experience
- ✅ Reduces manual effort for staff  
- ✅ Extensible to integrate with web or mobile applications  

---

## 🛠️ Tech Stack
- **Backend / Chatbot Engine**: Rasa (Python-based)  
- **Frontend (optional)**: Web integration (HTML, CSS, JS)  
- **Database**: SQLite / JSON knowledge base  
- **Documentation**: SRDS, SRS, Flowcharts, and Use Case diagrams  

---

## Documentation
All project reports, SRDS, and diagrams are available.  
Includes:
- Software Requirement Document (SRDS)  
- Use Case Diagrams  
- Sequence Diagrams  
- System Architecture  

---

## How to Run
Installation guide for Application
Prerequisites
Before installation, ensure the following are installed on your system:
Anaconda Distribution (with Python 3.9 support)
Visual Studio Code (VS Code) (or any preferred IDE)

Step-by-Step Installation
1) Set Up Python Environment
2) Open Anaconda Prompt or terminal and execute:
bash
conda create -n rasa_env python=3.9
conda activate rasa_env
3)Verify Python version:
bash
python --version 
4)Install Rasa Framework within the activated rasa_env environment:
bash
pip install rasa
5)Initialize a new Rasa project:
bash
rasa init
6)Validate Installation Check installed versions:
bash
rasa --version           
conda info --envs        
7)Install Additional Dependencies
Install required libraries for actions and Gemini API integration:
bash
pip install rasa_sdk python-dotenv requests flask flask-cors google-generativeai
pip install gemini-ai
8)Train the Chatbot Model
bash
rasa train
9)For production-ready models:
bash
rasa train --fixed-model-name su_admission_bot --force
10)Run the Chatbot
Start the Rasa action server:
bash
rasa run actions
Launch the API server (for frontend integration):
bash
rasa run -m models --enable-api --cors "*"
Test interactions in the shell:
bash
rasa shell

---

## 🌟 Future Enhancements

* Integration with **university website**
* **Voice-based interaction**
* **Live chat with staff + AI hybrid model**
* **Analytics dashboard** for queries

---

## Author

**Zainab Mushtaq**

* BS Information Technology (University of Sargodha)
* Skills: Python, Rasa, UI/UX, Databases, Web Development
* [LinkedIn](https://www.linkedin.com/in/zainab-mushtaq-068043324)

---

## License

This project is for academic and learning purposes only.





