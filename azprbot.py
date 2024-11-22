import os
import i18n
from telegram import ReplyKeyboardMarkup, ChatMember
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from azure.devops.connection import Connection
from azure.devops.v5_0.git.models import GitPullRequestSearchCriteria, IdentityRefWithVote
from msrest.authentication import BasicAuthentication

# Variables globales
AZURE_DEVOPS_TOKEN = os.environ.get("AZURE_DEVOPS_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
AZURE_DEVOPS_ORG = os.environ.get("AZURE_DEVOPS_ORG")

# Estados de conversación
SELECT_PROJECT, SELECT_REPO, SELECT_PR = range(3)

# Usuarios autorizados y administradores del grupo
AUTHORIZED_USERS = set()
GROUP_ADMINISTRATORS = set()

# Configuración de idioma
LANGUAGE = "en"  # Idioma predeterminado

# Configuración de i18n
i18n.load_path.append('locales')  # Ruta a la carpeta de traducciones
i18n.set("locale", LANGUAGE)
i18n.set("fallback", "en")
i18n.set("enable_memoization", True)

# Funciones auxiliares
def update_language(update, context):
    """Configura el idioma del bot."""
    global LANGUAGE
    if context.args:
        lang = context.args[0].strip().lower()
        if lang in ["en", "es", "zh", "ru", "pt", "it"]:
            LANGUAGE = lang
            i18n.set("locale", lang)
            update.message.reply_text(i18n.t("language_set", language=lang))
        else:
            update.message.reply_text(i18n.t("unsupported_language"))
    else:
        update.message.reply_text(i18n.t("language_usage"))

def update_group_admins(context):
    """Actualiza la lista de administradores del grupo."""
    chat_id = context.job.context  # ID del chat proporcionado por el job
    try:
        admins = context.bot.get_chat_administrators(chat_id)
        admin_ids = {admin.user.id for admin in admins if admin.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]}
        global GROUP_ADMINISTRATORS
        GROUP_ADMINISTRATORS = admin_ids
    except Exception as e:
        print(f"Error updating group administrators: {e}")

def is_admin(user_id):
    """Verifica si un usuario es administrador."""
    return user_id in GROUP_ADMINISTRATORS

def get_projects():
    """Obtiene los proyectos de la organización en Azure DevOps."""
    credentials = BasicAuthentication('', AZURE_DEVOPS_TOKEN)
    connection = Connection(base_url=f'https://dev.azure.com/{AZURE_DEVOPS_ORG}', creds=credentials)
    core_client = connection.clients.get_core_client()
    projects = core_client.get_projects()
    return [project.name for project in projects] if projects else None

def get_repositories(project):
    """Obtiene los repositorios de un proyecto específico."""
    credentials = BasicAuthentication('', AZURE_DEVOPS_TOKEN)
    connection = Connection(base_url=f'https://dev.azure.com/{AZURE_DEVOPS_ORG}', creds=credentials)
    git_client = connection.clients.get_git_client()
    repos = git_client.get_repositories(project=project)
    return [repo.name for repo in repos] if repos else None

def get_pull_requests(project, repo):
    """Obtiene las pull requests abiertas de un repositorio específico."""
    credentials = BasicAuthentication('', AZURE_DEVOPS_TOKEN)
    connection = Connection(base_url=f'https://dev.azure.com/{AZURE_DEVOPS_ORG}', creds=credentials)
    git_client = connection.clients.get_git_client()
    search_criteria = GitPullRequestSearchCriteria(status="open")
    pull_requests = git_client.get_pull_requests(project=project, repository_id=repo, search_criteria=search_criteria)
    return [(pr.pull_request_id, pr.title) for pr in pull_requests] if pull_requests else None

def approve_pull_request(project, repo, pull_request_id):
    """Aprueba una pull request específica."""
    credentials = BasicAuthentication('', AZURE_DEVOPS_TOKEN)
    connection = Connection(base_url=f'https://dev.azure.com/{AZURE_DEVOPS_ORG}', creds=credentials)
    git_client = connection.clients.get_git_client()
    reviewer = IdentityRefWithVote(id="", vote=10)  # 10 indica aprobación
    git_client.create_pull_request_reviewer(project=project, repository_id=repo, pull_request_id=pull_request_id, reviewer=reviewer)

# Handlers del bot
def start(update, context):
    user_token = update.message.text.split()[-1].strip()
    if user_token == AZURE_DEVOPS_TOKEN:
        AUTHORIZED_USERS.add(update.message.from_user.id)
        update.message.reply_text(i18n.t("start_message"))
    else:
        update.message.reply_text(i18n.t("access_denied"))

def projects(update, context):
    if update.message.from_user.id not in AUTHORIZED_USERS:
        update.message.reply_text(i18n.t("access_denied"))
        return
    if not is_admin(update.message.from_user.id):
        update.message.reply_text(i18n.t("admin_only"))
        return
    projects = get_projects()
    if projects:
        reply_markup = ReplyKeyboardMarkup([[proj] for proj in projects], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(i18n.t("select_project"), reply_markup=reply_markup)
        return SELECT_PROJECT
    else:
        update.message.reply_text(i18n.t("fetch_projects_failed"))
        return ConversationHandler.END

# Función principal
def main():
    if not AZURE_DEVOPS_TOKEN or not TELEGRAM_BOT_TOKEN or not AZURE_DEVOPS_ORG:
        print(i18n.t("missing_env_vars"))
        return
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Job para actualizar administradores
    updater.job_queue.run_repeating(update_group_admins, interval=60, first=0, context=-100)  # Reemplaza -100 con tu ID de grupo

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("language", update_language))

    # Inicia el bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
