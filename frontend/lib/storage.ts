import type { UploadApiResponse, UploadFormState } from "@/lib/types";

const FORM_KEY = "retrofit-upload-form-v2";
const RESULT_KEY = "retrofit-upload-result-v2";

export function createDefaultUploadForm(): UploadFormState {
  return {
    fullAddress: "",
    heatingFuel: "gas",
    coolingFuel: "electric",
    yearsInHome: "",
    approxSqft: "",

    electricityMode: "pdf",
    gasMode: "pdf",

    electricRateOverride: "",
    electricUsageOverride: "",
    gasRateOverride: "",
    gasUsageOverride: "",
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function saveUploadForm(form: UploadFormState): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(FORM_KEY, JSON.stringify(form));
}

export function loadUploadForm(): UploadFormState | null {
  if (typeof window === "undefined") return null;

  const raw = window.sessionStorage.getItem(FORM_KEY);
  if (!raw) return null;

  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isObject(parsed)) return null;

    const defaults = createDefaultUploadForm();

    const safeMode = (value: unknown) => (value === "manual" ? "manual" : "pdf");

    return {
      fullAddress: typeof parsed.fullAddress === "string" ? parsed.fullAddress : defaults.fullAddress,
      heatingFuel: parsed.heatingFuel === "electric" ? "electric" : "gas",
      coolingFuel: parsed.coolingFuel === "gas" ? "gas" : "electric",
      yearsInHome: typeof parsed.yearsInHome === "string" ? parsed.yearsInHome : defaults.yearsInHome,
      approxSqft: typeof parsed.approxSqft === "string" ? parsed.approxSqft : defaults.approxSqft,

      electricityMode: safeMode((parsed as any).electricityMode),
      gasMode: safeMode((parsed as any).gasMode),

      electricRateOverride: typeof parsed.electricRateOverride === "string" ? parsed.electricRateOverride : "",
      electricUsageOverride: typeof parsed.electricUsageOverride === "string" ? parsed.electricUsageOverride : "",
      gasRateOverride: typeof parsed.gasRateOverride === "string" ? parsed.gasRateOverride : "",
      gasUsageOverride: typeof parsed.gasUsageOverride === "string" ? parsed.gasUsageOverride : "",
    };
  } catch {
    return null;
  }
}

export function saveUploadResult(result: UploadApiResponse): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
}

export function loadUploadResult(): UploadApiResponse | null {
  if (typeof window === "undefined") return null;

  const raw = window.sessionStorage.getItem(RESULT_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as UploadApiResponse;
  } catch {
    return null;
  }
}