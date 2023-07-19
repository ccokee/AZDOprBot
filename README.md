**Azure DevOps Bot**

This repository contains a Telegram bot built with Python that integrates with the Azure DevOps API to provide project, repository, and pull request information to users. The bot allows users to interact with it using commands to get a list of projects, repositories, and pull requests, as well as to approve a pull request if the user is a reviewer.

**Dependencies**

The bot relies on the following dependencies:

- Python 3.9
- python-telegram-bot 13.7
- requests 2.26.0

You can install these dependencies by running:

```
pip install -r requirements.txt
```

**Getting Started**

1. Clone this repository:

```
git clone https://github.com/your-username/azure-devops-bot.git
cd azure-devops-bot
```

2. Create a virtual environment (optional but recommended):

```
python -m venv venv
```

3. Activate the virtual environment:

   - For Windows:

```
venv\Scripts\activate
```

   - For macOS and Linux:

```
source venv/bin/activate
```

4. Install the dependencies:

```
pip install -r requirements.txt
```

5. Set up environment variables:

   Before running the bot, make sure to set the following environment variables:

   - `AZURE_DEVOPS_TOKEN`: Your Azure DevOps Personal Access Token.
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
   - `AZURE_DEVOPS_ORG`: Your Azure DevOps organization name.

   You can set the environment variables by creating a `.env` file in the project root directory and adding the variables like this:

   ```
   AZURE_DEVOPS_TOKEN=your_azure_devops_token_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   AZURE_DEVOPS_ORG=your_azure_devops_organization_name_here
   ```

6. Run the bot:

```
python your_bot_script.py
```

**Usage**

- Start the bot by sending the `/start` command.
- Use the `/projects` command to get a list of projects from Azure DevOps.
- Select a project from the provided list to proceed.
- Use the `/repos` command to get a list of repositories for the selected project.
- Select a repository to proceed.
- Use the `/pull_requests` command to get a list of pull requests for the selected repository.
- Select a pull request to proceed.
- If you are a reviewer for the selected pull request, you can use the `/approve` command to approve it.

**Docker Support**

You can also run the bot using Docker. Ensure you have Docker installed and follow these steps:

1. Build the Docker image:

```
docker build -t azure-devops-bot .
```

2. Run the Docker container:

```
docker run -d -p 8443:8443 \
-e AZURE_DEVOPS_TOKEN=your_azure_devops_token_here \
-e TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here \
-e AZURE_DEVOPS_ORG=your_azure_devops_organization_name_here \
--name azure_devops_bot_container azure-devops-bot
```

**Deployment**

The bot can be deployed on any server that supports Python. You can use platforms like Heroku, AWS, or GCP to host the bot. Ensure you have set the required environment variables on the server before deploying.

**Contributing**

Contributions to the project are welcome! If you find any issues or have suggestions for improvements, please feel free to open a new issue or submit a pull request.

**License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Disclaimer**

Please note that this project is provided as-is, and the author takes no responsibility for its usage or any issues that may arise from using it in a production environment. Use it at your own risk.