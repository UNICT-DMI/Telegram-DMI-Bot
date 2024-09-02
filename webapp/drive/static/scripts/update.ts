import { FOLDERMIME, folders } from "./folder";
import { files } from "./file";
import { DriveResource } from "./resource";
import { BackButton } from "./back";


const backButton = document.getElementById('back-button') as BackButton;

export function update_content(folderId: string): void {
    fetch(`/drive/folder?folder_id=${folderId}`)
    .then(response => response.json())
    .then((data: DriveResource[]) => {
        folders.setContent(data.filter((res => res.mimeType == FOLDERMIME)));
        files.setContent(data.filter((res => res.mimeType != FOLDERMIME)));
        // Include a special link to go back to the previous folder
        backButton.onFolderChange(folderId);
    });
}