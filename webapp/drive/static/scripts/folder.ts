import { Container } from "./container";
import { DriveResource } from "./resource";
import { update_content } from "./update";


export const FOLDERMIME = 'application/vnd.google-apps.folder';

export class Folder extends HTMLElement {
    data: DriveResource;
    label: HTMLElement;

    constructor(parent: HTMLElement, i: number) {
        super();

        const icon = document.createElement('i');
        icon.classList.add('gg-folder');
        this.label = document.createElement('folder-name');
        this.append(icon, this.label);
        this.addEventListener('click', this.onClick.bind(this));
        this.classList.add('drive-folder');
    }

    onClick(): void {
        // this.classList.add('fadeout');
        update_content(this.data.id);
    }

    update(data: DriveResource): void {
        this.data = data;
        this.label.textContent = this.data.title;
    }

    show(): void {
        this.classList.remove('hidden');
    }

    hide(): void {
        this.classList.add('hidden');
    }
};



const foldersList = document.getElementById('folders-list') as HTMLElement;
export const folders = new Container<DriveResource>(foldersList, Folder);
window.customElements.define('drive-folder', Folder);