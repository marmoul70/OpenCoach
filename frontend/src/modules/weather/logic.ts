export interface WeatherDescription {
  label: string
  icon: string
}

export function getWeatherDescription(
  weatherCode: number,
): WeatherDescription {
  switch (weatherCode) {
    case 0:
      return {
        label: 'Ciel dégagé',
        icon: '☀️',
      }

    case 1:
      return {
        label: 'Principalement dégagé',
        icon: '🌤️',
      }

    case 2:
      return {
        label: 'Partiellement nuageux',
        icon: '⛅',
      }

    case 3:
      return {
        label: 'Couvert',
        icon: '☁️',
      }

    case 45:
    case 48:
      return {
        label: 'Brouillard',
        icon: '🌫️',
      }

    case 51:
    case 53:
    case 55:
      return {
        label: 'Bruine',
        icon: '🌦️',
      }

    case 56:
    case 57:
      return {
        label: 'Bruine verglaçante',
        icon: '🌧️',
      }

    case 61:
    case 63:
    case 65:
      return {
        label: 'Pluie',
        icon: '🌧️',
      }

    case 66:
    case 67:
      return {
        label: 'Pluie verglaçante',
        icon: '🌧️',
      }

    case 71:
    case 73:
    case 75:
      return {
        label: 'Neige',
        icon: '🌨️',
      }

    case 77:
      return {
        label: 'Grains de neige',
        icon: '🌨️',
      }

    case 80:
    case 81:
    case 82:
      return {
        label: 'Averses',
        icon: '🌦️',
      }

    case 85:
    case 86:
      return {
        label: 'Averses de neige',
        icon: '🌨️',
      }

    case 95:
      return {
        label: 'Orage',
        icon: '⛈️',
      }

    case 96:
    case 99:
      return {
        label: 'Orage avec grêle',
        icon: '⛈️',
      }

    default:
      return {
        label: 'Conditions inconnues',
        icon: '❓',
      }
  }
}
