const apiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type RecommendationStructured = {
  what: string;
  where: string;
  why: string;
  how: string;
};

export function isStructuredRecommendation(
  r: string | RecommendationStructured | null | undefined
): r is RecommendationStructured {
  return (
    typeof r === "object" && r !== null && "what" in r && "how" in r
  );
}

export type CheckFinding = {
  id: string;
  name: string;
  status: "pass" | "warn" | "fail";
  evidence: {
    file: string;
    snippet: string;
    start_line?: number;
    end_line?: number;
  };
  recommendation: string | RecommendationStructured;
  points: number;
  severity?: number;
  confidence?: number;
  scope_factor?: number;
  category?: string;
};

export type SectionFinding = {
  name: string;
  checks: CheckFinding[];
  score: number;
};

export type ReportFindingsSuccess = {
  overall_score: number;
  sections: SectionFinding[];
  interview_pack?: string[];
  category_scores?: { [category: string]: number };
};

export type ReportFindingsFailed = { error: string };

export type ReportFindings =
  | ReportFindingsSuccess
  | ReportFindingsFailed;

export type Report = {
  id: string;
  repo_url: string;
  repo_owner: string | null;
  repo_name: string | null;
  commit_sha?: string | null;
  status: string | null;
  overall_score: number | null;
  findings_json: ReportFindings | null;
  created_at: string | null;
  updated_at: string | null;
};

export function isFindingsFailed(
  f: ReportFindings | null
): f is ReportFindingsFailed {
  return f != null && "error" in f && typeof (f as ReportFindingsFailed).error === "string";
}

export function isFindingsSuccess(
  f: ReportFindings | null
): f is ReportFindingsSuccess {
  return (
    f != null &&
    "sections" in f &&
    Array.isArray((f as ReportFindingsSuccess).sections)
  );
}

export async function analyzeRepo(
  repoUrl: string
): Promise<{ report_id: string }> {
  const res = await fetch(`${apiBase}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg =
      typeof data?.detail === "string" ? data.detail : res.statusText;
    throw new Error(msg);
  }
  return res.json();
}

export async function getReport(id: string): Promise<Report> {
  const res = await fetch(`${apiBase}/api/reports/${id}?v=2`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("Report not found");
    const data = await res.json().catch(() => ({}));
    const msg =
      typeof data?.detail === "string" ? data.detail : res.statusText;
    throw new Error(msg);
  }
  return res.json();
}
