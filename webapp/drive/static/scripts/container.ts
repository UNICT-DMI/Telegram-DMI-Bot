export abstract class Containable<T> extends HTMLElement {
    // The HTMLElement to be collected.
    data: T

    abstract update(data: T): void;
    abstract show(): void;
    abstract hide(): void;
};

export class Container<T> {
    // Makes it easier to add elements or
    // update already existing ones.
    content = new Array<Containable<T>>();
    parent: HTMLElement;
    elementType: new (p: HTMLElement, i: number) => Containable<T>;

    constructor(parent: HTMLElement, elementType: new (p: HTMLElement, i: number) => Containable<T>) {
        this.parent = parent;
        this.elementType = elementType;
    }

    setContent(content: T[]) {
        // Displays the given list of objects
        for (var i=0; i < content.length; i++)
            this.addOrUpdate(content[i], i);
        this.hideFrom(i);
    }

    addOrUpdate(data: T, i: number = 0) {
        if (this.content[i]) {
            // If an object has been created already,
            // update its content and show it
            this.content[i].update(data);
            this.content[i].show();
        } else {
            // Otherwise, create a new one
            let e = new this.elementType(this.parent, i);
            e.update(data);
            e.show();
            this.content.push(e);
            this.parent.append(e);
        }
    }

    hideFrom(i: number = 0) {
        // Start hiding elements from i till the end
        for (; i < this.content.length; i++) {
            this.content[i].hide();
        }
    }
};
