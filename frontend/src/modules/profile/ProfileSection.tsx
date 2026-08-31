import {
  useState,
  type ReactNode,
} from 'react'


interface ProfileSectionProps {
  title: string
  description?: string
  children: ReactNode
  defaultOpen?: boolean
  trailing?: ReactNode
  icon?: ReactNode
  iconClassName?: string
}


export function ProfileSection({
  title,
  description,
  children,
  defaultOpen = false,
  trailing,
  icon,
  iconClassName,
}: ProfileSectionProps) {
  const [
    open,
    setOpen,
  ] = useState(
    defaultOpen,
  )


  return (
    <section
      className={[
        (
          'collapse-arrow collapse '
          + 'border border-base-300 '
          + 'bg-base-100 shadow-sm'
        ),
        open
          ? 'collapse-open'
          : '',
      ].join(' ')}
    >
      <button
        type="button"
        onClick={() =>
          setOpen(
            (current) =>
              !current,
          )
        }
        className="
          collapse-title
          flex
          min-h-0
          items-center
          justify-between
          gap-4
          px-6
          py-5
          pr-12
          text-left
        "
        aria-expanded={open}
      >
        <div
          className="
            flex
            min-w-0
            flex-1
            items-center
            gap-3
          "
        >
          {icon && (
            <div
              className={[
                (
                  'flex h-11 w-11 shrink-0 '
                  + 'items-center justify-center '
                  + 'rounded-xl'
                ),
                (
                  iconClassName
                  ?? 'bg-primary/10 text-primary'
                ),
              ].join(' ')}
            >
              {icon}
            </div>
          )}

          <div
            className="
              min-w-0
              flex-1
            "
          >
            <h2
              className="
                text-lg
                font-semibold
                text-base-content
              "
            >
              {title}
            </h2>

            {description && (
              <p
                className="
                  mt-1
                  text-sm
                  text-base-content/60
                "
              >
                {description}
              </p>
            )}
          </div>
        </div>

        {trailing && (
          <div
            className="
              mr-2
              shrink-0
            "
          >
            {trailing}
          </div>
        )}
      </button>

      {open && (
        <div
          className="
            collapse-content
            border-t
            border-base-300
            px-6
            pb-6
            pt-5
          "
        >
          {children}
        </div>
      )}
    </section>
  )
}
