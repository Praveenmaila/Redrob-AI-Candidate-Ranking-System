export type CandidateRow = {
  candidate_id: string;
  rank: number;
  score: number;
  reasoning: string;
};

export type RankingResponse = {
  status: string;
  progressMessage?: string;
};
