import os
import requests
from giturlparse import parse
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from azure.devops.connection import Connection
from azure.devops.v5_0.git.models import GitPullRequestSearchCriteria
from msrest.authentication import BasicAuthentication

# Conversation states for the bot
SELECT_PROJECT, SELECT_REPO, SELECT_PR = range(3)

# Set to store the telegram users who have successfully matched the Azure DevOps API key
AUTHORIZED_USERS = set()

def get_projects(token, organization):
    # Function to fetch a list of projects from Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{organization}', creds=credentials)

    core_client = connection.clients.get_core_client()
    projects = core_client.get_projects()

    if projects:
        project_names = [project.name for project in projects]
        return project_names
    else:
        return None


def get_repos(token, organization, project):
    # Function to fetch a list of repositories for the selected project from Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{organization}', creds=credentials)
    git_client = connection.clients.get_git_client()
    repos = git_client.get_repositories(project=project)

    if repos:
        repo_names = [repo.name for repo in repos]
        return repo_names
    else:
        return None

def get_pull_requests(token, organization, project, repository):
    # Function to fetch a list of pull requests for the selected repository from Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{organization}', creds=credentials)

    git_client = connection.clients.get_git_client()

    # Get the repository ID using the repository name
    repository_id = get_repository_id_by_repo_name(repository, token, organization, project)

    if repository_id:
        # Set the search criteria to fetch open pull requests for the selected repository
        search_criteria = GitPullRequestSearchCriteria(status='open')  # Fetch all pull requests (open, completed, abandoned)

        pull_requests = git_client.get_pull_requests(project=project, repository_id=repository_id, search_criteria=search_criteria, skip=0, top=150)

        if pull_requests:
            pr_titles = [pr.title for pr in pull_requests]
            return pr_titles
        else:
            return None
    else:
        return None

def get_pull_requests_by_name(token, organization, project, repository, pull_request_name):
    # Function to fetch a list of pull requests for the selected repository from Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{organization}', creds=credentials)

    git_client = connection.clients.get_git_client()

    # Get the repository ID using the repository name
    repository_id = get_repository_id_by_repo_name(repository, token, organization, project)

    if repository_id:
        # Set the search criteria to fetch pull requests for the selected repository
        search_criteria = GitPullRequestSearchCriteria()
        search_criteria.include_links = False
        search_criteria.status = 'open'
        search_criteria.source_ref_name = f'refs/heads/{pull_request_name}'
        search_criteria.target_ref_name = 'refs/heads/develop'
        search_criteria.text = pull_request_name
        # Fetch all pull requests matching the provided name (the query returns an array, but we'll only take the first match)
        pull_requests = git_client.get_pull_requests(
            project=project, 
            repository_id=repository_id, 
            search_criteria=search_criteria, 
            skip=0, 
            top=1,
        )

        if pull_requests and len(pull_requests) > 0:
            return pull_requests[0].pull_request_id
        else:
            return None
    else:
        return None


def get_repository_id_by_repo_name(repo_name, token, organization, project):
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{organization}', creds=credentials)

    git_client = connection.clients.get_git_client()

    # Get the repositories in the project
    repos = git_client.get_repositories(project=project)
    for repo in repos:
        repository_name = str(repo.name)
        if repository_name == repo_name:
            return repo.id
    return "Repository not found"

def start(update, context):
    # Check if the user provided a token in the message
    user_token = update.message.text.split()[-1].strip()

    # Load environment variable for the Azure DevOps token
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")

    # Check if the user's token matches the one in the environment variable
    if user_token == azure_devops_token:
        # Store the user's token in the set of authorized users
        AUTHORIZED_USERS.add(update.message.from_user.id)
        update.message.reply_text(
            "Hi! I am your Azure DevOps bot. Use /projects to get started."
        )
    else:
        update.message.reply_text("Access denied. Invalid token.")


def projects(update, context):
    # Check if the user is authorized to use the /projects command
    if update.message.from_user.id not in AUTHORIZED_USERS:
        update.message.reply_text("Access denied. Please start the conversation with a valid token using /start.")
        return
    
    # Load environment variable for the Azure DevOps token
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")

    if not azure_devops_token:
        update.message.reply_text("Error: Please set the environment variable AZURE_DEVOPS_TOKEN.")
        return ConversationHandler.END

    # Load environment variable for the Telegram bot token
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not telegram_bot_token:
        update.message.reply_text("Error: Please set the environment variable TELEGRAM_BOT_TOKEN.")
        return ConversationHandler.END

    # Load environment variable for the Azure DevOps organization
    azure_devops_org = os.environ.get("AZURE_DEVOPS_ORG")

    if not azure_devops_org:
        update.message.reply_text("Error: Please set the environment variable AZURE_DEVOPS_ORG.")
        return ConversationHandler.END

    # Call your Azure DevOps API function to get a list of projects
    projects = get_projects(azure_devops_token, azure_devops_org)

    if projects:
        # Format the projects into a menu and display it to the user
        reply_markup = ReplyKeyboardMarkup([[proj] for proj in projects], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Please select a project:",
            reply_markup=reply_markup
        )
        return SELECT_PROJECT
    else:
        update.message.reply_text("Failed to fetch projects from Azure DevOps.")
        return ConversationHandler.END

def select_repo(update, context):
    # Check if the user is authorized to use the /projects command
    if update.message.from_user.id not in AUTHORIZED_USERS:
        update.message.reply_text("Access denied. Please start the conversation with a valid token using /start.")
        return
    # Handle user selection of a project
    selected_project = update.message.text
    context.user_data["selected_project"] = selected_project
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")
    azure_devops_org = os.environ.get("AZURE_DEVOPS_ORG")

    # Call your Azure DevOps API function to get a list of repositories for the selected project
    repositories = get_repos(azure_devops_token, azure_devops_org, selected_project)

    if repositories:
        # Format the repositories into a menu and display it to the user
        reply_markup = ReplyKeyboardMarkup([[repo] for repo in repositories], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Please select a repository:",
            reply_markup=reply_markup
        )
        return SELECT_REPO
    else:
        update.message.reply_text(f"Failed to fetch repositories for project {selected_project} from Azure DevOps.")
        return ConversationHandler.END

def select_pr(update, context):
    # Check if the user is authorized to use the /projects command
    if update.message.from_user.id not in AUTHORIZED_USERS:
        update.message.reply_text("Access denied. Please start the conversation with a valid token using /start.")
        return
    # Handle user selection of a repository
    selected_repo = update.message.text
    context.user_data["selected_repo"] = selected_repo
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")
    selected_project = context.user_data["selected_project"]
    azure_devops_org = os.environ.get("AZURE_DEVOPS_ORG")

    # Call your Azure DevOps API function to get a list of pull requests for the selected repository
    pull_requests = get_pull_requests(azure_devops_token, azure_devops_org, selected_project, selected_repo)

    if pull_requests:
        # Format the pull requests into a menu and display it to the user
        reply_markup = ReplyKeyboardMarkup([[pr] for pr in pull_requests], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Please select a pull request:",
            reply_markup=reply_markup
        )
        return SELECT_PR
    else:
        update.message.reply_text(f"No pull requests found for repository {selected_repo}. Please select another repository.")
        return ConversationHandler.END


def approve(update, context):
    # Check if the user is authorized to use the /projects command
    if update.message.from_user.id not in AUTHORIZED_USERS:
        update.message.reply_text("Access denied. Please start the conversation with a valid token using /start.")
        return
    # Handle user selection of a pull request
    selected_pr = update.message.text
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")
    selected_project = context.user_data["selected_project"]
    selected_repo = context.user_data["selected_repo"]

    if not azure_devops_token:
        update.message.reply_text("Error: Please set the environment variable AZURE_DEVOPS_TOKEN.")
        return ConversationHandler.END

    # Call your Azure DevOps API function to check if the authenticated user is a reviewer for the selected pull request
    is_reviewer = check_is_reviewer(azure_devops_token, selected_project, selected_repo, selected_pr)

    if is_reviewer:
        # Call your Azure DevOps API function to approve the pull request
        # Update the message to inform the user that the pull request is approved
        update.message.reply_text(f"Pull request '{selected_pr}' has been approved!")
    else:
        update.message.reply_text("You don't have permission to approve this pull request.")

    return ConversationHandler.END

def check_is_reviewer(token, project, repository, pull_request_name):
    # Function to check if the authenticated user is a reviewer for the selected pull request using the Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://dev.azure.com/{os.environ.get("AZURE_DEVOPS_ORG")}', creds=credentials)

    git_client = connection.clients.get_git_client()

    repository_id = get_repository_id_by_repo_name(repository, token, os.environ.get("AZURE_DEVOPS_ORG"), project)

    # Get the pull request ID using the pull request name
    pull_request_id = get_pull_requests_by_name(token, os.environ.get("AZURE_DEVOPS_ORG"), project, repository, pull_request_name)

    if not pull_request_id:
        return False

    # Get the pull request reviewers
    reviewers = git_client.get_pull_request_reviewers(project=project, repository_id=repository_id, pull_request_id=pull_request_id)

    if reviewers:
        # Get the unique name of the authenticated user
        authenticated_user = get_authenticated_user(token)

        # Check if the authenticated user is a reviewer for the selected pull request
        if authenticated_user in [reviewer.unique_name for reviewer in reviewers]:
            return True

    return False


def get_authenticated_user(token):
    # Function to get the unique name of the authenticated user from the Azure DevOps API
    credentials = BasicAuthentication('', token)
    connection = Connection(base_url=f'https://vssps.dev.azure.com/{os.environ.get("AZURE_DEVOPS_ORG")}', creds=credentials)

    profile_client = connection.clients.get_profile_client()
    user_profile = profile_client.get_profile()

    if user_profile:
        return user_profile.unique_name
    else:
        return None

def cancel(update, context):
    update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    # Load environment variables
    azure_devops_token = os.environ.get("AZURE_DEVOPS_TOKEN")
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    azure_devops_org = os.environ.get("AZURE_DEVOPS_ORG")

    if not azure_devops_token or not telegram_bot_token or not azure_devops_org:
        print("Error: Please set the environment variables AZURE_DEVOPS_TOKEN, TELEGRAM_BOT_TOKEN, and AZURE_DEVOPS_ORG.")
        return

    # Set up your Telegram Bot here and add the command handlers
    updater = Updater(telegram_bot_token, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("projects", projects)],
        states={
            SELECT_PROJECT: [MessageHandler(Filters.text, select_repo)],
            SELECT_REPO: [MessageHandler(Filters.text, select_pr)],
            SELECT_PR: [MessageHandler(Filters.text, approve)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    dp.add_handler(CommandHandler("start", start))  # Handle "/start" command
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()