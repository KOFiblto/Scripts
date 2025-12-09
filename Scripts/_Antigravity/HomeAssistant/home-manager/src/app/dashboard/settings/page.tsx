'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { exportData, importData } from "@/actions/backup"
import { useState } from "react"
import { Download, Upload, AlertTriangle, FileUp } from "lucide-react"

export default function SettingsPage() {
    const [loading, setLoading] = useState(false)

    const handleExport = async () => {
        setLoading(true)
        try {
            const result = await exportData()
            if (result.success && result.data) {
                // Trigger download
                const link = document.createElement('a')
                link.href = `data:application/zip;base64,${result.data}`
                link.download = `home-manager-backup-${new Date().toISOString().split('T')[0]}.zip`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
            } else {
                alert("Failed to export data")
            }
        } catch (e) {
            alert("Error exporting data")
        }
        setLoading(false)
    }

    const handleImport = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        if (!confirm("WARNING: This will overwrite all your current data! Are you sure?")) return

        setLoading(true)
        const formData = new FormData(e.currentTarget)
        const result = await importData(formData)

        if (result.success) {
            alert("Data imported successfully! The page will reload.")
            window.location.reload()
        } else {
            alert("Failed to import data")
        }
        setLoading(false)
    }

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">Manage application settings and data.</p>
            </div>

            <div className="grid gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Download className="w-5 h-5" />
                            Data Management
                        </CardTitle>
                        <CardDescription>
                            Backup or restore your entire application data (Database + Images).
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">

                        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between p-4 border rounded-lg bg-secondary/10">
                            <div className="space-y-1">
                                <h4 className="text-sm font-medium">Export Data</h4>
                                <p className="text-xs text-muted-foreground">
                                    Download a .zip file containing all your floorplans, devices, and settings.
                                </p>
                            </div>
                            <Button onClick={handleExport} disabled={loading}>
                                <Download className="w-4 h-4 mr-2" />
                                {loading ? 'Exporting...' : 'Download Backup'}
                            </Button>
                        </div>

                        <div className="flex flex-col gap-4 border-t pt-6">
                            <div className="space-y-1">
                                <h4 className="text-sm font-medium flex items-center gap-2 text-red-500">
                                    <AlertTriangle className="w-4 h-4" />
                                    Import Data
                                </h4>
                                <p className="text-xs text-muted-foreground">
                                    Restore from a previous backup .zip file. <span className="font-bold text-red-500">This will overwrite all current data.</span>
                                </p>
                            </div>

                            <form onSubmit={handleImport} className="flex flex-col sm:flex-row gap-4 items-end sm:items-center">
                                <div className="grid w-full max-w-sm items-center gap-1.5">
                                    <Label htmlFor="backup-file">Backup File</Label>
                                    <Input id="backup-file" name="file" type="file" accept=".zip" required className="cursor-pointer" />
                                </div>
                                <Button type="submit" variant="destructive" disabled={loading}>
                                    <Upload className="w-4 h-4 mr-2" />
                                    {loading ? 'Restoring...' : 'Restore Data'}
                                </Button>
                            </form>
                        </div>

                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
