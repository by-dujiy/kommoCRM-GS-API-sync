# kommoCRM-GoogleSpreadsheets sync via API

---
## Description:
>This is a copy of my freelance order. All confidential information is hidden

The project was developed with the goal of synchronizing the patient visit log, which is kept in GoogleSpreadsheets, with the kommoCRM.

The program synchronizes any changes in orders, regardless of where these changes were made - in kommoCRM or in GoogleSpreadsheets.

During the development process was added the ability to create new orders and patient credentials through entries in a GoogleSpreadsheet

The program automatically checks the relevance of kommoCRM access tokens and, if they expire, automatically updates them.

___
## Features:
- Initially, the customer wanted the data from the kommoCRM to be simply uploaded to Google spreadsheets
- however, during the development process a number of changes were made, including double synchronization, creation of new fields in the kommoCRM from a GoogleSpreadsheet, and constant operation of the script in the background.

---
## Installation

- The program works by running run_app.py 
- Before starting, you must install all the necessary libraries from requirements.txt and configure all the necessary environment variables in .env
- If desired, you can package everything into *.exe file by running the command pyinstaller --onefile run_app.py through the terminal

___
## License:
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.