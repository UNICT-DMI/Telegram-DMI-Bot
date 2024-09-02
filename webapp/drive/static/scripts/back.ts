import { Folder, FOLDERMIME } from "./folder";
import { update_content } from "./update";

export class BackButton extends Folder {
    foldersHistory = new Array<string>();

    connectedCallback(): void {
        this.update({
            title: '..',
            id: 'back',
            mimeType: FOLDERMIME
        })
    }

    onFolderChange(folderId: string): void {
        this.foldersHistory.push(folderId);
        if (folderId != '') {
            this.show();
        } else {
            this.hide();
        }
    }

    override onClick(): void {
        const previousFolderId = this.foldersHistory[this.foldersHistory.length - 2];
        // Removing the last folder id in the history
        this.foldersHistory.splice(this.foldersHistory.length - 2);
        // Showing content of the previous folder
        update_content(previousFolderId);
    }
}

window.customElements.define('drive-back-button', BackButton);