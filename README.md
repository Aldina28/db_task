# Backend_task
This repository contains implementations of the task

# Steps to run 
1. Clone the repository
2. Create a virtual environment using command python3 -m venv env
3. Activate virtual enviornment using command
```
# for Windows
env/Source/activate
```
4. Install the dependencies using command pip install -r requirements.txt
5. In task\settings.py, update the host URL in the DATABASES configuration to your MongoDB client URL.
6. Run the server using command
```
python manage.py makemigrations
```
7. Run the server using command 
```
python manage.py migrate
```
8. Finally run the server using command
```
python manage.py runserver
```
Refer the documentation for making API calls
