export interface BackupInfo {
  filename: string
  createdAt: string
  sizeBytes: number
}


interface ApiBackupInfo {
  filename: string
  created_at: string
  size_bytes: number
}


export type BackupStatusValue =
  | 'success'
  | 'failed'
  | 'unknown'


export interface BackupStatus {
  status: BackupStatusValue
  executedAt?: string
  filename?: string
  error?: string
}


interface ApiBackupStatus {
  status: BackupStatusValue
  executed_at: string | null
  filename: string | null
  error: string | null
}


export interface BackupRestoreResult {
  restored: boolean
  safetyBackupFilename: string
  importedRevision: string
}


interface ApiBackupRestoreResult {
  restored: boolean
  safety_backup_filename: string
  imported_revision: string
}


function fromApi(
  backup: ApiBackupInfo,
): BackupInfo {
  return {
    filename: backup.filename,
    createdAt: backup.created_at,
    sizeBytes: backup.size_bytes,
  }
}


function restoreFromApi(
  result: ApiBackupRestoreResult,
): BackupRestoreResult {
  return {
    restored: result.restored,
    safetyBackupFilename:
      result.safety_backup_filename,
    importedRevision:
      result.imported_revision,
  }
}


async function errorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data =
      await response.json() as {
        detail?: string
      }

    return (
      data.detail
      ?? fallback
    )

  } catch {
    return fallback
  }
}


export async function fetchBackups(): Promise<
  BackupInfo[]
> {
  const response = await fetch(
    '/api/backups',
  )

  if (!response.ok) {
    throw new Error(
      await errorMessage(
        response,
        'Impossible de charger les sauvegardes.',
      ),
    )
  }

  const data =
    await response.json() as ApiBackupInfo[]

  return data.map(
    fromApi,
  )
}


export async function createBackup(): Promise<
  BackupInfo
> {
  const response = await fetch(
    '/api/backups',
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw new Error(
      await errorMessage(
        response,
        'Impossible de créer la sauvegarde.',
      ),
    )
  }

  const data =
    await response.json() as ApiBackupInfo

  return fromApi(
    data,
  )
}


export async function fetchBackupStatus(): Promise<
  BackupStatus
> {
  const response = await fetch(
    '/api/backups/status',
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de contrôler la sauvegarde automatique.',
    )
  }

  const data =
    await response.json() as ApiBackupStatus

  return {
    status: data.status,
    executedAt:
      data.executed_at
      ?? undefined,
    filename:
      data.filename
      ?? undefined,
    error:
      data.error
      ?? undefined,
  }
}


export async function deleteBackup(
  filename: string,
): Promise<void> {
  const response = await fetch(
    (
      '/api/backups/'
      + encodeURIComponent(
        filename,
      )
    ),
    {
      method: 'DELETE',
    },
  )

  if (!response.ok) {
    throw new Error(
      await errorMessage(
        response,
        'Impossible de supprimer la sauvegarde.',
      ),
    )
  }
}


export async function restoreExistingBackup(
  filename: string,
): Promise<BackupRestoreResult> {
  const response = await fetch(
    (
      '/api/backups/'
      + encodeURIComponent(
        filename,
      )
      + '/restore'
    ),
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw new Error(
      await errorMessage(
        response,
        'Impossible de restaurer la sauvegarde.',
      ),
    )
  }

  const data =
    await response.json() as ApiBackupRestoreResult

  return restoreFromApi(
    data,
  )
}


export async function restoreBackupFile(
  file: File,
): Promise<BackupRestoreResult> {
  const response = await fetch(
    '/api/backups/restore',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/zip',
      },
      body: file,
    },
  )

  if (!response.ok) {
    throw new Error(
      await errorMessage(
        response,
        'Impossible de restaurer la sauvegarde.',
      ),
    )
  }

  const data =
    await response.json() as ApiBackupRestoreResult

  return restoreFromApi(
    data,
  )
}


export function backupDownloadUrl(
  filename: string,
): string {
  return (
    '/api/backups/'
    + encodeURIComponent(
      filename,
    )
    + '/download'
  )
}
