export interface AthleteIdentity {
  firstName: string
  lastName: string
  birthDate: string
  gender?: 'male' | 'female' | 'other' | 'unspecified'
  avatar?: string
}

export interface AthleteBody {
  heightCm?: number
  weightKg?: number
}

export interface HeartRateZone {
  maxBpm: number
}

export interface HeartRateZones {
  z1?: HeartRateZone
  z2?: HeartRateZone
  z3?: HeartRateZone
  z4?: HeartRateZone
  z5?: HeartRateZone
}


export interface AthletePhysiology {
  maxHeartRate?: number
  restingHeartRate?: number
  vma?: number
  thresholdHeartRate1?: number
  thresholdHeartRate2?: number

  heartRateZones: HeartRateZones
}

export type SportDiscipline =
  | 'road_running'
  | 'trail_running'


export interface AthleteTraining {
  weeklySessions?: number
  weeklyDurationMinutes?: number
  weeklyDistanceKm?: number
  availableDays: number[]
  fatigueThreshold?: number
  experience?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  sportDisciplines: SportDiscipline[]
}

export interface AthleteLocation {
  name?: string
  latitude?: number
  longitude?: number
}

export interface EquipmentItem {
  id: string
  brand?: string
  model: string
  active: boolean
}

export interface Shoe extends EquipmentItem {
  distanceKm: number
  maxDistanceKm?: number
}

export interface Bike extends EquipmentItem {
  distanceKm: number
}

export interface Watch extends EquipmentItem {}

export interface AthleteEquipment {
  shoes: Shoe[]
  bikes: Bike[]
  watches: Watch[]
}

export interface AthleteNutrition {
  carbohydratesPerHour?: number
  fluidsPerHour?: number
  sodiumPerHour?: number
}

export interface AthleteProfile {
  identity: AthleteIdentity
  body: AthleteBody
  physiology: AthletePhysiology
  training: AthleteTraining
  location: AthleteLocation
  equipment: AthleteEquipment
  nutrition: AthleteNutrition
}
