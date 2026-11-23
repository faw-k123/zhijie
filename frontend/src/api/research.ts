/**
 * 国际传播研究数据 API。
 *
 * 国际传播研究只读接口统一入口；页面不得绕过这里直接拼接接口。
 */
import http, { type ApiEnvelope } from './http'
import type {
  ResearchCaseDetail,
  ResearchCaseList,
  ResearchMusicContext,
  ResearchMining,
  ResearchMusicPotential,
  ResearchPromoPlan,
  ResearchPromoPlanInput,
  ResearchRegionalMatrix,
  ResearchStatistics,
  ResearchStatus,
  ResearchSuccessFactors,
  TeacherRevisionOutcome,
  PilotValidationResult,
  PilotConfig,
  PilotOverview,
  PilotBatch,
  PilotScoreSummary,
  PilotEvidence,
  PilotLocalizationOverview,
  PilotLocalization,
} from '@/types/research'

function pilotAuth(token: string) {
  return { headers: { Authorization: `Bearer ${token}` } }
}

export interface ResearchCaseQuery {
  q?: string
  country?: string
  region?: string
  instrument?: string
  channel?: string
  theme?: string
  grade?: string
  analysis_sample?: 'all' | 'strict_candidate' | 'strict_individual' | 'extended_cross_cultural' | 'pending_review'
  page?: number
  page_size?: number
}

export async function fetchResearchStatus() {
  const { data } = await http.get<ApiEnvelope<ResearchStatus>>('/research/status/')
  return data
}

export async function fetchResearchCases(params: ResearchCaseQuery = {}) {
  const { data } = await http.get<ApiEnvelope<ResearchCaseList>>('/research/cases/', { params })
  return data
}

export async function fetchResearchCase(caseId: string) {
  const { data } = await http.get<ApiEnvelope<ResearchCaseDetail>>(
    `/research/cases/${encodeURIComponent(caseId)}/`,
  )
  return data
}

export async function fetchResearchStatistics(
  params: { analysis_sample?: 'all' | 'strict_candidate' | 'strict_individual' | 'extended_cross_cultural' | 'pending_review' } = {},
) {
  const { data } = await http.get<ApiEnvelope<ResearchStatistics>>('/research/statistics/', { params })
  return data
}

export async function fetchResearchSuccessFactors(
  params: {
    analysis_sample?: 'all' | 'strict_candidate' | 'strict_individual' | 'extended_cross_cultural' | 'pending_review'
    country?: string
  } = {},
) {
  const { data } = await http.get<ApiEnvelope<ResearchSuccessFactors>>(
    '/research/success-factors/',
    { params },
  )
  return data
}

export async function fetchResearchMusicPotential() {
  const { data } = await http.get<ApiEnvelope<ResearchMusicPotential>>(
    '/research/music-potential/',
  )
  return data
}

export async function fetchResearchRegionalMatrix() {
  const { data } = await http.get<ApiEnvelope<ResearchRegionalMatrix>>(
    '/research/regional-matrix/',
  )
  return data
}

export async function fetchTeacherRevisionOutcomes() {
  const { data } = await http.get<ApiEnvelope<TeacherRevisionOutcome>>(
    '/research/teacher-revision/',
  )
  return data
}

export async function validatePilotResponses(rows: Array<Record<string, string>>) {
  const { data } = await http.post<ApiEnvelope<PilotValidationResult>>(
    '/research/pilot/validate/',
    { rows },
  )
  return data
}


export async function fetchPilotOverview() {
  const { data } = await http.get<ApiEnvelope<PilotOverview>>('/research/pilot/overview/')
  return data.data
}

export async function fetchPilotConfig() {
  const { data } = await http.get<ApiEnvelope<PilotConfig>>('/research/pilot/config/')
  return data.data
}

export async function approvePilotConfig(configVersion: string | undefined, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotConfig>>(
    '/research/pilot/config/approve/',
    configVersion ? { config_version: configVersion } : {},
    pilotAuth(token),
  )
  return data.data
}

export async function submitPilotConfig(payload: Record<string, number>, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotConfig>>('/research/pilot/config/submit/', payload, pilotAuth(token))
  return data.data
}

export async function importPilotRows(rows: Array<Record<string, unknown>>, batchLabel: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotBatch>>('/research/pilot/import/', {
    rows,
    batch_label: batchLabel,
  }, pilotAuth(token))
  return data.data
}

export async function approvePilotBatch(batchId: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotBatch>>(
    `/research/pilot/batches/${encodeURIComponent(batchId)}/approve/`,
    {},
    pilotAuth(token),
  )
  return data.data
}

export async function aggregatePilot() {
  const { data } = await http.post<ApiEnvelope<PilotOverview>>('/research/pilot/aggregate/', {})
  return data.data
}

export async function createPilotScoreDraft(title: string, token: string) {
  const { data } = await http.post<ApiEnvelope<Record<string, unknown>>>('/research/pilot/scores/', {
    title,
  }, pilotAuth(token))
  return data.data
}

export async function fetchPilotScores() {
  const { data } = await http.get<ApiEnvelope<{ items: PilotScoreSummary[] }>>('/research/pilot/scores/')
  return data.data
}

export async function approvePilotScore(scoreId: string, token: string) {
  const { data } = await http.post<ApiEnvelope<Record<string, unknown>>>(
    `/research/pilot/scores/${encodeURIComponent(scoreId)}/approve/`,
    {},
    pilotAuth(token),
  )
  return data.data
}

export async function revokePilotScore(scoreId: string, reason: string, token: string) {
  const { data } = await http.post<ApiEnvelope<Record<string, unknown>>>(
    `/research/pilot/scores/${encodeURIComponent(scoreId)}/revoke/`,
    { reason },
    pilotAuth(token),
  )
  return data.data
}

export async function publishPilotScore(scoreId: string, token: string) {
  const { data } = await http.post<ApiEnvelope<Record<string, unknown>>>(
    `/research/pilot/scores/${encodeURIComponent(scoreId)}/publish/`,
    {},
    pilotAuth(token),
  )
  return data.data
}

export async function revokePublishedPilot(version: string, reason: string, token: string) {
  const { data } = await http.post<ApiEnvelope<Record<string, unknown>>>(
    `/research/pilot/published/${encodeURIComponent(version)}/revoke/`,
    { reason },
    pilotAuth(token),
  )
  return data.data
}

export async function submitPilotEvidence(payload: {
  music_id: string
  score_0_100: number
  source: string
  rule_version: string
}, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotEvidence>>('/research/pilot/evidence/', payload, pilotAuth(token))
  return data.data
}

export async function approvePilotEvidence(evidenceId: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotEvidence>>(
    `/research/pilot/evidence/${encodeURIComponent(evidenceId)}/approve/`,
    {},
    pilotAuth(token),
  )
  return data.data
}

export async function revokePilotEvidence(evidenceId: string, reason: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotEvidence>>(
    `/research/pilot/evidence/${encodeURIComponent(evidenceId)}/revoke/`,
    { reason },
    pilotAuth(token),
  )
  return data.data
}

export async function fetchPilotLocalizations(protocolVersion?: string) {
  const { data } = await http.get<ApiEnvelope<PilotLocalizationOverview>>(
    '/research/pilot/localizations/',
    { params: protocolVersion ? { protocol_version: protocolVersion } : {} },
  )
  return data.data
}

export async function generatePilotLocalizationSources(protocolVersion: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotLocalizationOverview>>(
    '/research/pilot/localizations/generate/',
    { protocol_version: protocolVersion },
    pilotAuth(token),
  )
  return data.data
}

export async function submitPilotLocalization(
  protocolVersion: string,
  country: string,
  translations: Record<string, unknown>,
  token: string,
) {
  const { data } = await http.post<ApiEnvelope<PilotLocalization>>(
    `/research/pilot/localizations/${encodeURIComponent(protocolVersion)}/${encodeURIComponent(country)}/submit/`,
    { translations },
    pilotAuth(token),
  )
  return data.data
}

export async function approvePilotLocalization(protocolVersion: string, country: string, token: string) {
  const { data } = await http.post<ApiEnvelope<PilotLocalization>>(
    `/research/pilot/localizations/${encodeURIComponent(protocolVersion)}/${encodeURIComponent(country)}/approve/`,
    {},
    pilotAuth(token),
  )
  return data.data
}

export async function fetchResearchMusicContext(params: {
  title: string
  category?: string
  subcategory?: string
  song_id?: string
}) {
  const { data } = await http.get<ApiEnvelope<ResearchMusicContext>>(
    '/research/music-context/',
    { params },
  )
  return data
}


export async function generateResearchPromoPlan(payload: ResearchPromoPlanInput) {
  const { data } = await http.post<ApiEnvelope<ResearchPromoPlan>>(
    '/research/promo-plan/',
    payload,
    { timeout: 120000 },
  )
  return data
}


export async function fetchResearchMining(params: {
  analysis_sample?: 'all' | 'strict_candidate' | 'strict_individual' | 'extended_cross_cultural' | 'pending_review'
} = {}) {
  const { data } = await http.get<ApiEnvelope<ResearchMining>>('/research/mining/', { params })
  return data
}

