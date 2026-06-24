export type CandidateRow = {
  candidate_id: string;
  rank: number;
  score: number;
  semantic_match_pct: number;
  skill_match_pct: number;
  experience_match_pct: number;
  key_strengths: string[];
  concerns: string[];
  title: string;
  years_experience: number;
  reasoning: string;
};

export type ResultsMetadata = {
  total_candidates: number;
  avg_score: number;
  max_score: number;
  min_score: number;
  generated_at: string;
};

export type ResultsResponse = {
  candidates: CandidateRow[];
  metadata: ResultsMetadata;
};

export type RankingStage = {
  stage: string;
  stageLabel: string;
  progressPct: number;
  candidatesProcessed: number;
  status: string;
  error?: string | null;
  errorDetails?: string | null;
};
