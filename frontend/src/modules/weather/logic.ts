export interface WeatherDescription {
  label: string
}

export function getWeatherDescription(
  weatherCode: number,
): WeatherDescription {
  switch (weatherCode) {
    case 0:
      return {
        label: 'Ciel dégagé',
      }

    case 1:
      return {
        label: 'Principalement dégagé',
      }

    case 2:
      return {
        label: 'Partiellement nuageux',
      }

    case 3:
      return {
        label: 'Couvert',
      }

    case 45:
    case 48:
      return {
        label: 'Brouillard',
      }

    case 51:
    case 53:
    case 55:
      return {
        label: 'Bruine',
      }

    case 56:
    case 57:
      return {
        label: 'Bruine verglaçante',
      }

    case 61:
    case 63:
    case 65:
      return {
        label: 'Pluie',
      }

    case 66:
    case 67:
      return {
        label: 'Pluie verglaçante',
      }

    case 71:
    case 73:
    case 75:
      return {
        label: 'Neige',
      }

    case 77:
      return {
        label: 'Grains de neige',
      }

    case 80:
    case 81:
    case 82:
      return {
        label: 'Averses',
      }

    case 85:
    case 86:
      return {
        label: 'Averses de neige',
      }

    case 95:
      return {
        label: 'Orage',
      }

    case 96:
    case 99:
      return {
        label: 'Orage avec grêle',
      }

    default:
      return {
        label: 'Conditions inconnues',
      }
  }
}
