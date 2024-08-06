Hello!
This is API for posts and comments write in FastAPI.
For using load code to your computer
Make .env file using your own data. Take as exapmle .env.example file.
Make virtual environment and load all packeges which are in pyproject.toml file
This API use PostgresSQL and Redis, that why you need Docker. All needed images you may load using docker-compose.yaml.
Using uvicorn server your app will run.
API:
- have authintification, with using JWT, reset of pasword and sending email for confirming user and reset pasword;
- have CRUD functionality for posts and comments;
- have validations to incorrect words in text of posts and comments. Posts and comments which not valid get status blocked and wuold`t show in site;
- you can show statistics of comments to the post in chosse days;
- have a automatical reply to the comment if user set the flag;
Enjoi!
