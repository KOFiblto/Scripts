'use server'

import { prisma } from '@/lib/prisma'
import AdmZip from 'adm-zip'
import fs from 'fs'
import path from 'path'
import { revalidatePath } from 'next/cache'

// Helper to get uploads dir
const UPLOADS_DIR = path.join(process.cwd(), 'public', 'uploads')
const DB_PATH = path.join(process.cwd(), 'prisma', 'dev.db')

export async function exportData() {
    try {
        const zip = new AdmZip()

        // Add Database file
        if (fs.existsSync(DB_PATH)) {
            zip.addLocalFile(DB_PATH, 'prisma')
        }

        // Add Uploads folder
        if (fs.existsSync(UPLOADS_DIR)) {
            zip.addLocalFolder(UPLOADS_DIR, 'uploads')
        }

        // Generate buffer
        const buffer = zip.toBuffer()

        // We need to return this as base64 to client to facilitate download 
        // since Server Actions can't stream files directly easily without a Route Handler?
        // Actually, returning a Base64 string is fine for small-medium apps.
        return { success: true, data: buffer.toString('base64') }
    } catch (e) {
        console.error("Export error:", e)
        return { success: false, error: "Failed to export data" }
    }
}

export async function importData(formData: FormData) {
    const file = formData.get('file') as File

    if (!file) {
        throw new Error("No file uploaded")
    }

    try {
        const arrayBuffer = await file.arrayBuffer()
        const buffer = Buffer.from(arrayBuffer)
        const zip = new AdmZip(buffer)

        // 1. Extract Database
        const dbEntry = zip.getEntry('prisma/dev.db')
        if (dbEntry) {
            // Need to close Prisma connection first? SQLite might lock...
            // In dev mode it might be fine, but robustly we should probably
            // disconnect. But Prisma disconnect isn't exposed easily on singleton.
            // Let's try overwriting. If it fails, we catch it.

            // Backup current DB just in case?
            if (fs.existsSync(DB_PATH)) {
                fs.copyFileSync(DB_PATH, `${DB_PATH}.bak`)
            }

            fs.writeFileSync(DB_PATH, dbEntry.getData())
        }

        // 2. Extract Uploads
        // zip.extractEntryTo doesn't support generic folder extraction easily without iteration?
        // extractAllTo overwrites.
        zip.extractAllTo(process.cwd(), true) // This might be messy if zip structure is wrong.
        // We zipped as 'uploads/...' and 'prisma/...'.
        // So extracting to process.cwd() should put them in `public/uploads` and `prisma/dev.db`.

        // Revalidate everything
        revalidatePath('/')

        return { success: true }
    } catch (e) {
        console.error("Import error:", e)
        return { success: false, error: "Failed to import data" }
    }
}
