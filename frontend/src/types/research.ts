export type ResearchSampleStatus =
  | 'empty'
  | 'insufficient'
  | 'exploratory'
  | 'descriptive'

export type ResearchAvailability = 'available' | 'partial' | 'pending' | 'unavailable' | 'exploratory' | 'descriptive'

export interface ResearchSample {
  n: number
  target: number
  status: ResearchSampleStatus
  label: string
  progress_percent: number
  thresholds: {
    exploratory: number
    descriptive: number
  }
}

export interface ResearchVersion {
  active_version: string
  status: string
  updated_at: string
  created_at: string
}

export interface ResearchWarning {
  file?: string
  record?: string
  reason?: string
}

export interface ResearchGradeCounts {
  A: number
  B: number
  C: number
  D: number
}

export interface ResearchStatus {
  sample: ResearchSample
  version: ResearchVersion
  counts: {
    cases: number
    approved: number
    strict_reviewed: number
    extended_reference: number
    pending_review: number
    sources: number
    countries: number
    instruments: number
  }
  countries: string[]
  instruments: string[]
  grade_counts: ResearchGradeCounts
  warnings: ResearchWarning[]
}


export interface ResearchAnalysisScope {
  key: 'all' | 'strict_candidate' | 'strict_individual' | 'extended_cross_cultural' | 'pending_review'
  label: string
  case_count: number
  scored_case_count: number
  valid_score_count: number
  strict_candidate_count?: number
  owner_approved_count?: number
  strict_approved_case_count?: number
  pending_owner_review_count?: number
  rejected_count?: number
  needs_more_evidence_count?: number
  thresholds: {
    exploratory: number
    descriptive: number
  }
}

export interface ResearchCaseSummary {
  case_id: string
  performer: string
  performer_type: string
  country: string
  region: string
  subregion?: string | null
  instrument: string[]
  work: string
  music_type: string
  event_date_text: string
  channel: string[]
  target_audience: string[]
  era_theme: string[]
  review_status: 'A' | 'B' | 'C' | 'D'
  source_count: number
  source_ids?: string[]
  source_links?: Array<{
    source_id?: string
    title?: string
    publisher?: string
    url: string
  }>
  cover_url: string | null
  summary: string
  cultural_hooks: string[]
  mean_score: number | null
  score_scale: number
  valid_count: number
  missing_count: number
  low_coverage: boolean
  case_type?: string
  analysis_sample?: 'strict_individual' | 'extended_cross_cultural' | 'pending_review' | null
  performer_identity_status?: string
  performance_location?: string
  overseas_activity?: boolean
  strict_sample_eligible?: boolean
  owner_approval_status?: string
  owner_approval_by?: string | null
  owner_approval_at?: string | null
  owner_approval_note?: string | null
  owner_approval_source_ids?: string[]
  eligibility_reason?: string
  evidence_limitations?: string[]
}

export interface ResearchSource {
  source_id: string
  title: string
  publisher: string
  url: string
  citation: string | null
  source_type: string
  published_at: string | null
  accessed_at: string
  reliability: string
  is_primary: boolean
  supports: string
  notes: string | null
  feedback_evidence_type?: string
  feedback_grade?: string
  feedback_country_basis?: string
  feedback_language?: string
  feedback_valence?: string
  mechanism_codes?: string[]
  coding_eligible?: boolean
}

export type AcceptanceMechanismStatus = 'strong' | 'partial' | 'not_evidenced'

export interface TeacherRevisionMechanism {
  code: string
  label: string
  status: AcceptanceMechanismStatus
  status_label: string
}

export interface TeacherRevisionFeedback {
  feedback_id: string
  evidence_type: string
  evidence_grade: string
  country_basis: string
  language: string | null
  valence: string | null
  excerpt: string | null
  summary: string
  limitations: string | null
  mechanism_codes: string[]
  coding_eligible: boolean
  source_url: string
  publisher: string
}

export interface TeacherRevisionCase {
  case_id: string
  performer: string
  country: string
  region: string
  instrument: string[]
  work: string
  summary: string
  outcome_status: string
  outcome_label: string
  mechanism_confidence: string
  mechanisms: TeacherRevisionMechanism[]
  feedback: TeacherRevisionFeedback[]
  evidence_limitations: string[]
  admission_audit: Array<{ code: string; passed: boolean; evidence: string }>
  source_count: number
  owner_approval_status: string
}

export interface TeacherRevisionMechanismAggregate {
  code: string
  label: string
  strong: number
  partial: number
  not_evidenced: number
  total: number
}

export interface TeacherRevisionMusic {
  music_id: string
  title: string
  category: string
  subcategory: string
  research_category: string
  instrument_or_form: string
  selection_tier: 'A' | 'B'
  primary_mechanisms: string[]
  era_theme: string
  international_format: string
  selection_reason: string
  main_risk: string
  first_validation: string
  scores: Record<string, number | null>
  total_score: number | null
  score_status: 'scored' | 'awaiting_six_country_pilot'
  score_status_label: string
}

export interface TeacherRevisionCountry extends ResearchRegionalRow {
  country: string
  priority_music_ids: string[]
  secondary_music_ids: string[]
  context_required_music_ids: string[]
  primary_entry_mechanisms: string[]
  theme_frame: string
  adaptation_design: string
  language_and_mediation: string
  religion_and_cultural_safeguard: string
  pilot_design: string
  success_metrics: string
  evidence_status: string
  fits: Record<string, 'A' | 'B' | 'C' | '待核验'>
}

export interface TeacherRevisionOutcome {
  sample: ResearchSample
  status: 'approved'
  status_label: string
  counts: {
    strict_cases: number
    feedback: number
    coding_eligible_feedback: number
    mechanisms: number
    music_candidates: number
    countries: number
    matrix_cells: number
  }
  cases: TeacherRevisionCase[]
  mechanisms: TeacherRevisionMechanismAggregate[]
  admission_rules: Array<{ code: string; label: string; requirement: string }>
  music: {
    status: string
    status_label: string
    note: string
    items: TeacherRevisionMusic[]
  }
  countries: TeacherRevisionCountry[]
  matrix: Array<{
    music_id: string
    title: string
    selection_tier: string
    countries: Record<string, 'A' | 'B' | 'C' | '待核验'>
  }>
  pilot: {
    status: 'not_started' | 'in_progress' | 'complete'
    status_label: string
    design_principles: string[]
    response_fields: Array<{ key: string; label: string; required: boolean; rule: string }>
    planned_cells: number
    completed_cells: number
  }
  scope_note: string
  warnings: ResearchWarning[]
}

export interface PilotValidationResult {
  sample: ResearchSample
  status: 'valid' | 'partial' | 'invalid'
  summary: {
    total_rows: number
    eligible_rows: number
    invalid_rows: number
    error_count: number
    duplicate_response_ids: number
    planned_cells: number
    observed_cells: number
    balanced_cells: number
  }
  errors: Array<{
    row_number: number
    response_id: string | null
    field: string
    field_label: string
    code: string
    message: string
  }>
  coverage: Array<{
    country: string
    music_id: string
    original_n: number
    adapted_n: number
    has_both_variants: boolean
  }>
  descriptive_metrics: Array<{
    key: string
    label: string
    n: number
    mean_1_5: number | null
  }>
  formal_scoring_allowed: false
  scope_note: string
  warnings: ResearchWarning[]
}

export interface ResearchCaseRecord
  extends Omit<
    ResearchCaseSummary,
    'mean_score' | 'score_scale' | 'valid_count' | 'missing_count' | 'low_coverage'
  > {
  event_start_date: string | null
  event_end_date: string | null
  event_name: string
  venue: string
  learning_motivation: string
  adaptation: string
  religion_culture: string
  feedback: string
  success_evidence: string
  research_notes: string
  origin_city: string | null
  display_allowed: boolean
  source_ids: string[]
  sources: ResearchSource[]
  updated_at: string
}

export interface ResearchCodingIndicator {
  indicator_id: string
  label: string
  order: number
  score: number | null
  evidence: string | null
  source_ids: string[]
  missing_reason: string | null
  approval_status?: string | null
  score_status?: string | null
  approver?: string | null
  approval_date?: string | null
}

export interface ResearchCaseCoding {
  mean_score: number | null
  score_scale: number
  valid_count: number
  missing_count: number
  low_coverage: boolean
  indicators: ResearchCodingIndicator[]
}

export interface ResearchSimilarCase extends ResearchCaseSummary {
  match_score: number
  match_reasons: string[]
}

export interface ResearchCaseDetail {
  sample: ResearchSample
  case: ResearchCaseRecord
  coding: ResearchCaseCoding
  audience_feedback: TeacherRevisionFeedback[]
  acceptance_mechanisms: TeacherRevisionMechanism[]
  acceptance_mechanism_confidence: string | null
  outcome_status: string | null
  outcome_label: string
  similar_cases: ResearchSimilarCase[]
  warnings: ResearchWarning[]
}

export interface ResearchPagination {
  page: number
  page_size: number
  pages: number
  has_next: boolean
  has_previous: boolean
}

export interface ResearchCaseFilters {
  q: string
  country: string
  region: string
  instrument: string
  channel: string
  theme: string
  grade: string
  analysis_sample?: string
}

export interface ResearchCaseList {
  sample: ResearchSample
  analysis_scope: ResearchAnalysisScope
  items: ResearchCaseSummary[]
  total: number
  result_count: number
  pagination: ResearchPagination
  filters: ResearchCaseFilters
}

export interface ResearchDistributionItem {
  key: string
  count: number
}

export interface ResearchIndicatorCoverage {
  indicator_id: string
  label: string
  valid_count: number
  missing_count: number
  coverage_rate?: number
}

export interface ResearchStatistics {
  sample: ResearchSample
  analysis_scope: ResearchAnalysisScope
  distributions: {
    country: ResearchDistributionItem[]
    region: ResearchDistributionItem[]
    instrument: ResearchDistributionItem[]
    channel: ResearchDistributionItem[]
    theme: ResearchDistributionItem[]
    evidence_grade: ResearchDistributionItem[]
  }
  indicator_coverage: ResearchIndicatorCoverage[]
  country_factor_correspondence?: Array<{
    country: string
    case_count: number
    analysis_status: ResearchSampleStatus
    top_factors: Array<{
      indicator_id: string
      label: string
      mean_score: number
      n: number
      missing_count: number
    }>
    note: string
  }>
  rankings_allowed: boolean
  success_factors_available: boolean
  warnings: ResearchWarning[]
}

export interface ResearchSuccessFactor {
  indicator_id: string
  label: string
  order: number
  n: number
  missing_count: number
  coverage_rate?: number
  mean_score: number | null
  score_scale: number
  status: 'empty' | 'insufficient' | 'exploratory' | 'descriptive'
  status_label: string
  ranking_allowed: boolean
  gate_note: string
  rank: number | null
}

export interface ResearchSuccessFactors {
  sample: ResearchSample
  analysis_scope: ResearchAnalysisScope
  availability: ResearchAvailability
  rankings: ResearchSuccessFactor[] | null
  factors: ResearchSuccessFactor[]
  reason: string | null
  thresholds: {
    exploratory: number
    descriptive: number
    indicator_exploratory_min?: number
    indicator_rank_min?: number
  }
  gate_counts?: {
    empty: number
    insufficient: number
    exploratory: number
    descriptive: number
  }
  warnings?: ResearchWarning[]
}

export interface ResearchMusicItem {
  music_id: string
  title: string
  category: string
  subcategory: string
  instrument: string
  scores: Record<string, number | null>
  total_score: number | null
  tier: string
  rank?: number
}

export interface ResearchMusicPotential {
  sample: ResearchSample
  availability: ResearchAvailability
  status: 'pending' | 'partial' | 'complete'
  status_label: string
  note: string
  music_sample: {
    n: number
    target: number
    status: ResearchSampleStatus
  }
  weights: Record<string, number>
  tiers: Array<{ min: number; max: number; label: string }>
  items: ResearchMusicItem[]
  rankings: ResearchMusicItem[] | null
  warnings?: ResearchWarning[]
}

export interface ResearchRegionalMatrix {
  sample: ResearchSample
  availability: ResearchAvailability
  independent_of_case_sample?: boolean
  scope_note?: string
  status: 'pending' | 'partial' | 'complete'
  status_label: string
  note: string
  regions: string[]
  audiences: string[]
  themes: string[]
  rows: unknown[]
  matrix: unknown[] | null
  warnings?: ResearchWarning[]
}


export interface ResearchMusicPotentialItem {
  status: 'pending' | 'incomplete' | 'complete'
  music_id: string
  title: string
  scores: Record<string, number | null>
  valid_count: number
  missing_indicators: string[]
  total_score: number | null
  tier: string
  rank: number | null
  selection_tier?: 'A' | 'B' | string | null
  primary_mechanisms?: string[]
  era_theme?: string | null
  international_format?: string | null
  selection_reason?: string | null
  main_risk?: string | null
}

export interface ResearchMusicAssociation {
  status: 'linked' | 'category_reference' | 'unmapped'
  matched_by: string | null
  label: string
  reasons: string[]
}

export interface ResearchMusicContext {
  sample: ResearchSample
  music: {
    song_id: string | null
    title: string
    category: string
    subcategory: string
  }
  association: ResearchMusicAssociation
  music_status: 'pending' | 'partial' | 'complete'
  music_status_label: string
  music_note: string
  weights: Record<string, number>
  tiers: Array<{ min: number; max: number; label: string }>
  potential: ResearchMusicPotentialItem | null
  related_cases: Array<ResearchCaseSummary & { relation: string }>
  matched_cases: Array<ResearchCaseSummary & {
    relation: string
    match_score: number
    match_reasons: string[]
  }>
  factor_reference: {
    scope: 'direct' | 'matched' | 'library' | 'unavailable'
    scope_label: string
    case_ids: string[]
    factor_shares: Array<{
      indicator_id: string
      label: string
      mean_score: number
      n: number
      share: number
    }>
  }
  regional_rows: ResearchRegionalRow[]
  category_reference: {
    scope_label: string
    items: Array<{
      music_id: string
      title: string
      selection_tier: string
      primary_mechanisms: string[]
      era_theme: string | null
      international_format: string | null
      selection_reason: string | null
      main_risk: string | null
    }>
    primary_mechanisms: string[]
  } | null
  global_reference: {
    scope_label: string
    cases: ResearchCaseSummary[]
    factor_shares: Array<{
      indicator_id: string
      label: string
      mean_score: number
      n: number
      share: number
    }>
    regional_rows: ResearchRegionalRow[]
  }
  warnings: ResearchWarning[]
}


export interface ResearchRegionalRow {
  strategy_id?: string
  region?: string
  subregion?: string | null
  country?: string
  audience?: string
  language?: string
  cultural_background?: string
  religion_notes?: string
  match_reason?: string
  music_ids?: string[]
  themes?: string[]
  platforms?: string[]
  formats?: string[]
  case_ids?: string[]
  adaptation?: string
  risks?: Array<{ risk?: string; mitigation?: string }>
  source_ids?: string[]
  origin_city?: string | null
  city_anchor?: string | null
  city_scene?: string | null
  city_narrative?: string | null
  city_sources?: string[]
  review_status?: string
  display_allowed?: boolean
  [key: string]: unknown
}


export interface ResearchPromoPlanInput {
  title: string
  target_country: string
  target_city: string
  target_audience: string
  age_range: string
  purpose: string
  platform: string
  content_format: string
  adaptation_allowed: 'yes' | 'no' | 'undecided'
  budget_range: string
  duration: string
  language: string
  origin_city?: '北京' | '上海' | '其他' | '未提供' | null
}

export interface ResearchPlanEvidence {
  text: string
  case_ids: string[]
  source_ids: string[]
  source_links: Array<{
    source_id?: string
    title?: string
    publisher?: string
    url: string
  }>
  kind: 'evidence'
}

export interface ResearchPlanSuggestion {
  text: string
  basis: string
  kind: 'suggestion'
}

export interface ResearchPlanHypothesis {
  text: string
  validation: string
  kind: 'hypothesis'
}

export interface ResearchPlanGap {
  text: string
  action: string
  kind: 'gap'
}

export interface ResearchPlanModule {
  id: string
  title: string
  evidence: ResearchPlanEvidence[]
  suggestions: ResearchPlanSuggestion[]
  hypotheses: ResearchPlanHypothesis[]
  gaps: ResearchPlanGap[]
}

export interface ResearchPromoPlan {
  meta: {
    plan_id: string
    generated_at: string
    generation_mode: string
    ai_generated: boolean
    data_version: string
    module_count: number
    inputs: ResearchPromoPlanInput & { origin_city: string | null }
  }
  sample: ResearchSample
  evidence_summary: {
    potential: {
      status: string
      total_score: number | null
      tier: string
      valid_count: number
    }
    case_count: number
    case_scope_label?: string | null
    country_case_count?: number
    country_factor_count?: number
    regional_count: number
    source_count: number
    association: ResearchMusicAssociation
    music_status: string
    music_status_label: string
  }
  counts: {
    evidence: number
    suggestions: number
    hypotheses: number
    gaps: number
  }
  modules: ResearchPlanModule[]
  warnings: ResearchWarning[]
  disclaimer: string
}


export interface ResearchMiningCase {
  case_id: string
  performer: string
  country: string
  region: string
  instrument: string[]
  case_type: string | null
  analysis_sample: string | null
  source_count: number
  valid_count: number
  missing_count: number
  mean_score: number | null
  scores: Record<string, number | null>
}

export interface ResearchMiningIndicator {
  indicator_id: string
  label: string
  n: number
  missing_count: number
  coverage_rate: number
  mean_score: number | null
  max_score: number
  status: 'empty' | 'insufficient' | 'exploratory' | 'descriptive'
  status_label: string
  ranking_allowed: boolean
  gate_note: string
}

export interface ResearchMiningCorrelation {
  x: string
  y: string
  n: number
  rho: number | null
  status: 'exploratory' | 'insufficient'
  note: string
}

export interface ResearchMining {
  sample: ResearchSample
  analysis_scope: ResearchAnalysisScope
  case_count: number
  score_count: number
  valid_score_count: number
  cases: ResearchMiningCase[]
  distributions: {
    country: ResearchDistributionItem[]
    instrument: ResearchDistributionItem[]
    case_type: ResearchDistributionItem[]
    analysis_sample: ResearchDistributionItem[]
    review_status: ResearchDistributionItem[]
  }
  indicators: ResearchMiningIndicator[]
  correlations: ResearchMiningCorrelation[]
  library: {
    status: 'connected' | 'unavailable'
    database: string
    table: string
    song_count: number | null
    mapping_count: number
    mapped_count: number
    note: string
  }
  analysis_db: {
    status: 'connected' | 'unavailable'
    tables: string[]
    case_count: number | null
    score_count: number | null
    null_score_count: number | null
    source_count: number | null
    note?: string
  }
  scope_note: string
  data_version: string
  warnings: ResearchWarning[]
}

export interface PilotConfig {
  config_version: string
  status: 'proposed' | 'approved'
  approved_by: string | null
  approved_at: string | null
  min_per_variant: number
  min_per_cell: number
  variant_balance_tolerance: number
  min_country_total: number
  min_country_cells: number
  min_completion_rate: number
  max_missing_ratio: number
  cross_country_min_countries: number
  cross_country_min_cells: number
  weights: Record<string, number>
  note: string
}

export interface PilotDimensionStat {
  n: number
  mean: number | null
  sd: number | null
  missing: number
}

export interface PilotUnit {
  country: string
  music_id: string
  title: string
  n_total: number
  n_original: number
  n_adapted: number
  variant_balance: number
  variants: Record<'original' | 'adapted', { n: number; dimensions: Record<string, PilotDimensionStat> }>
  survey_means: Record<string, number | null>
  variant_diff: Record<string, number | null>
  evidence_score: number | null
  evidence_record_id?: string | null
  formal_score: number | null
  status: string
  status_reason: string
  open_responses: string[]
  cultural_risk_flags: string[]
}

export interface PilotBatch {
  batch_id: string
  batch_label: string
  file_digest: string
  imported_at: string
  imported_by: string
  approval_status: 'pending_approval' | 'approved' | string
  approved_by: string | null
  approved_at: string | null
  rows_total: number
  rows_clean: number
  rows_rejected: number
  error_count: number
  validation_status: string
}

export interface PilotScoreSummary {
  score_id: string
  title: string
  status: 'pending_approval' | 'approved_candidate' | 'published' | 'revoked' | string
  published_version?: string | null
  config_version?: string | null
  created_at: string
  created_by: string
  approved_by: string | null
  approved_at: string | null
  input_batches: string[]
  summary: Record<string, number>
}

export interface PilotOverview {
  sample: { countries: number; music: number; cells: number }
  config: PilotConfig
  validation: PilotValidationResult
  eligible_rows: number
  units: PilotUnit[]
  country_summary: Array<{
    country: string
    cells: number
    cells_with_data: number
    eligible_cells: number
    valid_n: number
    country_ready: boolean
  }>
  cross_country: Array<{
    music_id: string
    title: string
    countries_with_score: number
    cross_country_score: number | null
    weighting: string
    ready_for_ranking: boolean
  }>
  status_counts: Record<string, number>
  formula: {
    scale: string
    weights: Record<string, number>
    weights_note: string
    score: string
    existing_evidence: string
  }
  formal_scoring_allowed: boolean
  ranking_allowed: boolean
  batches: PilotBatch[]
  scores: PilotScoreSummary[]
  evidence: PilotEvidence[]
  published: PilotPublished | null
  protocol?: {
    protocol_version: string
    status: string
    sha256: string
    approved_by: string | null
    approved_at: string | null
    localization: Array<{ country: string; language: string; translation_status: string }>
  } | null
  assignments?: {
    total: number
    active: number
    withdrawn: number
    by_country: Record<string, number>
    by_status: Record<string, number>
    by_variant: Record<string, number>
    cells: Array<{ country: string; music_id: string; original: number; adapted: number }>
    imbalanced_cells: number
  }
  localizations?: PilotLocalizationOverview
  rankings_allowed: boolean
  scope_note: string
}

export interface PilotLocalizationQuestion {
  id: string
  prompt: string
  anchor_1: string
  anchor_5: string
}

export interface PilotLocalizationContent {
  title: string | null
  intro: string | null
  background_100: string | null
  consent: string | null
  questionnaire: PilotLocalizationQuestion[]
  open_questions: string[]
  risk_notice: string | null
  recruitment: string | null
  operator_manual: string[]
}

export interface PilotLocalization {
  protocol_version: string
  protocol_sha256?: string | null
  country: string
  language: string
  source_language?: string
  localization_version: string | null
  status: 'not_created' | 'source_ready' | 'pending_native_review' | 'approved' | 'revoked'
  source_zh?: PilotLocalizationContent
  translations?: PilotLocalizationContent
  translator: string | null
  submitted_at?: string | null
  reviewer: string | null
  reviewed_at?: string | null
  sha256: string | null
}

export interface PilotLocalizationOverview {
  protocol_version: string | null
  items: PilotLocalization[]
  counts: Record<string, number>
  recruitment_ready: boolean
  note: string
}

export interface PilotDimension {
  key: string
  label: string
  source: 'survey' | 'evidence'
  order: number
}

export interface PilotEvidence {
  evidence_id: string
  music_id: string
  score_0_100: number
  source: string
  rule_version: string
  status: 'pending_approval' | 'approved' | 'revoked' | string
  entered_by: string
  entered_at: string
  approved_by: string | null
  approved_at: string | null
  revoke_reason?: string | null
}

export interface PilotPublished {
  version: string
  status: string
  score_id: string
  published_by: string
  published_at: string
  config_version: string
  units: PilotUnit[]
}
