import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  Download,
  HardDriveDownload,
  RotateCcw,
  Trash2,
  Upload,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  ProfileSection,
} from '../profile/ProfileSection'

import {
  backupDownloadUrl,
  createBackup,
  deleteBackup,
  fetchBackups,
  fetchBackupStatus,
  restoreBackupFile,
  restoreExistingBackup,
} from './backupApi'

import type {
  BackupInfo,
  BackupStatus,
} from './backupApi'


export function BackupSection() {
  const {
    toast,
  } = useToast()

  const [
    backups,
    setBackups,
  ] = useState<BackupInfo[]>([])

  const [
    status,
    setStatus,
  ] = useState<BackupStatus>({
    status: 'unknown',
  })

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    creating,
    setCreating,
  ] = useState(false)

  const [
    deleting,
    setDeleting,
  ] = useState<string | null>(
    null,
  )

  const [
    restoreOpen,
    setRestoreOpen,
  ] = useState(false)

  const [
    restoreFilename,
    setRestoreFilename,
  ] = useState<string | null>(
    null,
  )

  const [
    restoreFile,
    setRestoreFile,
  ] = useState<File | null>(
    null,
  )

  const [
    restoring,
    setRestoring,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )


  const loadData =
    useCallback(
      async () => {
        try {
          setError(
            null,
          )

          const [
            backupResult,
            statusResult,
          ] = await Promise.all([
            fetchBackups(),
            fetchBackupStatus(),
          ])

          setBackups(
            backupResult,
          )

          setStatus(
            statusResult,
          )

        } catch (reason) {
          setError(
            getErrorMessage(
              reason,
              'Impossible de charger les sauvegardes.',
            ),
          )

        } finally {
          setLoading(
            false,
          )
        }
      },
      [],
    )


  useEffect(() => {
    void loadData()
  }, [
    loadData,
  ])


  async function handleBackup() {
    try {
      setCreating(
        true,
      )

      setError(
        null,
      )

      await createBackup()

      await loadData()

      toast({
        type: 'success',
        title: 'Sauvegarde créée',
        message:
          'La base OpenCoach a été sauvegardée.',
      })

    } catch (reason) {
      const message =
        getErrorMessage(
          reason,
          'Impossible de créer la sauvegarde.',
        )

      setError(
        message,
      )

      toast({
        type: 'error',
        title: 'Sauvegarde impossible',
        message,
      })

    } finally {
      setCreating(
        false,
      )
    }
  }


  async function handleDelete(
    backup: BackupInfo,
  ) {
    const confirmed =
      window.confirm(
        (
          'Supprimer définitivement cette '
          + 'sauvegarde ?\n\n'
          + backup.filename
        ),
      )

    if (!confirmed) {
      return
    }

    try {
      setDeleting(
        backup.filename,
      )

      await deleteBackup(
        backup.filename,
      )

      await loadData()

      toast({
        type: 'success',
        title: 'Sauvegarde supprimée',
      })

    } catch (reason) {
      toast({
        type: 'error',
        title: 'Suppression impossible',
        message:
          getErrorMessage(
            reason,
            'Impossible de supprimer la sauvegarde.',
          ),
      })

    } finally {
      setDeleting(
        null,
      )
    }
  }


  function openExistingRestore(
    filename: string,
  ) {
    setRestoreFilename(
      filename,
    )

    setRestoreFile(
      null,
    )

    setRestoreOpen(
      true,
    )
  }


  function openUploadRestore() {
    setRestoreFilename(
      null,
    )

    setRestoreFile(
      null,
    )

    setRestoreOpen(
      true,
    )
  }


  function closeRestore() {
    if (restoring) {
      return
    }

    setRestoreOpen(
      false,
    )

    setRestoreFilename(
      null,
    )

    setRestoreFile(
      null,
    )
  }


  async function handleRestore() {
    if (
      !restoreFilename
      && !restoreFile
    ) {
      return
    }

    try {
      setRestoring(
        true,
      )

      const result =
        restoreFilename
          ? await restoreExistingBackup(
              restoreFilename,
            )
          : await restoreBackupFile(
              restoreFile!,
            )

      setRestoreOpen(
        false,
      )

      setRestoreFilename(
        null,
      )

      setRestoreFile(
        null,
      )

      await loadData()

      toast({
        type: 'success',
        title: 'Restauration terminée',
        message: (
          'Une sauvegarde de sécurité '
          + 'a été créée avant restauration : '
          + result.safetyBackupFilename
        ),
        duration: null,
        actionLabel: 'Recharger',
        onAction: () => {
          window.location.reload()
        },
      })

    } catch (reason) {
      toast({
        type: 'error',
        title: 'Restauration impossible',
        message:
          getErrorMessage(
            reason,
            'Le backup n’a pas pu être restauré.',
          ),
        duration: null,
      })

    } finally {
      setRestoring(
        false,
      )
    }
  }


  const latest =
    backups[0]


  return (
    <>
      <ProfileSection
        title="Sauvegarde des données"
        icon={
          <HardDriveDownload
            size={21}
          />
        }
        iconClassName="
          bg-secondary/10
          text-secondary
        "
        description={
          'Sauvegarde automatique, '
          + 'export et protection des données OpenCoach.'
        }
        trailing={
          <BackupStatusBadge
            status={
              status.status
            }
          />
        }
      >
        <div className="space-y-5">

          <div
            className="
              grid
              gap-4
              sm:grid-cols-3
            "
          >
            <BackupStat
              label="Automatique"
              value="Chaque nuit · 03:00"
            />

            <BackupStat
              label="Rétention"
              value="7 jours"
            />

            <BackupStat
              label="Dernière sauvegarde"
              value={
                latest
                  ? formatBackupDate(
                      latest.createdAt,
                    )
                  : 'Aucune'
              }
            />
          </div>


          {status.status === 'failed' && (
            <div
              className="
                alert
                alert-error
                text-sm
              "
            >
              <div>
                <p className="font-semibold">
                  La dernière sauvegarde
                  automatique a échoué.
                </p>

                {status.executedAt && (
                  <p className="mt-1 text-xs opacity-80">
                    {
                      formatBackupDate(
                        status.executedAt,
                      )
                    }
                  </p>
                )}

                {status.error && (
                  <p className="mt-1 text-xs opacity-80">
                    {status.error}
                  </p>
                )}
              </div>
            </div>
          )}


          {error && (
            <div
              className="
                alert
                alert-error
                text-sm
              "
            >
              {error}
            </div>
          )}


          <div
            className="
              flex
              flex-wrap
              items-center
              justify-between
              gap-3
            "
          >
            <div>
              <h3 className="font-semibold text-base-content">
                Sauvegardes disponibles
              </h3>

              <p className="mt-1 text-sm text-base-content/50">
                Archives ZIP exportables et restaurables.
              </p>
            </div>

            <div
              className="
                flex
                flex-wrap
                gap-2
              "
            >
              <button
                type="button"
                onClick={
                  openUploadRestore
                }
                className="
                  btn
                  btn-outline
                  btn-sm
                "
              >
                <Upload
                  size={15}
                />

                Importer
              </button>

              <button
                type="button"
                disabled={creating}
                onClick={
                  handleBackup
                }
                className="
                  btn
                  btn-primary
                  btn-sm
                "
              >
                {creating
                  ? (
                    <span
                      className="
                        loading
                        loading-spinner
                        loading-xs
                      "
                    />
                  )
                  : (
                    <HardDriveDownload
                      size={15}
                    />
                  )}

                Sauvegarder maintenant
              </button>
            </div>
          </div>


          {loading ? (
            <div className="flex justify-center py-6">
              <span
                className="
                  loading
                  loading-spinner
                  loading-sm
                "
              />
            </div>
          ) : backups.length === 0 ? (
            <p className="py-4 text-sm text-base-content/45">
              Aucune sauvegarde disponible.
            </p>
          ) : (
            <div
              className="
                divide-y
                divide-base-300
                rounded-xl
                border
                border-base-300
              "
            >
              {backups.map(
                (backup) => (
                  <div
                    key={
                      backup.filename
                    }
                    className="
                      flex
                      flex-wrap
                      items-center
                      justify-between
                      gap-3
                      px-4
                      py-3
                    "
                  >
                    <div>
                      <p
                        className="
                          text-sm
                          font-medium
                          text-base-content
                        "
                      >
                        {
                          formatBackupDate(
                            backup.createdAt,
                          )
                        }
                      </p>

                      <p
                        className="
                          mt-0.5
                          text-xs
                          text-base-content/45
                        "
                      >
                        {
                          formatBytes(
                            backup.sizeBytes,
                          )
                        }
                      </p>
                    </div>

                    <div
                      className="
                        flex
                        flex-wrap
                        items-center
                        gap-1
                      "
                    >
                      <a
                        href={
                          backupDownloadUrl(
                            backup.filename,
                          )
                        }
                        className="
                          btn
                          btn-ghost
                          btn-sm
                        "
                      >
                        <Download
                          size={15}
                        />

                        Télécharger
                      </a>

                      <button
                        type="button"
                        onClick={() =>
                          openExistingRestore(
                            backup.filename,
                          )
                        }
                        className="
                          btn
                          btn-ghost
                          btn-sm
                        "
                      >
                        <RotateCcw
                          size={15}
                        />

                        Restaurer
                      </button>

                      <button
                        type="button"
                        disabled={
                          deleting
                          === backup.filename
                        }
                        onClick={() =>
                          void handleDelete(
                            backup,
                          )
                        }
                        className="
                          btn
                          btn-ghost
                          btn-sm
                          text-error
                        "
                        aria-label="Supprimer la sauvegarde"
                      >
                        {deleting === backup.filename
                          ? (
                            <span
                              className="
                                loading
                                loading-spinner
                                loading-xs
                              "
                            />
                          )
                          : (
                            <Trash2
                              size={15}
                            />
                          )}
                      </button>
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </ProfileSection>


      <Modal
        title="Restaurer une sauvegarde"
        open={
          restoreOpen
        }
        onClose={
          closeRestore
        }
      >
        <div className="space-y-5">

          <div
            className="
              alert
              alert-warning
              text-sm
            "
          >
            <div>
              <p className="font-semibold">
                Cette opération remplace les données
                actuellement utilisées par OpenCoach.
              </p>

              <p className="mt-1">
                Une sauvegarde de sécurité de la base
                actuelle sera créée automatiquement
                avant toute restauration.
              </p>
            </div>
          </div>


          {restoreFilename ? (
            <div
              className="
                rounded-xl
                border
                border-base-300
                bg-base-200/40
                p-4
              "
            >
              <p className="text-xs text-base-content/45">
                Sauvegarde sélectionnée
              </p>

              <p
                className="
                  mt-1
                  break-all
                  font-semibold
                  text-base-content
                "
              >
                {restoreFilename}
              </p>
            </div>
          ) : (
            <fieldset className="fieldset">
              <label
                htmlFor="backup-import-file"
                className="fieldset-legend"
              >
                Fichier de sauvegarde OpenCoach
              </label>

              <input
                id="backup-import-file"
                type="file"
                accept=".zip,application/zip"
                onChange={(event) => {
                  setRestoreFile(
                    event.target.files?.[0]
                    ?? null,
                  )
                }}
                className="
                  file-input
                  file-input-bordered
                  w-full
                "
              />

              <p className="mt-2 text-xs text-base-content/45">
                Sélectionnez une archive ZIP créée
                par le système de sauvegarde OpenCoach.
              </p>
            </fieldset>
          )}


          <div
            className="
              flex
              justify-end
              gap-3
              border-t
              border-base-300
              pt-5
            "
          >
            <button
              type="button"
              disabled={restoring}
              onClick={
                closeRestore
              }
              className="
                btn
                btn-ghost
              "
            >
              Annuler
            </button>

            <button
              type="button"
              disabled={
                restoring
                || (
                  !restoreFilename
                  && !restoreFile
                )
              }
              onClick={() =>
                void handleRestore()
              }
              className="
                btn
                btn-warning
              "
            >
              {restoring && (
                <span
                  className="
                    loading
                    loading-spinner
                    loading-sm
                  "
                />
              )}

              Restaurer les données
            </button>
          </div>
        </div>
      </Modal>
    </>
  )
}


function BackupStatusBadge({
  status,
}: {
  status: BackupStatus['status']
}) {
  if (status === 'success') {
    return (
      <span className="badge badge-success badge-sm">
        OK
      </span>
    )
  }

  if (status === 'failed') {
    return (
      <span className="badge badge-error badge-sm">
        Échec
      </span>
    )
  }

  return (
    <span className="badge badge-ghost badge-sm">
      Inconnu
    </span>
  )
}


function BackupStat({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-xl
        border
        border-base-300
        bg-base-200/40
        p-4
      "
    >
      <p
        className="
          text-xs
          uppercase
          tracking-wide
          text-base-content/40
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-sm
          font-semibold
          text-base-content
        "
      >
        {value}
      </p>
    </div>
  )
}


function formatBackupDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      dateStyle: 'short',
      timeStyle: 'short',
    },
  ).format(
    new Date(
      value,
    ),
  )
}


function formatBytes(
  bytes: number,
): string {
  if (bytes < 1024) {
    return `${bytes} o`
  }

  if (
    bytes
    < 1024 * 1024
  ) {
    return (
      `${(
        bytes / 1024
      ).toFixed(0)} Ko`
    )
  }

  return (
    `${(
      bytes
      / 1024
      / 1024
    ).toFixed(1)} Mo`
  )
}


function getErrorMessage(
  reason: unknown,
  fallback: string,
): string {
  return (
    reason instanceof Error
      ? reason.message
      : fallback
  )
}
