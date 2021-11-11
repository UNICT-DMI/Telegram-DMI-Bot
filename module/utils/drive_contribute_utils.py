import yaml

from pydrive2.files import GoogleDriveFile

with open('config/settings.yaml', 'r') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)


def delete_drive_permission_job(context):
    job_data = context.job.context

    drive_root_folder: GoogleDriveFile = job_data['folder_obj']
    permission = job_data['permission_obj']
    request_message = job_data['request_message']

    drive_root_folder.DeletePermission(permission['id'])

    context.bot.send_message(
        chat_id=config_map["dev_group_chatid"],
        text=f"Permessi ritirati",
        reply_to_message_id=request_message.message_id,
    )
