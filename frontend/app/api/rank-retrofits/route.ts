import { NextResponse } from "next/server";
import { buildDemoRanking } from "@/lib/demo-ranking";
import type { HomeAnalysisRequest, RankingResponse } from "@/lib/types";

export const runtime = "nodejs";

function getPythonRankUrl(): string | null {
  const base = process.env.PYTHON_BACKEND_URL?.trim();

  if (!base) return null;
  if (base.endsWith("/rank")) return base;

  return `${base.replace(/\/+$/, "")}/rank`;
}

function isValidPayload(value: unknown): value is HomeAnalysisRequest {
  if (!value || typeof value !== "object") return false;

  const candidate = value as Partial<HomeAnalysisRequest>;

  return (
    typeof candidate.address === "string" &&
    typeof candidate.sqft === "number" &&
    typeof candidate.monthly_electric_bill === "number" &&
    "location" in candidate
  );
}

export async function POST(request: Request) {
  let payload: unknown;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON request body." },
      { status: 400 },
    );
  }

  if (!isValidPayload(payload)) {
    return NextResponse.json(
      { error: "Request body does not match the expected shape." },
      { status: 400 },
    );
  }

  const pythonUrl = getPythonRankUrl();

  if (pythonUrl) {
    try {
      const response = await fetch(pythonUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });

      if (response.ok) {
        const data = (await response.json()) as Partial<RankingResponse>;

        return NextResponse.json({
          ranked_options: Array.isArray(data.ranked_options)
            ? data.ranked_options
            : [],
          assumptions: Array.isArray(data.assumptions) ? data.assumptions : [],
          source: "python",
        } satisfies RankingResponse);
      }

      const errorText = await response.text();
      console.error("Python backend returned a non-200 response:", errorText);
    } catch (error) {
      console.error("Python backend request failed:", error);
    }
  }

  return NextResponse.json(buildDemoRanking(payload));
}