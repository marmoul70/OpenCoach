import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Snowflake,
  Sun,
} from 'lucide-react'


interface WeatherIconProps {
  weatherCode: number
  size?: number
  className?: string
}


export function WeatherIcon({
  weatherCode,
  size = 32,
  className = '',
}: WeatherIconProps) {
  const commonClassName = [
    'shrink-0',
    className,
  ].join(' ')

  if (weatherCode === 0) {
    return (
      <Sun
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-amber-400',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 1
    || weatherCode === 2
  ) {
    return (
      <CloudSun
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-sky-400',
        ].join(' ')}
      />
    )
  }

  if (weatherCode === 3) {
    return (
      <Cloud
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-slate-400',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 45
    || weatherCode === 48
  ) {
    return (
      <CloudFog
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-slate-400',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 51
    || weatherCode === 53
    || weatherCode === 55
  ) {
    return (
      <CloudDrizzle
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-sky-500',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 56
    || weatherCode === 57
    || weatherCode === 61
    || weatherCode === 63
    || weatherCode === 65
    || weatherCode === 66
    || weatherCode === 67
    || weatherCode === 80
    || weatherCode === 81
    || weatherCode === 82
  ) {
    return (
      <CloudRain
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-sky-500',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 71
    || weatherCode === 73
    || weatherCode === 75
    || weatherCode === 85
    || weatherCode === 86
  ) {
    return (
      <CloudSnow
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-sky-300',
        ].join(' ')}
      />
    )
  }

  if (weatherCode === 77) {
    return (
      <Snowflake
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-sky-300',
        ].join(' ')}
      />
    )
  }

  if (
    weatherCode === 95
    || weatherCode === 96
    || weatherCode === 99
  ) {
    return (
      <CloudLightning
        size={size}
        strokeWidth={1.7}
        className={[
          commonClassName,
          'text-amber-500',
        ].join(' ')}
      />
    )
  }

  return (
    <Cloud
      size={size}
      strokeWidth={1.7}
      className={[
        commonClassName,
        'text-slate-400',
      ].join(' ')}
    />
  )
}
