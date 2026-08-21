import type {
  Race,
} from './types'


export const races: Race[] = [
  {
    id: 'race-upcoming-demo',
    name: 'Trail des Vosges',
    location: 'Vosges, France',
    date: '2026-09-12',
    type: 'trail',

    priority: 'primary',

    distanceKm: 42,
    elevationGainM: 1800,
    targetTimeMinutes: 300,

    status: 'planned',
  },

  {
    id: 'race-completed-demo',
    name: 'Trail du Jura',
    location: 'Jura, France',
    date: '2026-05-17',
    type: 'trail',

    priority: 'primary',

    distanceKm: 50,
    elevationGainM: 2600,

    actualDistanceKm: 50,
    actualElevationGainM: 2600,
    actualTimeMinutes: 510,

    status: 'completed',

    notes:
      'Bonne gestion de course malgré la durée.',
  },

  {
    id: 'race-abandoned-demo',
    name: 'Ultra du Jura',
    location: 'Jura, France',
    date: '2026-04-18',
    type: 'ultra',

    priority: 'training',

    distanceKm: 65,
    elevationGainM: 3000,

    actualDistanceKm: 42.8,
    actualElevationGainM: 2150,

    status: 'not_participated',

    notes:
      'Abandon au 43e kilomètre.',
  },
]