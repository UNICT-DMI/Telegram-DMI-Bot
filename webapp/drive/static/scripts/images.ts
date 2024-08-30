const images = {
    audio: 'https://telegra.ph/file/83285485816f7cf0fcf67.png',
    image: 'https://telegra.ph/file/a1f5285c74ce80d8fa554.png',
    pdf: 'https://telegra.ph/file/cc429f1e5d235f54a4500.png',
    document: 'https://telegra.ph/file/a12324faf7e9385ed23e8.png',
    file: 'https://telegra.ph/file/6995dd010a84417175963.png'
}


export function match(mime: string) {
    const entries = Object.entries(images);
    for (let i=0; i < entries.length; i++) {
        if (mime.includes(entries[i][0])) {
            return entries[i][1];
        }
    }

    return images.file;
}