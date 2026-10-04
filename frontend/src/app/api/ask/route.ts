import { NextResponse } from "next/server";

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "invalid_request",
          message: "Request body must be JSON.",
        },
      },
      { status: 400 },
    );
  }
  try {
    const base = process.env.BACKEND_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${base.replace(/\/$/, "")}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: AbortSignal.timeout(120_000),
    });
    const text = await response.text();
    try {
      return NextResponse.json(JSON.parse(text), { status: response.status });
    } catch {
      return NextResponse.json(
        {
          error: {
            code: "backend_error",
            message: "Backend returned an invalid JSON response.",
          },
        },
        { status: response.ok ? 502 : response.status },
      );
    }
  } catch (error) {
    const timeout =
      error instanceof Error &&
      ["TimeoutError", "AbortError"].includes(error.name);
    return NextResponse.json(
      {
        error: {
          code: timeout ? "timeout" : "backend_unavailable",
          message: timeout
            ? "The backend request timed out."
            : "The backend is unavailable.",
        },
      },
      { status: timeout ? 504 : 503 },
    );
  }
}
