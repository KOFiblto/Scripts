import fs from 'fs/promises';
import path from 'path';

export async function saveFile(file: File, folder: string): Promise<string> {
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    const uploadDir = path.join(process.cwd(), 'public', 'uploads', folder);
    await fs.mkdir(uploadDir, { recursive: true });

    const fileName = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, '-')}`;
    const filePath = path.join(uploadDir, fileName);

    await fs.writeFile(filePath, buffer);

    return `/uploads/${folder}/${fileName}`;
}
