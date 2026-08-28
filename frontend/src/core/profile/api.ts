import type { AthleteProfile } from './types'

interface ApiProfile {
  identity: {
    first_name: string
    last_name: string
    birth_date: string
    gender?: 'male' | 'female' | 'other' | 'unspecified'
    avatar?: string | null
  }
  body: {
    height_cm?: number | null
    weight_kg?: number | null
  }
  physiology: {
    max_heart_rate?: number | null
    resting_heart_rate?: number | null
    vma?: number | null
    threshold_heart_rate_1?: number | null
    threshold_heart_rate_2?: number | null
  }
  training: {
    weekly_sessions?: number | null
    weekly_duration_minutes?: number | null
    weekly_distance_km?: number | null
    available_days: number[]
    fatigue_threshold?: number | null
    experience?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
    sport_disciplines: Array<
      'road_running'
      | 'trail_running'
    >
  }
  location: {
    name?: string | null
    latitude?: number | null
    longitude?: number | null
  }
  equipment: {
    shoes: ApiShoe[]
    bikes: ApiBike[]
    watches: ApiWatch[]
  }
  nutrition: {
    carbohydrates_per_hour?: number | null
    fluids_per_hour?: number | null
    sodium_per_hour?: number | null
  }
}

interface ApiEquipmentItem {
  id: string
  brand?: string | null
  model: string
  active: boolean
}

interface ApiShoe extends ApiEquipmentItem {
  distance_km: number
  max_distance_km?: number | null
}

interface ApiBike extends ApiEquipmentItem {
  distance_km: number
}

interface ApiWatch extends ApiEquipmentItem {}

function optionalNumber(
  value: number | null | undefined,
): number | undefined {
  return value ?? undefined
}

function fromApi(profile: ApiProfile): AthleteProfile {
  return {
    identity: {
      firstName: profile.identity.first_name,
      lastName: profile.identity.last_name,
      birthDate: profile.identity.birth_date,
      gender: profile.identity.gender ?? 'unspecified',
      avatar: profile.identity.avatar ?? undefined,
    },

    body: {
      heightCm: optionalNumber(profile.body.height_cm),
      weightKg: optionalNumber(profile.body.weight_kg),
    },

    physiology: {
      maxHeartRate: optionalNumber(
        profile.physiology.max_heart_rate,
      ),
      restingHeartRate: optionalNumber(
        profile.physiology.resting_heart_rate,
      ),
      vma: optionalNumber(profile.physiology.vma),
      thresholdHeartRate1: optionalNumber(
        profile.physiology.threshold_heart_rate_1,
      ),
      thresholdHeartRate2: optionalNumber(
        profile.physiology.threshold_heart_rate_2,
      ),
    },

    training: {
      weeklySessions: optionalNumber(
        profile.training.weekly_sessions,
      ),
      weeklyDurationMinutes: optionalNumber(
        profile.training.weekly_duration_minutes,
      ),
      weeklyDistanceKm: optionalNumber(
        profile.training.weekly_distance_km,
      ),
      availableDays: [...profile.training.available_days],
      fatigueThreshold: optionalNumber(
        profile.training.fatigue_threshold,
      ),
      experience: profile.training.experience,
      sportDisciplines: [
        ...(profile.training.sport_disciplines ?? []),
      ],
    },

    location: {
      name: profile.location.name ?? undefined,
      latitude: optionalNumber(profile.location.latitude),
      longitude: optionalNumber(profile.location.longitude),
    },

    equipment: {
      shoes: profile.equipment.shoes.map((shoe) => ({
        id: shoe.id,
        brand: shoe.brand ?? undefined,
        model: shoe.model,
        active: shoe.active,
        distanceKm: shoe.distance_km,
        maxDistanceKm: optionalNumber(shoe.max_distance_km),
      })),

      bikes: profile.equipment.bikes.map((bike) => ({
        id: bike.id,
        brand: bike.brand ?? undefined,
        model: bike.model,
        active: bike.active,
        distanceKm: bike.distance_km,
      })),

      watches: profile.equipment.watches.map((watch) => ({
        id: watch.id,
        brand: watch.brand ?? undefined,
        model: watch.model,
        active: watch.active,
      })),
    },

    nutrition: {
      carbohydratesPerHour: optionalNumber(
        profile.nutrition.carbohydrates_per_hour,
      ),
      fluidsPerHour: optionalNumber(
        profile.nutrition.fluids_per_hour,
      ),
      sodiumPerHour: optionalNumber(
        profile.nutrition.sodium_per_hour,
      ),
    },
  }
}

function toApi(profile: AthleteProfile): ApiProfile {
  return {
    identity: {
      first_name: profile.identity.firstName,
      last_name: profile.identity.lastName,
      birth_date: profile.identity.birthDate,
      gender: profile.identity.gender,
      avatar: profile.identity.avatar ?? null,
    },

    body: {
      height_cm: profile.body.heightCm ?? null,
      weight_kg: profile.body.weightKg ?? null,
    },

    physiology: {
      max_heart_rate: profile.physiology.maxHeartRate ?? null,
      resting_heart_rate:
        profile.physiology.restingHeartRate ?? null,
      vma: profile.physiology.vma ?? null,
      threshold_heart_rate_1:
        profile.physiology.thresholdHeartRate1 ?? null,
      threshold_heart_rate_2:
        profile.physiology.thresholdHeartRate2 ?? null,
    },

    training: {
      weekly_sessions:
        profile.training.weeklySessions ?? null,
      weekly_duration_minutes:
        profile.training.weeklyDurationMinutes ?? null,
      weekly_distance_km:
        profile.training.weeklyDistanceKm ?? null,
      available_days: [...profile.training.availableDays],
      fatigue_threshold:
        profile.training.fatigueThreshold ?? null,
      experience: profile.training.experience ?? 'beginner',
      sport_disciplines: [
        ...profile.training.sportDisciplines,
      ],
    },

    location: {
      name: profile.location.name ?? null,
      latitude: profile.location.latitude ?? null,
      longitude: profile.location.longitude ?? null,
    },

    equipment: {
      shoes: profile.equipment.shoes.map((shoe) => ({
        id: shoe.id,
        brand: shoe.brand ?? null,
        model: shoe.model,
        active: shoe.active,
        distance_km: shoe.distanceKm,
        max_distance_km: shoe.maxDistanceKm ?? null,
      })),

      bikes: profile.equipment.bikes.map((bike) => ({
        id: bike.id,
        brand: bike.brand ?? null,
        model: bike.model,
        active: bike.active,
        distance_km: bike.distanceKm,
      })),

      watches: profile.equipment.watches.map((watch) => ({
        id: watch.id,
        brand: watch.brand ?? null,
        model: watch.model,
        active: watch.active,
      })),
    },

    nutrition: {
      carbohydrates_per_hour:
        profile.nutrition.carbohydratesPerHour ?? null,
      fluids_per_hour:
        profile.nutrition.fluidsPerHour ?? null,
      sodium_per_hour:
        profile.nutrition.sodiumPerHour ?? null,
    },
  }
}

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(input, init)

  if (!response.ok) {
    const message = await response.text()

    throw new Error(
      message || `Erreur HTTP ${response.status}`,
    )
  }

  return response.json() as Promise<T>
}

export async function fetchAthleteProfile(): Promise<AthleteProfile> {
  const profile = await request<ApiProfile>('/api/profile')

  return fromApi(profile)
}

export async function saveAthleteProfile(
  profile: AthleteProfile,
): Promise<AthleteProfile> {
  const savedProfile = await request<ApiProfile>(
    '/api/profile',
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(toApi(profile)),
    },
  )

  return fromApi(savedProfile)
}
