export type Severity = "critical" | "major" | "minor" | "nit";
export type Category =
  "bug" | "security" | "performance" | "style" | "missing_tests";

export interface Finding {
  severity: Severity;
  category: Category;
  file: string;
  line_start: number;
  line_end: number;
  title: string;
  explanation: string;
  suggested_fix: string;
}

export interface Review {
  id: string;
  title: string;
  summary: string;
  findings: Finding[];
  changed_files: string[];
  excluded_files: string[];
  processed_changed_lines: number;
  diff?: string;
}

export interface User {
  id: string;
  login: string;
  display_name: string | null;
  avatar_url: string | null;
}

export interface AuthResponse {
  authenticated: boolean;
  user: User | null;
}
