# PyFixer-Gemini

#  Create Gemini API Key and add to your PC
- Goto [Link](https://aistudio.google.com/apikey) and login with google account and Create API KEY 
- Add API Key to System Enviromnetal Variable 

![alt text](<./images/systemEnvsetupApiKey.png>)

- Restart your PC incase if getting problem with API Key to apply changes on System variables

#  How to setup Python Environment
### On the Path of PyFixer-Gemini folder create a Python environment
```bash
$ python -m venv pyEnv 
$ .\pyEnv\Scripts\activate
$ pip install PyQt6 google-generativeai
```

# Run Main.py 
```bash
$ python .\main.py
```
**Note:** INTENTIONAL ERROR FOR DEMO: This will cause a ZeroDivisionError at Line 62
#### If main.py runs properly it corrects the code
