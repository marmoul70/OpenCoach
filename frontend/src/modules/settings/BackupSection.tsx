import {
  Archive,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Download,
  HardDriveDownload,
  LoaderCircle,
  RotateCcw,
  ShieldCheck,
  Trash2,
  Upload,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  useToast,
} from '../../components/ui/ToastProvider'

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
  ] = useState<
    BackupInfo[]
  >([])

  const [
    status,
    setStatus,
  ] = useState<
    BackupStatus
  >({
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
  ] = useState<
    string | null
  >(null)

  const [
    restoreOpen,
    setRestoreOpen,
  ] = useState(false)

  const [
    restoreFilename,
    setRestoreFilename,
  ] = useState<
    string | null
  >(null)

  const [
    restoreFile,
    setRestoreFile,
  ] = useState<
    File | null
  >(null)

  const [
    restoring,
    setRestoring,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)


  const loadData =
    useCallback(
      async () => {
        try {
          setError(null)

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
              (
                'Impossible de charger '
                + 'les sauvegardes.'
              ),
            ),
          )
        } finally {
          setLoading(false)
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
      setCreating(true)
      setError(null)

      await createBackup()
      await loadData()

      toast({
        type: 'success',

        title:
          'Sauvegarde créée',

        message:
          'La base OpenCoach '
          + 'a été sauvegardée.',
      })
    } catch (reason) {
      const message =
        getErrorMessage(
          reason,
          (
            'Impossible de créer '
            + 'la sauvegarde.'
          ),
        )

      setError(message)

      toast({
        type: 'error',
        title:
          'Sauvegarde impossible',
        message,
      })
    } finally {
      setCreating(false)
    }
  }


  async function handleDelete(
    backup: BackupInfo,
  ) {
    const confirmed =
      window.confirm(
        (
          'Supprimer définitivement '
          + 'cette sauvegarde ?\n\n'
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
        title:
          'Sauvegarde supprimée',
      })
    } catch (reason) {
      toast({
        type: 'error',

        title:
          'Suppression impossible',

        message:
          getErrorMessage(
            reason,
            (
              'Impossible de supprimer '
              + 'la sauvegarde.'
            ),
          ),
      })
    } finally {
      setDeleting(null)
    }
  }


  function openExistingRestore(
    filename: string,
  ) {
    setRestoreFilename(
      filename,
    )

    setRestoreFile(null)
    setRestoreOpen(true)
  }


  function openUploadRestore() {
    setRestoreFilename(null)
    setRestoreFile(null)
    setRestoreOpen(true)
  }


  function closeRestore() {
    if (restoring) {
      return
    }

    setRestoreOpen(false)
    setRestoreFilename(null)
    setRestoreFile(null)
  }


  async function handleRestore() {
    if (
      !restoreFilename
      && !restoreFile
    ) {
      return
    }

    try {
      setRestoring(true)

      const result =
        restoreFilename
          ? (
              await restoreExistingBackup(
                restoreFilename,
              )
            )
          : (
              await restoreBackupFile(
                restoreFile!,
              )
            )

      setRestoreOpen(false)
      setRestoreFilename(null)
      setRestoreFile(null)

      await loadData()

      toast({
        type: 'success',

        title:
          'Restauration terminée',

        message: (
          'Une sauvegarde de sécurité '
          + 'a été créée avant restauration : '
          + result.safetyBackupFilename
        ),

        duration: null,

        actionLabel:
          'Recharger',

        onAction: () => {
          window.location.reload()
        },
      })
    } catch (reason) {
      toast({
        type: 'error',

        title:
          'Restauration impossible',

        message:
          getErrorMessage(
            reason,
            (
              'Le backup n’a pas pu '
              + 'être restauré.'
            ),
          ),

        duration: null,
      })
    } finally {
      setRestoring(false)
    }
  }


  const latest =
    backups[0]


  return (
    <>

      <div className="space-y-3">

        {/* =============================================
            DATA HEALTH
            ============================================= */}

        <section
          className="
            overflow-hidden
            rounded-[12px]
            border
            border-black/[0.065]
            bg-white
            dark:border-white/[0.065]
            dark:bg-[#151b1f]
          "
        >
          <div
            className="
              relative
              overflow-hidden
              px-4
              py-4
            "
          >
            <div
              className="
                pointer-events-none
                absolute
                -right-16
                -top-20
                h-44
                w-44
                rounded-full
                bg-emerald-500/[0.05]
                blur-3xl
              "
            />

            <div
              className="
                relative
                flex
                items-start
                justify-between
                gap-3
              "
            >
              <div
                className="
                  flex
                  min-w-0
                  items-start
                  gap-3
                "
              >
                <div
                  className="
                    flex
                    h-10
                    w-10
                    shrink-0
                    items-center
                    justify-center
                    rounded-[11px]
                    bg-emerald-50
                    text-emerald-600
                    dark:bg-emerald-500/[0.08]
                    dark:text-emerald-400
                  "
                >
                  <ShieldCheck
                    className="
                      h-[18px]
                      w-[18px]
                    "
                  />
                </div>

                <div>
                  <div
                    className="
                      flex
                      flex-wrap
                      items-center
                      gap-2
                    "
                  >
                    <h3
                      className="
                        text-[14px]
                        font-bold
                        tracking-[-0.02em]
                        text-slate-950
                        dark:text-white
                      "
                    >
                      Protection des données
                    </h3>

                    <BackupStatus
                      status={
                        status.status
                      }
                    />
                  </div>

                  <p
                    className="
                      mt-1
                      text-[10px]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    Sauvegarde automatique,
                    archives et restauration
                    OpenCoach.
                  </p>
                </div>
              </div>


              <button
                type="button"
                disabled={creating}
                onClick={() =>
                  void handleBackup()
                }
                className="
                  flex
                  h-8
                  shrink-0
                  items-center
                  gap-1.5
                  rounded-[8px]
                  bg-emerald-600
                  px-3
                  text-[9.5px]
                  font-semibold
                  text-white
                  transition
                  hover:bg-emerald-700
                  disabled:opacity-40
                "
              >
                {
                  creating
                    ? (
                        <LoaderCircle
                          className="
                            h-3
                            w-3
                            animate-spin
                          "
                        />
                      )
                    : (
                        <HardDriveDownload
                          className="
                            h-3
                            w-3
                          "
                        />
                      )
                }

                Sauvegarder
              </button>
            </div>
          </div>


          <div
            className="
              grid
              grid-cols-3
              border-t
              border-black/[0.055]
              dark:border-white/[0.06]
            "
          >
            <DataMetric
              icon={
                <Clock3
                  className="
                    h-3
                    w-3
                  "
                />
              }
              label="Automatique"
              value="Chaque nuit"
              secondary="03:00"
            />

            <DataMetric
              icon={
                <Archive
                  className="
                    h-3
                    w-3
                  "
                />
              }
              label="Rétention"
              value="7 jours"
            />

            <DataMetric
              icon={
                <CheckCircle2
                  className="
                    h-3
                    w-3
                  "
                />
              }
              label="Dernière"
              value={
                latest
                  ? (
                      formatHumanDate(
                        latest.createdAt,
                      )
                    )
                  : 'Aucune'
              }
            />
          </div>
        </section>


        {/* =============================================
            STATUS / ERROR
            ============================================= */}

        {status.status === 'failed' && (
          <div
            className="
              flex
              items-start
              gap-2
              rounded-[10px]
              border
              border-red-500/15
              bg-red-50
              px-3
              py-2.5
              text-red-600
              dark:bg-red-500/[0.06]
              dark:text-red-400
            "
          >
            <CircleAlert
              className="
                mt-px
                h-4
                w-4
                shrink-0
              "
            />

            <div>
              <p
                className="
                  text-[10px]
                  font-semibold
                "
              >
                La dernière sauvegarde
                automatique a échoué.
              </p>

              {status.executedAt && (
                <p
                  className="
                    mt-1
                    text-[9px]
                    opacity-75
                  "
                >
                  {
                    formatHumanDate(
                      status.executedAt,
                    )
                  }
                </p>
              )}

              {status.error && (
                <p
                  className="
                    mt-1
                    text-[9px]
                    opacity-75
                  "
                >
                  {status.error}
                </p>
              )}
            </div>
          </div>
        )}


        {error && (
          <div
            className="
              flex
              items-start
              gap-2
              rounded-[10px]
              border
              border-red-500/15
              bg-red-50
              px-3
              py-2.5
              text-[10px]
              text-red-600
              dark:bg-red-500/[0.06]
              dark:text-red-400
            "
          >
            <CircleAlert
              className="
                mt-px
                h-3.5
                w-3.5
                shrink-0
              "
            />

            {error}
          </div>
        )}


        {/* =============================================
            ARCHIVES
            ============================================= */}

        <section
          className="
            overflow-hidden
            rounded-[12px]
            border
            border-black/[0.065]
            bg-white
            dark:border-white/[0.065]
            dark:bg-[#151b1f]
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              gap-3
              border-b
              border-black/[0.055]
              px-4
              py-3
              dark:border-white/[0.06]
            "
          >
            <div>
              <p
                className="
                  text-[9px]
                  font-bold
                  uppercase
                  tracking-[0.1em]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Archives
              </p>

              <p
                className="
                  mt-1
                  text-[11.5px]
                  font-semibold
                  text-slate-800
                  dark:text-slate-200
                "
              >
                Sauvegardes disponibles
              </p>
            </div>


            <button
              type="button"
              onClick={
                openUploadRestore
              }
              className="
                flex
                h-8
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-emerald-500/35
                px-2.5
                text-[9.5px]
                font-semibold
                text-emerald-700
                transition
                hover:border-emerald-500/55
                hover:bg-emerald-50
                dark:border-emerald-400/30
                dark:text-emerald-400
                dark:hover:bg-emerald-500/[0.07]
              "
            >
              <Upload
                className="
                  h-3
                  w-3
                "
              />

              Importer
            </button>
          </div>


          {loading ? (
            <div
              className="
                flex
                justify-center
                py-8
              "
            >
              <LoaderCircle
                className="
                  h-5
                  w-5
                  animate-spin
                  text-emerald-500
                "
              />
            </div>

          ) : backups.length === 0 ? (

            <div
              className="
                px-4
                py-7
                text-center
              "
            >
              <Archive
                className="
                  mx-auto
                  h-5
                  w-5
                  text-slate-200
                  dark:text-slate-700
                "
              />

              <p
                className="
                  mt-2
                  text-[10px]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Aucune sauvegarde disponible.
              </p>
            </div>

          ) : (

            <div>
              {backups.map(
                (
                  backup,
                  index,
                ) => (
                  <BackupRow
                    key={
                      backup.filename
                    }
                    backup={backup}
                    divided={
                      index > 0
                    }
                    deleting={
                      deleting
                      === backup.filename
                    }
                    onRestore={() =>
                      openExistingRestore(
                        backup.filename,
                      )
                    }
                    onDelete={() =>
                      void handleDelete(
                        backup,
                      )
                    }
                  />
                ),
              )}
            </div>
          )}
        </section>
      </div>


      {/* =============================================
          RESTORE MODAL
          ============================================= */}

      <Modal
        title="Restaurer une sauvegarde"
        open={restoreOpen}
        onClose={closeRestore}
      >
        <div className="space-y-4">

          <div
            className="
              flex
              items-start
              gap-2
              rounded-[10px]
              border
              border-amber-500/15
              bg-amber-50
              px-3
              py-2.5
              text-amber-700
              dark:bg-amber-500/[0.06]
              dark:text-amber-400
            "
          >
            <CircleAlert
              className="
                mt-px
                h-4
                w-4
                shrink-0
              "
            />

            <div>
              <p
                className="
                  text-[10.5px]
                  font-semibold
                "
              >
                Cette opération remplace
                les données actuelles.
              </p>

              <p
                className="
                  mt-1
                  text-[9.5px]
                  leading-4
                  opacity-80
                "
              >
                Une sauvegarde de sécurité
                sera créée automatiquement
                avant la restauration.
              </p>
            </div>
          </div>


          {restoreFilename ? (
            <div
              className="
                rounded-[10px]
                border
                border-black/[0.06]
                bg-slate-50
                p-3
                dark:border-white/[0.06]
                dark:bg-white/[0.025]
              "
            >
              <p
                className="
                  text-[8.5px]
                  font-semibold
                  uppercase
                  tracking-[0.08em]
                  text-slate-400
                "
              >
                Sauvegarde sélectionnée
              </p>

              <p
                className="
                  mt-1.5
                  break-all
                  text-[10.5px]
                  font-semibold
                  text-slate-700
                  dark:text-slate-300
                "
              >
                {restoreFilename}
              </p>
            </div>

          ) : (

            <label>
              <span
                className="
                  mb-1.5
                  block
                  text-[9px]
                  font-semibold
                  uppercase
                  tracking-[0.07em]
                  text-slate-400
                "
              >
                Archive OpenCoach
              </span>

              <input
                id="backup-import-file"
                type="file"
                accept=".zip,application/zip"
                onChange={event => {
                  setRestoreFile(
                    event.target
                      .files?.[0]
                    ?? null,
                  )
                }}
                className="
                  block
                  w-full
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-slate-50
                  p-2
                  text-[9.5px]
                  text-slate-500
                  file:mr-3
                  file:rounded-[7px]
                  file:border-0
                  file:bg-emerald-50
                  file:px-2.5
                  file:py-1.5
                  file:text-[9px]
                  file:font-semibold
                  file:text-emerald-700
                  dark:border-white/[0.07]
                  dark:bg-white/[0.025]
                  dark:text-slate-400
                  dark:file:bg-emerald-500/[0.08]
                  dark:file:text-emerald-400
                "
              />

              <p
                className="
                  mt-1.5
                  text-[9px]
                  text-slate-400
                "
              >
                Archive ZIP créée par
                OpenCoach.
              </p>
            </label>
          )}


          <div
            className="
              flex
              justify-end
              gap-2
              border-t
              border-black/[0.055]
              pt-3
              dark:border-white/[0.06]
            "
          >
            <button
              type="button"
              disabled={restoring}
              onClick={closeRestore}
              className="
                h-8
                rounded-[8px]
                px-3
                text-[10px]
                font-semibold
                text-slate-400
                hover:bg-slate-50
                hover:text-slate-700
                dark:hover:bg-white/[0.04]
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
                flex
                h-8
                items-center
                gap-1.5
                rounded-[8px]
                bg-amber-500
                px-3
                text-[10px]
                font-semibold
                text-white
                transition
                hover:bg-amber-600
                disabled:cursor-not-allowed
                disabled:bg-slate-200
                disabled:text-slate-400
                dark:disabled:bg-white/[0.05]
              "
            >
              {restoring && (
                <LoaderCircle
                  className="
                    h-3
                    w-3
                    animate-spin
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


function BackupRow({
  backup,
  divided,
  deleting,
  onRestore,
  onDelete,
}: {
  backup: BackupInfo
  divided: boolean
  deleting: boolean
  onRestore: () => void
  onDelete: () => void
}) {
  return (
    <div
      className={[
        (
          'flex items-center '
          + 'gap-3 px-4 py-3'
        ),
        divided
          ? (
              'border-t '
              + 'border-black/[0.055] '
              + 'dark:border-white/[0.06]'
            )
          : '',
      ].join(' ')}
    >
      <div
        className="
          flex
          h-8
          w-8
          shrink-0
          items-center
          justify-center
          rounded-[9px]
          bg-emerald-50
          text-emerald-600
          dark:bg-emerald-500/[0.07]
          dark:text-emerald-400
        "
      >
        <Archive
          className="
            h-3.5
            w-3.5
          "
        />
      </div>


      <div
        className="
          min-w-0
          flex-1
        "
      >
        <p
          className="
            text-[10.5px]
            font-semibold
            text-slate-700
            dark:text-slate-300
          "
        >
          {
            formatHumanDate(
              backup.createdAt,
            )
          }
        </p>

        <p
          className="
            mt-0.5
            text-[8.5px]
            text-slate-400
            dark:text-slate-500
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
          aria-label="Télécharger"
          title="Télécharger"
          className="
            flex
            h-8
            w-8
            items-center
            justify-center
            rounded-[8px]
            text-slate-400
            transition
            hover:bg-emerald-50
            hover:text-emerald-600
            dark:hover:bg-emerald-500/[0.07]
          "
        >
          <Download
            className="
              h-3.5
              w-3.5
            "
          />
        </a>

        <button
          type="button"
          aria-label="Restaurer"
          title="Restaurer"
          onClick={onRestore}
          className="
            flex
            h-8
            w-8
            items-center
            justify-center
            rounded-[8px]
            text-slate-400
            transition
            hover:bg-amber-50
            hover:text-amber-600
            dark:hover:bg-amber-500/[0.07]
          "
        >
          <RotateCcw
            className="
              h-3.5
              w-3.5
            "
          />
        </button>

        <button
          type="button"
          disabled={deleting}
          aria-label="Supprimer"
          title="Supprimer"
          onClick={onDelete}
          className="
            flex
            h-8
            w-8
            items-center
            justify-center
            rounded-[8px]
            text-slate-300
            transition
            hover:bg-red-50
            hover:text-red-500
            disabled:opacity-40
            dark:hover:bg-red-500/[0.06]
          "
        >
          {
            deleting
              ? (
                  <LoaderCircle
                    className="
                      h-3.5
                      w-3.5
                      animate-spin
                    "
                  />
                )
              : (
                  <Trash2
                    className="
                      h-3.5
                      w-3.5
                    "
                  />
                )
          }
        </button>
      </div>
    </div>
  )
}


function BackupStatus({
  status,
}: {
  status:
    BackupStatus['status']
}) {
  const success =
    status === 'success'

  const failed =
    status === 'failed'

  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'gap-1 rounded-full '
          + 'px-1.5 py-0.5 '
          + 'text-[8px] '
          + 'font-semibold'
        ),
        success
          ? (
              'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : failed
            ? (
                'bg-red-50 '
                + 'text-red-600 '
                + 'dark:bg-red-500/[0.07] '
                + 'dark:text-red-400'
              )
            : (
                'bg-slate-100 '
                + 'text-slate-400 '
                + 'dark:bg-white/[0.04] '
                + 'dark:text-slate-500'
              ),
      ].join(' ')}
    >
      <span
        className={[
          (
            'h-1.5 w-1.5 '
            + 'rounded-full'
          ),
          success
            ? 'bg-emerald-500'
            : failed
              ? 'bg-red-500'
              : 'bg-slate-300',
        ].join(' ')}
      />

      {
        success
          ? 'Opérationnelle'
          : failed
            ? 'Échec'
            : 'État inconnu'
      }
    </span>
  )
}


function DataMetric({
  icon,
  label,
  value,
  secondary,
}: {
  icon: ReactNode
  label: string
  value: string
  secondary?: string
}) {
  return (
    <div
      className="
        min-w-0
        px-3
        py-3
        text-center
        not-last:border-r
        not-last:border-black/[0.055]
        dark:not-last:border-white/[0.06]
      "
    >
      <div
        className="
          flex
          items-center
          justify-center
          gap-1
          text-slate-400
        "
      >
        {icon}

        <span
          className="
            text-[8px]
            font-semibold
            uppercase
            tracking-[0.07em]
          "
        >
          {label}
        </span>
      </div>

      <p
        className="
          mt-1.5
          truncate
          text-[10.5px]
          font-semibold
          text-slate-700
          dark:text-slate-300
        "
      >
        {value}
      </p>

      {secondary && (
        <p
          className="
            mt-0.5
            text-[8.5px]
            text-slate-400
          "
        >
          {secondary}
        </p>
      )}
    </div>
  )
}


function formatHumanDate(
  value: string,
): string {
  const date =
    new Date(value)

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value
  }

  const today =
    new Date()

  const todayStart =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    )

  const targetStart =
    new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
    )

  const differenceDays =
    Math.round(
      (
        targetStart.getTime()
        - todayStart.getTime()
      )
      / 86_400_000,
    )

  const time =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        hour: '2-digit',
        minute: '2-digit',
      },
    ).format(date)

  if (differenceDays === 0) {
    return (
      `Aujourd’hui à ${time}`
    )
  }

  if (differenceDays === -1) {
    return (
      `Hier à ${time}`
    )
  }

  if (differenceDays === 1) {
    return (
      `Demain à ${time}`
    )
  }

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(date)
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
      `${
        (
          bytes / 1024
        ).toFixed(0)
      } Ko`
    )
  }

  return (
    `${
      (
        bytes
        / 1024
        / 1024
      ).toFixed(1)
    } Mo`
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
